# ============================================================
# 阶段① / Day 1：先看清 YOLO 的输出（不写后处理）
# ============================================================
# 用法:
#   cd ~/projects/rknn
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn
#   python3 yolo_inspect.py                     # 自动挑 ~/datasets/images 里第一张图
#   python3 yolo_inspect.py /path/to/图.jpg      # 也可以指定图片
#
# 它只干一件事：喂一张图进 ONNX，把 3 个输出的形状和【数值范围】打印出来。
#
# 为什么先干这个:
#   后处理的第一步是"要不要自己 sigmoid"，这取决于模型的输出范围。
#   这件事必须用数字说话，不能猜。
#
# 判读方法见 docs/12-目标检测与YOLO入门.md §9
# ============================================================

import os
import sys
import glob

import numpy as np
import cv2
import onnxruntime as ort


MODEL_PATH = os.path.expanduser("~/projects/rknn/model/yolov5s_relu.onnx")
INPUT_SIZE = 640


def pick_image():
    """优先用命令行给的路径，否则从 ~/datasets/images 里挑一张。"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    files = sorted(glob.glob(os.path.expanduser("~/datasets/images/*.jpg")))
    if not files:
        files = sorted(glob.glob(os.path.expanduser("~/datasets/images/*.png")))
    return files[0] if files else None


def letterbox(img, size=INPUT_SIZE):
    """
    保持比例缩放到 size x size，空的地方填灰边（YOLO 的标准做法）。
    返回: 处理后的图, 缩放系数 r, 左边填充 left, 上边填充 top
    ★ 这三个数后处理要用：算出来的框要"反向映射"回原图。
    """
    h, w = img.shape[:2]                                  # 先高后宽
    r = min(size / h, size / w)                           # 取小的，保证装得下
    nh, nw = int(round(h * r)), int(round(w * r))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)   # dsize 先宽后高
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)                # 114 = YOLO 标准灰
    top = (size - nh) // 2
    left = (size - nw) // 2
    canvas[top:top + nh, left:left + nw] = resized                        # 切片赋值
    return canvas, r, left, top


def main():
    # ---------- 1. 准备输入图 ----------
    path = pick_image()
    img = cv2.imread(path) if path else None

    if img is None:
        if path:
            print(f"读图失败: {path}")
        print("用随机噪声当输入（形状和范围检查照样有效，但分数会没有意义）\n")
        img = np.random.randint(0, 256, (1080, 1920, 3), dtype=np.uint8)
    else:
        print(f"输入图片: {path}")
        print(f"  原始 shape (高, 宽, 通道) = {img.shape}")

    # ---------- 2. letterbox ----------
    box, r, pad_left, pad_top = letterbox(img, INPUT_SIZE)
    print(f"letterbox 后 = {box.shape}")
    print(f"  缩放系数 r = {r:.4f}   左填充 = {pad_left}   上填充 = {pad_top}")
    print("  ★ 记住这三个数：把框映射回原图时要减 pad、再除以 r\n")

    # ---------- 3. 转成模型要的格式 ----------
    # BGR -> RGB        （OpenCV 读进来是 BGR，YOLO 要 RGB）
    # HWC -> CHW        （图是"先高后宽"，模型要"先通道"）
    # 加 batch 维 -> NCHW
    # 除以 255 归一化到 0~1
    blob = box[:, :, ::-1].astype(np.float32) / 255.0
    blob = np.transpose(blob, (2, 0, 1))[None, ...]
    blob = np.ascontiguousarray(blob)
    print(f"喂给模型的 blob = {blob.shape}  dtype = {blob.dtype}")
    print("  (1, 3, 640, 640) = (batch, 通道, 高, 宽)\n")

    # ---------- 4. 加载模型 ----------
    if not os.path.exists(MODEL_PATH):
        print(f"找不到模型: {MODEL_PATH}")
        print("检查一下 ~/projects/rknn/model/ 里有什么：")
        for f in glob.glob(os.path.expanduser("~/projects/rknn/model/*")):
            print("   ", f)
        raise SystemExit(1)

    print(f"加载模型: {MODEL_PATH}")
    sess = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    in_name = sess.get_inputs()[0].name
    out_names = [o.name for o in sess.get_outputs()]
    print(f"  输入名: {in_name}")
    print(f"  输出个数: {len(out_names)}")
    for o in sess.get_outputs():
        print(f"    {o.name}: {o.shape}")

    # ---------- 5. 推理 ----------
    print("\n推理中……")
    outputs = sess.run(out_names, {in_name: blob})

    # ---------- 6. 报告 ----------
    line = "=" * 68
    print("\n" + line)
    print(" 输出报告   ★ 重点看 min / max")
    print(line)

    for i, out in enumerate(outputs):
        print(f"输出{i}: shape={out.shape}  dtype={out.dtype}")
        print(f"        min={out.min():+.4f}   max={out.max():+.4f}   mean={out.mean():+.4f}")

        # 标准 YOLOv5 头：通道数 = 3 anchors x 85   通道4 = obj, 通道5 = 第0类
        if out.ndim == 4 and out.shape[1] % 85 == 0:
            ch = out[0]
            n_anchor = out.shape[1] // 85
            print(f"        通道数 {out.shape[1]} = {n_anchor} anchors x 85")
            print(f"        通道4 (obj_conf) 范围: {ch[4].min():+.4f} ~ {ch[4].max():+.4f}")
            print(f"        通道5 (第0类分数) 范围: {ch[5].min():+.4f} ~ {ch[5].max():+.4f}")
        print()

    print(line)
    print("""
判读方法:
  ┌────────────────────────────────────┬──────────────────────────────┐
  │ 所有值都在 0 ~ 1 之间              │ 模型已内置 sigmoid           │
  │                                    │ → 后处理不用再 sigmoid       │
  ├────────────────────────────────────┼──────────────────────────────┤
  │ 出现负数，或存在 > 1 的值          │ 输出是原始 logits            │
  │                                    │ → 后处理要自己 sigmoid()     │
  ├────────────────────────────────────┼──────────────────────────────┤
  │ 输出不是 3 个 / 通道不是 255 的倍数│ 不是标准 YOLOv5 导出格式     │
  │                                    │ → 把上面整段贴给我           │
  └────────────────────────────────────┴──────────────────────────────┘

另外注意:
  · 用随机噪声跑的时候，分数本身没有意义（模型没见过噪声），但"范围"照样能判断。
  · 如果 max 明显小于 1 且 min 接近 0（比如 0.001 ~ 0.3），这也是 sigmoid 之后的特征。
""")
    print(line)
    print("下一步: 把上面整段输出贴给我 → 我给你写完整的 yolo_infer.py")
    print(line)


if __name__ == "__main__":
    main()
