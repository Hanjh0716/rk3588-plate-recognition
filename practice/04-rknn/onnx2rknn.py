#!/usr/bin/env python3
# ============================================================
# ONNX -> RKNN 转换 + 仿真推理验证（纯 PC，不需要板子）
# ============================================================
# 用法:
#   conda activate rknn
#   python3 onnx2rknn.py 模型.onnx                     # FP16（不量化，先跑通流程）
#   python3 onnx2rknn.py 模型.onnx --int8 校准图片目录  # INT8 量化（要校准集）
#
# 它做了什么:
#   ① config     → 告诉工具链"目标平台是 rk3588"、预处理参数
#   ② load_onnx  → 读入 ONNX
#   ③ build      → 真正编译（可选 INT8 量化）
#   ④ export     → 导出 .rknn 文件
#   ⑤ 仿真推理    → 在 PC 上模拟 NPU 跑一次，验证 .rknn 是活的（不需要板子！）
#
# 讲解见: docs/09-RKNN-Toolkit2环境安装.md
# ============================================================

import argparse
import os
import sys

import numpy as np

from rknn.api import RKNN

# ------------------------------------------------------------
# 预处理参数：按你的模型改
#   YOLOv5 / YOLOv8（ultralytics 导出）一般用 mean=0, std=255（即像素 /255 归一化）
#   如果你的模型训练时没做归一化，就都填 0 和不填 std
# ------------------------------------------------------------
MEAN_VALUES = [[0, 0, 0]]
STD_VALUES = [[255, 255, 255]]

TARGET = "rk3588"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("onnx", help="输入的 .onnx 文件")
    ap.add_argument("--out", default=None, help="输出的 .rknn 路径（默认同名加 _rk3588）")
    ap.add_argument("--int8", metavar="CALIB_DIR", default=None,
                    help="INT8 量化：校准图片目录（目录里要有 dataset.txt）")
    ap.add_argument("--input-shape", default="1,3,640,640",
                    help="输入形状，按 ONNX 的 NCHW 写，例 1,3,640,640（默认 YOLO）")
    args = ap.parse_args()

    out = args.out or os.path.splitext(args.onnx)[0] + "_rk3588.rknn"

    rknn = RKNN(verbose=True)

    # ---------- ① config ----------
    print("\n== ① config ==")
    ret = rknn.config(
        mean_values=MEAN_VALUES,
        std_values=STD_VALUES,
        target_platform=TARGET,
    )
    if ret != 0:
        sys.exit("config 失败")

    # ---------- ② load_onnx ----------
    print("\n== ② load_onnx ==")
    if rknn.load_onnx(model=args.onnx) != 0:
        sys.exit("load_onnx 失败（ONNX 路径对不对？模型是不是动态 shape？）")

    # ---------- ③ build ----------
    print("\n== ③ build ==")
    if args.int8:
        dataset = os.path.join(args.int8, "dataset.txt")
        if not os.path.isfile(dataset):
            sys.exit(f"INT8 量化需要校准集清单: {dataset}\n"
                     "格式：每行一张图片路径（相对 dataset.txt 所在目录）")
        print(f"INT8 量化，校准集: {dataset}")
        ret = rknn.build(do_quantization=True, dataset=dataset)
    else:
        print("FP16（不做量化）")
        ret = rknn.build(do_quantization=False)
    if ret != 0:
        sys.exit("build 失败 —— 多半是遇到不支持的算子，见 docs/01 第 6 周")

    # ---------- ④ export ----------
    print("\n== ④ export_rknn ==")
    if rknn.export_rknn(out) != 0:
        sys.exit("export 失败")
    size_mb = os.path.getsize(out) / 1024 / 1024
    print(f"已生成: {out}  ({size_mb:.1f} MB)")

    # ---------- ⑤ 仿真推理（PC 上模拟 NPU，不需要板子）----------
    print("\n== ⑤ 仿真推理 ==")
    # init_runtime() 不传 target，就是在 PC 上仿真
    if rknn.init_runtime() != 0:
        sys.exit("init_runtime（仿真）失败")
    nchw = tuple(int(x) for x in args.input_shape.split(","))
    fake_nchw = np.zeros(nchw, dtype=np.uint8)
    # ⚠️ 关键：RKNN 的 inference() 默认 data_format='nhwc'，
    #    而 ONNX / PyTorch 是 NCHW，所以这里要转一次，否则报
    #    "The input(ndarray) shape (1,3,640,640) is wrong, expect 'nhwc' like (1,640,640,3)!"
    fake = np.transpose(fake_nchw, (0, 2, 3, 1)) if len(nchw) == 4 else fake_nchw
    print("输入形状: ONNX/NCHW =", fake_nchw.shape, "-> 喂给 NPU 的 NHWC =", fake.shape)
    outs = rknn.inference(inputs=[fake])
    print("输出个数:", len(outs))
    for i, o in enumerate(outs):
        print(f"  输出{i}: shape={o.shape} dtype={o.dtype}")

    rknn.release()
    print("\n成功：.rknn 已生成，且能在 PC 上仿真推理。")
    print("下一步：scp 到板子上，用 rknn_toolkit_lite2 跑真实推理。")


if __name__ == "__main__":
    main()
