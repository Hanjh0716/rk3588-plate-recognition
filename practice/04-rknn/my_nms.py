# ============================================================
# my_nms.py —— 任务 4：自己写 IoU 和 NMS
# ============================================================
# 用法:
#   cd ~/projects/rknn
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn
#   python3 my_nms.py
#
# ★ 三个函数【你来写】，函数体里标了 "你写" 的地方
# ★ 知识点在 docs/16-系统教材-从一张图到车牌号.md 第 6 章
# ============================================================

import numpy as np


# ============================================================
# 任务 4a：iou_one —— 两个框的重叠程度
# ============================================================
def iou_one(a, b):
    """
    a, b : [x1, y1, x2, y2]   左上角 + 右下角
    返回 : 一个 0~1 的数

    思路（照着写就行）:
        交集左上角 x = max(a[0], b[0])      交集左上角 y = max(a[1], b[1])
        交集右下角 x = min(a[2], b[2])      交集右下角 y = min(a[3], b[3])
        交集宽 = max(0, 右下x - 左上x)      ← 可能算成负数，必须用 max(0,...) 兜住
        交集高 = max(0, 右下y - 左上y)
        交集面积 = 交集宽 * 交集高
        面积A = (a[2]-a[0]) * (a[3]-a[1])
        面积B = (b[2]-b[0]) * (b[3]-b[1])
        IoU  = 交集面积 / (面积A + 面积B - 交集面积)
    """
    # ==================== 【你写】 ====================


# ============================================================
# 任务 4b：iou_many —— 一个框 vs 一堆框（向量化）
# ============================================================
def iou_many(box, boxes):
    """
    box   : (4,)     一个框
    boxes : (N, 4)   一堆框
    返回  : (N,)     每个框和 box 的 IoU

    ★ 和 iou_one 是【同一个公式】，只是把 b 换成数组。
    ★ 关键：用 np.maximum / np.minimum（不是 max/min！），它们能一次算 N 个。
    ★ 广播：(4,) 和 (N,4) 从右对齐是能用的，所以不用 [:, None]。
    """
    # ==================== 【你写】 ====================


# ============================================================
# 任务 4c：nms —— 一个目标只留一个框
# ============================================================
def nms(boxes, scores, iou_thresh):
    """
    boxes  : (N, 4)
    scores : (N,)
    返回   : 保留下来的下标数组

    算法（骨架已经给你了，你只需要填两行）:
        ① order = 按分数从高到低排序的下标
        ② while order 不空:
             取 order[0] 作为本轮结果 → 放进 keep
             算 boxes[order[0]] 和 boxes[order[1:]] 每个框的 IoU
             把 IoU > 阈值的从 order 里删掉，只留 <= 阈值的
             去掉已经处理过的 order[0]
        ③ 返回 keep
    """
    order = scores.argsort()[::-1]        # ← 给你：按分数降序排列的【下标】
    keep = []

    while order.size > 0:
        i = order[0]                      # 当前分数最高的那个框
        keep.append(i)

        if order.size == 1:
            break

        # ==================== 【你写 ①】 ====================
        # 用 iou_many 算 boxes[i] 和 boxes[order[1:]] 里每个框的 IoU
        ious = ...

        # ==================== 【你写 ②】 ====================
        # 只保留 IoU <= iou_thresh 的那些下标
        # 提示：order[1:] 是"待处理的下标"，[...] 里放布尔条件做筛选（Day 9 学的布尔索引）
        order = ...

    return np.array(keep)


# ============================================================
# 测试区（这部分我写好了，你只跑，不用改）
# ============================================================
if __name__ == "__main__":
    boxes = np.array([[0, 0, 10, 10],
                      [1, 1, 11, 11],
                      [5, 5, 15, 15],
                      [20, 20, 30, 30]], dtype=np.float32)

    print("=" * 64)
    print(" 任务 4a：iou_one  （两个框）")
    print("=" * 64)
    print("  先手算，再对答案：")
    print("    iou(A,B): 交集 = 9x9 = 81，并集 = 100+100-81 = 119  → 81/119  = 0.6807")
    print("    iou(A,C): 交集 = 5x5 = 25，并集 = 100+100-25 = 175  → 25/175  = 0.1429")
    print("    iou(A,D): 完全不相交                                   → 0.0")
    print()
    print("  iou(A, B) =", iou_one(boxes[0], boxes[1]), "  期望 0.6807")
    print("  iou(A, C) =", iou_one(boxes[0], boxes[2]), "  期望 0.1429")
    print("  iou(A, D) =", iou_one(boxes[0], boxes[3]), "  期望 0.0")

    print()
    print("=" * 64)
    print(" 任务 4b：iou_many  （一个 vs 一堆，向量化）")
    print("=" * 64)
    ious = iou_many(boxes[0], boxes)
    print("  iou_many(boxes[0], boxes) =", ious)
    print("  期望: [1.0, 0.6807, 0.1429, 0.0]")
    print("        ↑ 自己和自己重叠 = 1.0（这是个很好的自检）")
    print()
    print("  ★ 金标准：向量化版本必须复现单点版本")
    ok1 = np.allclose(ious[1], iou_one(boxes[0], boxes[1]))
    ok2 = np.allclose(ious[2], iou_one(boxes[0], boxes[2]))
    print(f"    iou_many()[1] == iou_one(A,B) ? {ok1}")
    print(f"    iou_many()[2] == iou_one(A,C) ? {ok2}")

    print()
    print("=" * 64)
    print(" 任务 4c：nms  （去重）")
    print("=" * 64)
    scores = np.array([0.90, 0.80, 0.70, 0.60], dtype=np.float32)

    print("  4 个框的分数:", scores)
    print("  A 和 B 的 IoU = 0.68（高度重叠）")
    print()
    keep = nms(boxes, scores, 0.45)
    print(f"  阈值 0.45 → keep = {keep}      期望 [0 2 3]")
    print(f"            分数 = {scores[keep]}")
    print("            （B 因为和 A 重叠 0.68 > 0.45，被删掉了）")
    print()
    keep = nms(boxes, scores, 0.80)
    print(f"  阈值 0.80 → keep = {keep}      期望 [0 1 2 3]")
    print("            （阈值放宽到 0.8，B 的 0.68 <= 0.8，所以留下了）")
