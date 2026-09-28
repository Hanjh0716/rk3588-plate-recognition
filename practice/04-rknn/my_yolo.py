# ============================================================
# my_yolo.py —— 自己实现的 YOLO 后处理
# ============================================================
# 阶段①：任务 1（拆通道）/ 3a（单点解码）/ 3b（向量化）/ 3c（三个尺度）
#
# 用法:
#   cd ~/projects/rknn
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn
#   python3 my_yolo.py
#
# 讲解: docs/16-系统教材-从一张图到车牌号.md 第 5 章
# ============================================================

import os
import numpy as np
import cv2
import onnxruntime as ort

from yolo_infer import letterbox          # 借用一下，任务 5 会自己写


# ============================================================
# 第 0 部分：样板 —— 读图 → letterbox → 转 blob → 推理
# ============================================================
IMG_PATH = os.path.expanduser("~/datasets/images/test1.jpg")
MODEL_PATH = os.path.expanduser("~/projects/rknn/model/yolov5s_relu.onnx")

img = cv2.imread(IMG_PATH)
if img is None:
    raise SystemExit(f"读图失败: {IMG_PATH}")

box, r, pad_left, pad_top, content_w, content_h = letterbox(img)

# BGR→RGB、除255、HWC→CHW、加 batch 维
blob = box[:, :, ::-1].astype(np.float32) / 255.0
blob = np.ascontiguousarray(np.transpose(blob, (2, 0, 1))[None, ...])

sess = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
outs = sess.run([o.name for o in sess.get_outputs()],
                {sess.get_inputs()[0].name: blob})

print("图片      :", IMG_PATH)
print("原始 shape:", img.shape)
print("letterbox :", box.shape, "  r =", round(float(r), 4),
      " pad_left =", pad_left, " pad_top =", pad_top)
print("blob      :", blob.shape)
print("模型输出  :", [tuple(o.shape) for o in outs])
print()


# ============================================================
# 任务 3a：解码【一个格子】—— 验证公式
# ============================================================
print("=" * 62)
print(" 任务 3a：解码一个格子")
print("=" * 62)

o2 = outs[2][0].reshape(3, 85, 20, 20)      # 尺度2 = 20x20
a, yy, xx = 1, 14, 17                       # anchor 1，第 14 行、第 17 列

stride_2 = 32
anchors_2 = np.array([[116, 90], [156, 198], [373, 326]], dtype=np.float32)
aw_2, ah_2 = anchors_2[a]                   # 156, 198
grid_x, grid_y = xx, yy                     # ★ 列号是 x，行号是 y

tx = o2[a, 0, yy, xx]
ty = o2[a, 1, yy, xx]
tw = o2[a, 2, yy, xx]
th = o2[a, 3, yy, xx]

print(f"tx,ty,tw,th = {tx:.6f}  {ty:.6f}  {tw:.6f}  {th:.6f}")
print(f"grid=(x={grid_x}, y={grid_y})   stride={stride_2}   anchor=({aw_2}, {ah_2})")

cx = (tx * 2 - 0.5 + grid_x) * stride_2
cy = (ty * 2 - 0.5 + grid_y) * stride_2
w = (tw * 2) ** 2 * aw_2
h = (th * 2) ** 2 * ah_2

print(f"cx,cy,w,h   = {cx:.4f}  {cy:.4f}  {w:.4f}  {h:.4f}")
print("期望        = 581.75  460.03  44.28  122.54")
print()


# ============================================================
# 任务 3b：向量化 —— 3 个 anchor × 20×20 个格子，一次算完
# ============================================================
print("=" * 62)
print(" 任务 3b：向量化（尺度2，全部格子一次算完）")
print("=" * 62)

tx_all = o2[:, 0]        # (3, 20, 20)   ← 切片，不是单点
ty_all = o2[:, 1]
tw_all = o2[:, 2]
th_all = o2[:, 3]

H, W = 20, 20
grid_y_all, grid_x_all = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")

aw_all = anchors_2[:, 0]     # (3,)     ← 整数索引会消掉一维
ah_all = anchors_2[:, 1]     # (3,)

cx_all = (tx_all * 2 - 0.5 + grid_x_all) * stride_2
cy_all = (ty_all * 2 - 0.5 + grid_y_all) * stride_2
w_all = (tw_all * 2) ** 2 * aw_all[:, None, None]    # ★ (3,) → (3,1,1) 才能广播
h_all = (th_all * 2) ** 2 * ah_all[:, None, None]

print("形状检查 (都必须是 (3, 20, 20)):")
print("  cx_all.shape =", cx_all.shape)
print("  cy_all.shape =", cy_all.shape)
print("  w_all.shape  =", w_all.shape)
print("  h_all.shape  =", h_all.shape)

print("复现检查 (必须和 3a 完全一致):")
print(f"  cx_all[1,14,17] = {cx_all[1, 14, 17]}")
print(f"  cy_all[1,14,17] = {cy_all[1, 14, 17]}")
print(f"  w_all [1,14,17] = {w_all[1, 14, 17]}")
print(f"  h_all [1,14,17] = {h_all[1, 14, 17]}")
print()


# ============================================================
# 任务 3c：通用化 —— 三个尺度都跑一遍
# ============================================================
print("=" * 62)
print(" 任务 3c：三个尺度")
print("=" * 62)

STRIDES = [8, 16, 32]

ANCHORS = [
    np.array([[10, 13], [16, 30], [33, 23]], dtype=np.float32),         # 尺度0 (80x80)
    np.array([[30, 61], [62, 45], [59, 119]], dtype=np.float32),        # 尺度1 (40x40)
    np.array([[116, 90], [156, 198], [373, 326]], dtype=np.float32),    # 尺度2 (20x20)
]


def decode_scale(out, stride, anchors):
    """
    out     : (1, 255, H, W)  模型某一个尺度的原始输出
    stride  : 8 / 16 / 32
    anchors : (3, 2)          这个尺度对应的 3 个先验框（宽, 高）
    返回    : cx, cy, w, h    形状都是 (3, H, W)，单位 = letterbox 图像的像素
    """
    o = out[0]                              # (255, H, W)
    H, W = o.shape[1], o.shape[2]           # ★ 不再写死，直接从数组读
    o = o.reshape(3, 85, H, W)              # (3, 85, H, W)

    tx = o[:, 0]
    ty = o[:, 1]
    tw = o[:, 2]
    th = o[:, 3]

    # 网格，形状 (H, W)；indexing="ij" 保证"第0维是行、第1维是列"
    grid_y, grid_x = np.meshgrid(np.arange(H), np.arange(W), indexing="ij")

    # anchor 宽高 (3,) → (3,1,1)，从右对齐才能和 (3,H,W) 广播
    aw = anchors[:, 0][:, None, None]
    ah = anchors[:, 1][:, None, None]

    cx = (tx * 2 - 0.5 + grid_x) * stride
    cy = (ty * 2 - 0.5 + grid_y) * stride
    w = (tw * 2) ** 2 * aw
    h = (th * 2) ** 2 * ah
    return cx, cy, w, h


results = []
for i, out in enumerate(outs):
    cx, cy, w, h = decode_scale(out, STRIDES[i], ANCHORS[i])
    results.append((cx, cy, w, h))
    print(f"尺度{i}  stride={STRIDES[i]:2d}  输出{tuple(out.shape)}   cx.shape={cx.shape}")

print()
total = 0
for i, (cx, cy, w, h) in enumerate(results):
    n = cx.size
    total += n
    print(f"  尺度{i}: {n:6d} 个候选框")
print(f"  合计 : {total:6d} 个候选框")

print()
cx2, cy2, w2, h2 = results[2]
print("复现检查 (必须和 3a/3b 一致):")
print(f"  尺度2 cx[1,14,17] = {cx2[1, 14, 17]}")
print(f"  尺度2 cy[1,14,17] = {cy2[1, 14, 17]}")
print(f"  尺度2 w [1,14,17] = {w2[1, 14, 17]}")
print(f"  尺度2 h [1,14,17] = {h2[1, 14, 17]}")
