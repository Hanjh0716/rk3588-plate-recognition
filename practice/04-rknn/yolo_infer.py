# ============================================================
# 阶段① / Day 2：完整的 YOLO 推理 + 后处理 + 画框
# ============================================================
# 用法:
#   cd ~/projects/rknn
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn
#   python3 yolo_infer.py                       # 自动挑 ~/datasets/images 里第一张
#   python3 yolo_infer.py /path/to/图.jpg        # 指定图片
#   python3 yolo_infer.py 图.jpg 0.5             # 第2个参数 = 置信度阈值
#
# 流程:  letterbox -> 推理 -> 解码 -> 过滤 -> NMS -> 映射回原图 -> 画框 -> 存图
#
# ★ 本脚本的三个关键决定（都由 yolo_probe.py 的实测数据得出）:
#   1) 模型输出【已经 sigmoid 过】了       -> 解码时不再 sigmoid
#   2) 通道4 的 objectness 是【死的】      -> 置信度只用 max(类分数)，不乘 obj
#       实测: 19200 个格子上 obj 最大值只有 0.0006
#   3) 输出是【原始偏移量】，不是绝对坐标  -> 必须自己做 grid + anchor 解码
#       实测: 通道0~3 的值都压在 0~1（≈0.5 附近），若是绝对坐标会是 0~640
#
# 讲解见 docs/12-目标检测与YOLO入门.md §4
# ============================================================

import os
import sys
import glob
import time

import numpy as np
import cv2
import onnxruntime as ort


MODEL_PATH = os.path.expanduser("~/projects/rknn/model/yolov5s_relu.onnx")
OUT_DIR = os.path.expanduser("~/datasets/output_detect")
INPUT_SIZE = 640
IOU_THRESH = 0.45
USE_OBJ = False          # ★ 本模型的 obj 通道是死的，所以不用它

# 阈值可以从命令行给（第 2 个参数）
# ★ 默认从 0.35 提到 0.5：类分支是 softmax（各类互斥、和为 1），
#   所以背景格子也一定有个"赢家"，分数不会整体很低 —— 阈值必须比 sigmoid 时更高。
CONF_THRESH = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

# YOLOv5s 的标准 anchor（按尺度排列）
ANCHORS = np.array([
    [[10, 13], [16, 30], [33, 23]],            # stride 8    -> 80x80
    [[30, 61], [62, 45], [59, 119]],           # stride 16   -> 40x40
    [[116, 90], [156, 198], [373, 326]],       # stride 32   -> 20x20
], dtype=np.float32)
STRIDES = [8, 16, 32]

# COCO 80 类（下标就是模型输出的类别索引）
COCO_NAMES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush",
]


# ------------------------------------------------------------
def pick_image():
    if len(sys.argv) > 1:
        return sys.argv[1]
    for pat in ("*.jpg", "*.png", "*.jpeg", "*.JPG", "*.PNG"):
        files = sorted(glob.glob(os.path.join(os.path.expanduser("~/datasets/images"), pat)))
        if files:
            return files[0]
    return None


def letterbox(img, size=INPUT_SIZE):
    """保持比例缩放 + 灰边填充。返回 图, 缩放系数 r, 左填充, 上填充, 内容宽, 内容高"""
    h, w = img.shape[:2]
    r = min(size / h, size / w)
    nh, nw = int(round(h * r)), int(round(w * r))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    top = (size - nh) // 2
    left = (size - nw) // 2
    canvas[top:top + nh, left:left + nw] = resized
    return canvas, r, left, top, nw, nh


def decode_scale(out, stride, anchors, conf_thresh):
    """
    把一个尺度的输出解码成框。
    out: (1, 255, H, W)   ->   reshape 成 (3 anchors, 85, H, W)
    85 = [cx, cy, w, h, obj] + 80 个类分数（都已经 sigmoid 过）
    返回: boxes(N,4) xyxy(letterbox 坐标), scores(N,), class_ids(N,)
    """
    c, h, w = out.shape[1], out.shape[2], out.shape[3]
    na = c // 85
    o = out[0].reshape(na, 85, h, w)

    # 网格坐标（先高后宽！）
    grid_y, grid_x = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")

    tx = o[:, 0]                    # (na, h, w)  已经 sigmoid
    ty = o[:, 1]
    tw = o[:, 2]
    th = o[:, 3]
    obj = o[:, 4]                   # 死通道，实测 ≈0
    cls = o[:, 5:]                  # (na, 80, h, w)

    # ★ 解码公式（YOLOv5 标准）
    cx = (tx * 2 - 0.5 + grid_x[None]) * stride
    cy = (ty * 2 - 0.5 + grid_y[None]) * stride
    bw = (tw * 2) ** 2 * anchors[:, 0][:, None, None]
    bh = (th * 2) ** 2 * anchors[:, 1][:, None, None]

    cls_conf = cls.max(axis=1)      # (na, h, w) 最大类分数
    cls_id = cls.argmax(axis=1)

    # 置信度：不用 obj（它是死的）
    conf = cls_conf * obj if USE_OBJ else cls_conf

    mask = conf > conf_thresh
    if not mask.any():
        return (np.zeros((0, 4), np.float32), np.zeros(0, np.float32),
                np.zeros(0, np.int32), 0)

    n_total = int(mask.sum())
    cx, cy, bw, bh = cx[mask], cy[mask], bw[mask], bh[mask]
    conf_v = conf[mask]
    cls_v = cls_id[mask]

    boxes = np.stack([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], axis=1)
    return boxes.astype(np.float32), conf_v.astype(np.float32), cls_v.astype(np.int32), n_total


def nms(boxes, scores, class_ids, iou_thresh):
    """按类别分别做 NMS：给不同类别的框加上很大的坐标偏移，让它们互不抑制。"""
    if len(boxes) == 0:
        return np.zeros(0, np.int32)
    off = class_ids.astype(np.float32) * 1e5
    b = boxes + off[:, None]

    x1, y1, x2, y2 = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    areas = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        if order.size == 1:
            break
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-9)
        order = order[1:][iou <= iou_thresh]
    return np.array(keep, dtype=np.int32)


def main():
    path = pick_image()
    img = cv2.imread(path) if path else None
    if img is None:
        print(f"读图失败或没找到图片: {path}")
        print("把一张真实照片（有人/车/动物）放进 ~/datasets/images/ 再试")
        raise SystemExit(1)

    H0, W0 = img.shape[:2]
    print(f"输入图片: {path}")
    print(f"  原始尺寸: 宽 {W0} x 高 {H0}")
    print(f"  阈值: 置信度 {CONF_THRESH}   IoU {IOU_THRESH}   obj通道: "
          f"{'使用' if USE_OBJ else '不使用（实测是死的）'}")

    box, r, pad_left, pad_top, cw, ch = letterbox(img)
    print(f"  letterbox: r={r:.4f}  左填充={pad_left}  上填充={pad_top}  "
          f"内容区 x[{pad_left},{pad_left+cw}] y[{pad_top},{pad_top+ch}]")

    blob = box[:, :, ::-1].astype(np.float32) / 255.0
    blob = np.ascontiguousarray(np.transpose(blob, (2, 0, 1))[None, ...])

    sess = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    in_name = sess.get_inputs()[0].name
    out_names = [o.name for o in sess.get_outputs()]

    t0 = time.time()
    outputs = sess.run(out_names, {in_name: blob})
    t1 = time.time()
    print(f"\n推理耗时: {(t1-t0)*1000:.1f} ms   (纯 CPU，板子上换 NPU 会快很多)")

    # ---------- 解码三个尺度 ----------
    print("\n" + "=" * 70)
    print(" 解码")
    print("=" * 70)
    all_boxes, all_scores, all_cls = [], [], []
    for i, out in enumerate(outputs):
        stride = STRIDES[i]
        anchors = ANCHORS[i]
        b, s, c, n = decode_scale(out, stride, anchors, CONF_THRESH)
        print(f" 尺度{i} stride={stride:2d} 输出{tuple(out.shape)} -> "
              f"过阈值 {n:6d} 个候选")
        if len(b):
            all_boxes.append(b); all_scores.append(s); all_cls.append(c)

    if not all_boxes:
        print("\n⚠️  没有任何候选框通过阈值。")
        print("   1) 先降阈值试试:  python3 yolo_infer.py 图片 0.1")
        print("   2) 如果还是 0，说明这张图里没有 COCO 认识的东西（人/车/动物…）")
        print("      —— 换一张真实照片。合成的测试图不算。")
        raise SystemExit(0)

    boxes = np.concatenate(all_boxes)
    scores = np.concatenate(all_scores)
    cls_ids = np.concatenate(all_cls)
    print(f"\n 三尺度合计候选: {len(boxes)}")

    # ---------- 过滤1：框必须落在 letterbox 的内容区里 ----------
    cx = (boxes[:, 0] + boxes[:, 2]) / 2
    cy = (boxes[:, 1] + boxes[:, 3]) / 2
    bw = boxes[:, 2] - boxes[:, 0]
    bh = boxes[:, 3] - boxes[:, 1]
    inside = ((cx >= pad_left) & (cx <= pad_left + cw) &
              (cy >= pad_top) & (cy <= pad_top + ch) &
              (bw > 2) & (bh > 2))
    print(f" 去掉落在灰边上的 / 尺寸荒谬的: -{int((~inside).sum())} 个")
    boxes, scores, cls_ids = boxes[inside], scores[inside], cls_ids[inside]

    # ---------- 过滤2：NMS ----------
    keep = nms(boxes, scores, cls_ids, IOU_THRESH)
    print(f" NMS 之后: {len(keep)} 个")
    boxes, scores, cls_ids = boxes[keep], scores[keep], cls_ids[keep]

    # ---------- 排序，只留前 20 个 ----------
    order = scores.argsort()[::-1][:20]
    boxes, scores, cls_ids = boxes[order], scores[order], cls_ids[order]

    # ---------- 映射回原图坐标 ----------
    ob = boxes.copy()
    ob[:, [0, 2]] = (ob[:, [0, 2]] - pad_left) / r
    ob[:, [1, 3]] = (ob[:, [1, 3]] - pad_top) / r
    ob[:, [0, 2]] = np.clip(ob[:, [0, 2]], 0, W0 - 1)
    ob[:, [1, 3]] = np.clip(ob[:, [1, 3]], 0, H0 - 1)

    # ---------- 报告 ----------
    print("\n" + "=" * 70)
    print(" 检测结果（按置信度排序）")
    print("=" * 70)
    print(f"{'#':>2}  {'类别':<14}{'置信度':>8}   {'letterbox 坐标':<28}{'原图坐标'}")
    for i in range(len(boxes)):
        nm = COCO_NAMES[cls_ids[i]] if cls_ids[i] < len(COCO_NAMES) else str(cls_ids[i])
        lb = f"({boxes[i][0]:.0f},{boxes[i][1]:.0f})-({boxes[i][2]:.0f},{boxes[i][3]:.0f})"
        og = f"({ob[i][0]:.0f},{ob[i][1]:.0f})-({ob[i][2]:.0f},{ob[i][3]:.0f})"
        print(f"{i:>2}  {nm:<14}{scores[i]:>8.4f}   {lb:<28}{og}")

    # ---------- 画框 ----------
    os.makedirs(OUT_DIR, exist_ok=True)
    vis = img.copy()
    for i in range(len(ob)):
        x1, y1, x2, y2 = [int(v) for v in ob[i]]
        nm = COCO_NAMES[cls_ids[i]] if cls_ids[i] < len(COCO_NAMES) else str(cls_ids[i])
        label = f"{nm} {scores[i]:.2f}"
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        ty = max(y1 - 6, th + 4)                       # 别让文字跑出画面
        cv2.rectangle(vis, (x1, ty - th - 4), (x1 + tw + 4, ty + 2), (0, 255, 0), -1)
        cv2.putText(vis, label, (x1 + 2, ty - 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    name = os.path.basename(path)
    out_path = os.path.join(OUT_DIR, "detect_" + name)
    cv2.imwrite(out_path, vis)
    print(f"\n已保存: {out_path}")
    print(f"在 Windows 里看:  explorer.exe \"$(wslpath -w {OUT_DIR})\"")

    # ---------- 附1：类分数是 softmax 还是逐类 sigmoid？ ----------
    print("\n" + "=" * 70)
    print(" 附加诊断 1：类分数是 softmax 还是逐类 sigmoid？")
    print("=" * 70)
    s_best = None
    for i, out in enumerate(outputs):
        H, W = out.shape[2], out.shape[3]
        na = out.shape[1] // 85
        o = out[0].reshape(na, 85, H, W)
        cls = o[:, 5:]                                   # (na, 80, H, W)  ← 4 维
        k = int(cls.reshape(-1).argmax())
        a, ci, y, x = np.unravel_index(k, cls.shape)     # ★ 4 维 → 4 个索引
        v80 = o[a, 5:, y, x]
        if s_best is None or float(v80.max()) > s_best[0]:
            s_best = (float(v80.max()), float(v80.sum()),
                      i, int(a), int(ci), int(y), int(x))

    print(f" 全场最高类分数       = {s_best[0]:.4f}")
    print(f" 它那 80 个类分数之和 = {s_best[1]:.4f}")
    print("   和 ≈ 1.0      -> 是 softmax（各类互斥，背景格子也必有'赢家'）")
    print("   和 明显 != 1  -> 是逐类 sigmoid（背景格子可以整体很低）")
    print(f" 位置: 尺度{s_best[2]}(stride={STRIDES[s_best[2]]}) anchor {s_best[3]} "
          f"类别索引 {s_best[4]} 格子(y={s_best[5]}, x={s_best[6]})")

    # ---------- 附2：阈值扫描 ----------
    print("\n" + "=" * 70)
    print(" 附加诊断 2：不同阈值下 NMS 后剩多少个框（用来看该选哪个阈值）")
    print("=" * 70)
    for th in (0.25, 0.35, 0.45, 0.55, 0.70):
        bs, ss, cs = [], [], []
        for i, out in enumerate(outputs):
            b, s, c, _ = decode_scale(out, STRIDES[i], ANCHORS[i], th)
            if len(b):
                bs.append(b); ss.append(s); cs.append(c)
        if not bs:
            print(f" 阈值 {th:.2f}:            0 个")
            continue
        b = np.concatenate(bs); s = np.concatenate(ss); c = np.concatenate(cs)
        cxx = (b[:, 0] + b[:, 2]) / 2
        cyy = (b[:, 1] + b[:, 3]) / 2
        bww = b[:, 2] - b[:, 0]
        bhh = b[:, 3] - b[:, 1]
        m = ((cxx >= pad_left) & (cxx <= pad_left + cw) &
             (cyy >= pad_top) & (cyy <= pad_top + ch) & (bww > 2) & (bhh > 2))
        b, s, c = b[m], s[m], c[m]
        k = nms(b, s, c, IOU_THRESH)
        print(f" 阈值 {th:.2f}:  过滤后 {len(b):5d} 个 -> NMS 后 {len(k):4d} 个")


if __name__ == "__main__":
    main()
