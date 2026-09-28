# ============================================================
# 阶段① / Day 1-B：把 255 个通道的"排布"看清
# ============================================================
# 用法:
#   cd ~/projects/rknn
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn
#   python3 yolo_probe.py                     # 自动挑 ~/datasets/images 里第一张
#   python3 yolo_probe.py /path/to/图.jpg
#
# 为什么要再跑这一步:
#   yolo_inspect.py 看到"所有值都在 0~1"，符合"已内置 sigmoid"的特征。
#   但有一处矛盾：
#       通道4 (obj_conf) 最大只有 0.0006   ← "这里没有东西"
#       通道5 (类分数)   最大却有 0.9658   ← "非常确定是这一类"
#   标准 YOLOv5 里这两个应该同高同低。
#   所以先别下结论 —— 把"85 个数到底怎么排的"直接打出来看。
#
# 本脚本做三件事:
#   诊断1  每个通道索引的"最大值"—— 哪些索引有反应、哪些是死的
#   诊断2  全场分数最高的那个位置，把它那一整组 85 个数原样展开
#   诊断3  两种假设下，通过阈值的候选框数量
# ============================================================

import os
import sys
import glob

import numpy as np
import cv2
import onnxruntime as ort


MODEL_PATH = os.path.expanduser("~/projects/rknn/model/yolov5s_relu.onnx")
INPUT_SIZE = 640
NA = 3        # anchors
NO = 85       # 每个 anchor 的通道数 = 5 + 80


def pick_image():
    if len(sys.argv) > 1:
        return sys.argv[1]
    files = sorted(glob.glob(os.path.expanduser("~/datasets/images/*.jpg")))
    if not files:
        files = sorted(glob.glob(os.path.expanduser("~/datasets/images/*.png")))
    return files[0] if files else None


def letterbox(img, size=INPUT_SIZE):
    h, w = img.shape[:2]
    r = min(size / h, size / w)
    nh, nw = int(round(h * r)), int(round(w * r))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    top = (size - nh) // 2
    left = (size - nw) // 2
    canvas[top:top + nh, left:left + nw] = resized
    return canvas, r, left, top


def main():
    # ---------- 输入 ----------
    path = pick_image()
    img = cv2.imread(path) if path else None
    if img is None:
        print("没有可用图片，用随机噪声代替（诊断1/3 有效，诊断2 的分数无意义）")
        img = np.random.randint(0, 256, (1080, 1920, 3), dtype=np.uint8)
    else:
        print(f"输入图片: {path}")
        print(f"  原始 shape = {img.shape}")

    box, r, pad_left, pad_top = letterbox(img)
    blob = box[:, :, ::-1].astype(np.float32) / 255.0
    blob = np.ascontiguousarray(np.transpose(blob, (2, 0, 1))[None, ...])

    sess = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    in_name = sess.get_inputs()[0].name
    outputs = sess.run([o.name for o in sess.get_outputs()], {in_name: blob})

    line = "=" * 70

    # ==========================================================
    # 诊断1：每个通道索引的最大值
    # ==========================================================
    out0 = outputs[0][0]                     # (255, 80, 80)  最小尺度的支路
    per_idx_max = out0.reshape(255, -1).max(axis=1)

    print("\n" + line)
    print(" 诊断1  255 个通道各自的最大值（看哪些索引'有反应'）")
    print(line)
    print(" 标准 YOLOv5 的排布假设：  [cx, cy, w, h, obj] + 80 个类分数")
    print(" 也就是每个 anchor 的第 0~3 是框偏移，第 4 是 obj，第 5~84 是类分数\n")

    for a in range(NA):
        seg = per_idx_max[a * NO:(a + 1) * NO]
        print(f" --- anchor {a} ---")
        print("   idx  0-4 (cx,cy,w,h,obj?): " + "  ".join(f"{v:.4f}" for v in seg[:5]))
        for start in range(5, 85, 20):
            chunk = seg[start:start + 20]
            print(f"   idx {start:2d}-{start+19:2d}              : "
                  + "  ".join(f"{v:.4f}" for v in chunk))
        hi5 = [i for i in range(NO) if seg[i] > 0.5]
        hi1 = [i for i in range(NO) if seg[i] > 0.1]
        print(f"   > 0.5 的索引: {hi5}")
        print(f"   > 0.1 的索引: {hi1}")
        print(f"   本组最大值: idx {int(seg.argmax())} = {seg.max():.4f}\n")

    # ==========================================================
    # 诊断2：全场最高分位置的完整 85 个数
    # ==========================================================
    print(line)
    print(" 诊断2  全场最高'类分数'所在位置，把它那一整组 85 个数展开")
    print(line)

    best = None
    for a in range(NA):
        grp = out0[a * NO:(a + 1) * NO]        # (85, 80, 80)
        cls = grp[5:]                          # (80, 80, 80)
        k = int(cls.reshape(-1).argmax())
        ci, y, x = np.unravel_index(k, cls.shape)
        val = float(cls[ci, y, x])
        if best is None or val > best[0]:
            best = (val, a, int(ci), int(y), int(x), grp[:, y, x])

    val, a, ci, y, x, vec = best
    print(f" 最高类分数 = {val:.4f}")
    print(f" 位置: anchor {a}, 类别索引 {ci}, 格子 (y={y}, x={x})\n")
    print(" 这个位置的完整 85 个数：")
    for i in range(0, 85, 10):
        print(f"   idx {i:2d}-{i+9:2d}: " + " ".join(f"{v:7.4f}" for v in vec[i:i + 10]))
    print()
    print(" 怎么读这段：")
    print("   · 如果 idx 0~3 大约在 0.3~0.7 之间  → 它们是框的偏移量（正常）")
    print("   · 如果 idx 4 是个较大的值（>0.5）    → obj 就在第 4 位，假设成立")
    print("   · 如果 idx 4 接近 0，而某个 idx>=5 很大 → 排布和假设不一样，把这行贴给我")

    # ==========================================================
    # 诊断3：两种假设下的候选框数量
    # ==========================================================
    print("\n" + line)
    print(" 诊断3  阈值 0.25 下能过多少个候选（三个尺度合计）")
    print(line)

    for si, out in enumerate(outputs):
        o = out[0]
        n = o.shape[0] // NO
        objs, clsm = [], []
        for a in range(n):
            grp = o[a * NO:(a + 1) * NO]
            objs.append(grp[4].reshape(-1))
            clsm.append(grp[5:].max(axis=0).reshape(-1))
        objs = np.concatenate(objs)
        clsm = np.concatenate(clsm)
        na_ = int(((objs * clsm) > 0.25).sum())
        nb_ = int((clsm > 0.25).sum())
        print(f" 输出{si} {tuple(out.shape)}  候选格子总数 {objs.size}")
        print(f"    假设A  conf = obj × max(类分数)  → {na_:6d} 个通过")
        print(f"    假设B  conf = max(类分数)（无obj）→ {nb_:6d} 个通过")

    print()
    print(line)
    print(" 判读")
    print(line)
    print("""  情况①  诊断1 里 idx 0~3 有较大值、idx 4 也有较大值，
          诊断3 假设A 能过几十~几百个
          → 排布就是标准 YOLOv5，且已经 sigmoid 过了。下一步直接写解码+NMS。

  情况②  诊断1 里 idx 4 一直是死的（≈0），但 idx>=5 有高值
          → 排布不是 [cx,cy,w,h,obj,...]，需要按诊断2 的实际排列调整解码。

  情况③  三个尺度诊断3 假设A 都是 0 个
          → 很可能图片是合成的/没有 COCO 里的东西。
            换一张真实照片（有人、车、动物）再跑一次。

  ★ 请把【诊断1 的三个 anchor 段】+【诊断2 的 85 个数】+【诊断3】整段贴回来。
""")
    print(line)


if __name__ == "__main__":
    main()
