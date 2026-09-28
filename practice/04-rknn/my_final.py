# ============================================================
# my_final.py —— 任务 5：组装完整流水线（图 → 框）
# ============================================================
# 目标: 自己写出完整后处理，结果要和 yolo_infer.py 在 test1.jpg 上【一致】
#
# 用法:
#   cd ~/projects/rknn
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn
#   python3 my_final.py
#
# ★ 标了【你写】的地方 = 你要填的
# ★ 每一步都打印了中间结果，哪一步不对一眼就能看出来
#
# 讲解: docs/16-系统教材-从一张图到车牌号.md 第 5、6、7 章 + 第 10 章流程图
# ============================================================

import os
import numpy as np
import cv2
import onnxruntime as ort

from yolo_infer import COCO_NAMES          # 80 个类别名，借用


# ============================================================
# 0. 我给你的：letterbox（第 7 章"上半部分"）
#    反向映射那两行在下面【你写】——那才是重点
# ============================================================
def letterbox(img, size=640):
    """保比例缩放 + 灰边填充。返回: 图, r, 左填充, 上填充, 内容宽, 内容高"""
    h, w = img.shape[:2]
    r = min(size / h, size / w)
    nh, nw = int(round(h * r)), int(round(w * r))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    top = (size - nh) // 2
    left = (size - nw) // 2
    canvas[top:top + nh, left:left + nw] = resized
    return canvas, r, left, top, nw, nh


# ============================================================
# 1. 【粘贴区】把你已经写好的东西搬过来
# ============================================================
# 【粘贴 1】从 my_yolo.py 复制过来：
#     STRIDES = [8, 16, 32]
#     ANCHORS = [ ... 三个 np.array ... ]
#     def decode_scale(out, stride, anchors): ...
#
# 【粘贴 2】从 my_nms.py 复制过来：
#     def iou_many(box, boxes): ...
#     def nms(boxes, scores, iou_thresh): ...


# ============================================================
# 2. 【你写】收集一个尺度的所有框
# ============================================================
def collect_one_scale(out, stride, anchors, conf_thresh):
    """
    out : (1, 255, H, W)
    返回: boxes (N,4) xyxy（letterbox 坐标）, scores (N,), class_ids (N,)
    """
    o = out[0]                                  # (255, H, W)
    H, W = o.shape[-2], o.shape[-1]
    o = o.reshape(3, 85, H, W)                  # (3, 85, H, W)

    # ---- 解码：调用你写好的函数 ----
    cx, cy, w, h = decode_scale(out, stride, anchors)

    # ---- ① 中心+宽高 → 左上+右下 ----
    # 【你写】4 行
    x1 = ...
    y1 = ...
    x2 = ...
    y2 = ...

    # ---- ② 置信度 ----
    # obj = o[:, 4]        形状 (3, H, W)
    # cls = o[:, 5:]       形状 (3, 80, H, W)
    # 【你写】5 行
    obj     = ...
    cls     = ...
    cls_max = ...       # 每个格子的最大类分数       形状 (3,H,W)
    cls_id  = ...       # 最大分数对应的类别【下标】 形状 (3,H,W)
                        #   提示: cls.argmax(axis=1) —— 沿着"类别"那一维找最大
    conf    = ...       # obj × cls_max

    # ---- ③ 过滤 + 拉平成 (N,4)（这段是数组搬运，我写给你）----
    mask = conf > conf_thresh                   # (3,H,W) 布尔
    boxes = np.stack([x1[mask], y1[mask], x2[mask], y2[mask]], axis=1)
    return boxes.astype(np.float32), conf[mask].astype(np.float32), cls_id[mask].astype(np.int32)


# ============================================================
# 3. 主流程
# ============================================================
if __name__ == "__main__":
    IMG_PATH = os.path.expanduser("~/datasets/images/test1.jpg")
    MODEL_PATH = os.path.expanduser("~/projects/rknn/model/yolov5s_relu.onnx")
    OUT_DIR = os.path.expanduser("~/datasets/output_detect")
    CONF_THRESH = 0.5
    IOU_THRESH = 0.45

    # ---------- [1] 读图 + letterbox ----------
    print("=" * 64)
    print(" [1] 读图 + letterbox")
    print("=" * 64)
    img = cv2.imread(IMG_PATH)
    if img is None:
        raise SystemExit(f"读图失败: {IMG_PATH}")
    H0, W0 = img.shape[:2]
    box, r, pad_left, pad_top, content_w, content_h = letterbox(img)
    print(f"  原图       {W0} x {H0}")
    print(f"  letterbox  {box.shape}   r={r:.4f}  pad_left={pad_left}  pad_top={pad_top}")
    print(f"  内容区     x[{pad_left}, {pad_left+content_w}]  y[{pad_top}, {pad_top+content_h}]")

    # ---------- [2] 推理 ----------
    blob = box[:, :, ::-1].astype(np.float32) / 255.0
    blob = np.ascontiguousarray(np.transpose(blob, (2, 0, 1))[None, ...])
    sess = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    outs = sess.run([o.name for o in sess.get_outputs()],
                    {sess.get_inputs()[0].name: blob})

    # ---------- [3] 三个尺度收集 → 拼接 ----------
    print()
    print("=" * 64)
    print(f" [3] 收集候选框（置信度 > {CONF_THRESH}）")
    print("=" * 64)
    all_boxes, all_scores, all_cls = [], [], []
    for i, out in enumerate(outs):
        b, s, c = collect_one_scale(out, STRIDES[i], ANCHORS[i], CONF_THRESH)
        print(f"  尺度{i} stride={STRIDES[i]:2d}  过阈值 {len(b):5d} 个")
        if len(b):
            all_boxes.append(b)
            all_scores.append(s)
            all_cls.append(c)

    if not all_boxes:
        raise SystemExit("  没有任何候选框通过阈值")

    boxes = np.concatenate(all_boxes)
    scores = np.concatenate(all_scores)
    class_ids = np.concatenate(all_cls)
    print(f"  合计 {len(boxes)} 个候选      （yolo_infer 的结果是 44 个）")

    # ---------- [4] 内容区过滤 ----------
    print()
    print("=" * 64)
    print(" [4] 内容区过滤（框中心必须落在真正有画面的区域里）")
    print("=" * 64)
    # 【你写】
    # 1) 算每个框的中心:  cx = (x1+x2)/2   cy = (y1+y2)/2
    # 2) 判断中心是否同时满足：
    #       cx 在 [pad_left, pad_left+content_w] 之间
    #       cy 在 [pad_top , pad_top +content_h] 之间
    # 3) 用这个布尔数组筛 boxes / scores / class_ids
    # 提示: 多个条件同时成立用 & ，每个条件都要加括号
    cx_all = ...
    cy_all = ...
    inside = ...
    boxes, scores, class_ids = boxes[inside], scores[inside], class_ids[inside]
    print(f"  过滤后 {len(boxes)} 个      （yolo_infer 的结果是 44 个）")

    # ---------- [5] NMS ----------
    print()
    print("=" * 64)
    print(f" [5] NMS（IoU 阈值 {IOU_THRESH}）")
    print("=" * 64)
    keep = nms(boxes, scores, IOU_THRESH)
    boxes, scores, class_ids = boxes[keep], scores[keep], class_ids[keep]
    print(f"  NMS 后 {len(boxes)} 个      （yolo_infer 的结果是 3 个）")

    # 按分数排序
    order = scores.argsort()[::-1]
    boxes, scores, class_ids = boxes[order], scores[order], class_ids[order]

    # ---------- [6] 反向映射回原图 ----------
    print()
    print("=" * 64)
    print(" [6] 反向映射（letterbox 坐标 → 原图坐标）")
    print("=" * 64)
    # 【你写】
    # x_原图 = (x_letterbox - pad_left) / r
    # y_原图 = (y_letterbox - pad_top ) / r
    # 提示: boxes[:, [0, 2]] 是"所有框的 x1 和 x2"，boxes[:, [1, 3]] 是 y1 和 y2
    ob = boxes.copy()
    ob[:, [0, 2]] = ...
    ob[:, [1, 3]] = ...
    # 裁到图像范围内（别让框跑出画面）
    ob[:, [0, 2]] = np.clip(ob[:, [0, 2]], 0, W0 - 1)
    ob[:, [1, 3]] = np.clip(ob[:, [1, 3]], 0, H0 - 1)

    # ---------- [7] 报告 + 画框 ----------
    print()
    print("=" * 64)
    print(" [7] 检测结果")
    print("=" * 64)
    print(f"{'#':>2}  {'类别':<14}{'置信度':>8}   {'letterbox 坐标':<26}原图坐标")
    for i in range(len(ob)):
        nm = COCO_NAMES[class_ids[i]] if class_ids[i] < len(COCO_NAMES) else str(class_ids[i])
        lb = f"({boxes[i][0]:.0f},{boxes[i][1]:.0f})-({boxes[i][2]:.0f},{boxes[i][3]:.0f})"
        og = f"({ob[i][0]:.0f},{ob[i][1]:.0f})-({ob[i][2]:.0f},{ob[i][3]:.0f})"
        print(f"{i:>2}  {nm:<14}{scores[i]:>8.4f}   {lb:<26}{og}")

    os.makedirs(OUT_DIR, exist_ok=True)
    vis = img.copy()
    for i in range(len(ob)):
        x1, y1, x2, y2 = [int(v) for v in ob[i]]
        nm = COCO_NAMES[class_ids[i]] if class_ids[i] < len(COCO_NAMES) else str(class_ids[i])
        label = f"{nm} {scores[i]:.2f}"
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(vis, label, (x1 + 2, max(y1 - 6, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    out_path = os.path.join(OUT_DIR, "detect_final.jpg")
    cv2.imwrite(out_path, vis)
    print(f"\n  已保存: {out_path}")

    # ---------- [8] 和 yolo_infer.py 对比 ----------
    print()
    print("=" * 64)
    print(" [8] 验收：应该和 yolo_infer.py 的结果一致")
    print("=" * 64)
    print("  yolo_infer.py 的答案（同一张图、同样阈值）:")
    print("    候选 44 个 → NMS 后 3 个")
    print("    第 1 个是 person，置信度约 0.8616，原图坐标约 (3582,2040)-(3865,2825)")
    print()
    if len(scores) > 0:
        print(f"  你的结果: {len(scores)} 个框")
        print(f"    第 1 个是 {COCO_NAMES[class_ids[0]]}，置信度 {scores[0]:.4f}，"
              f"原图坐标 ({ob[0][0]:.0f},{ob[0][1]:.0f})-({ob[0][2]:.0f},{ob[0][3]:.0f})")
        print()
        print("  对得上 = 第 4 层封版 ✅")
