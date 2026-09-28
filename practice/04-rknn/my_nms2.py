# ============================================================
# my_nms2.py —— 任务 6：把 NMS 升级成"按类别"
# ============================================================
# 用法:
#   cd ~/projects/rknn
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn
#   python3 my_nms2.py
#
# 目的:
#   任务 4 写的 nms 是【不分类别】的 —— 所有框混在一起压制。
#   问题是：一个人靠在车上时，人和车的框本来就重叠，
#   不分类别做就会把其中一个误删。
#
#   正确做法：每个类别【各自】做一遍 NMS。
#
# ★ 标了【你写】的地方 = 你要填的
# ============================================================

import numpy as np


# ============================================================
# 1. 【粘贴区】把你已经写好的东西搬过来
# ============================================================
# 【粘贴 1】从 my_nms.py 复制过来：
#     def iou_many(box, boxes): ...
#
# 【粘贴 2】从 my_nms.py 复制过来 nms 函数，并且【改个名字】：
#     原来的  def nms(boxes, scores, iou_thresh):
#     改成    def nms_one_class(boxes, scores, iou_thresh):
#
#     因为它现在的职责变成"只对给定的一批框做 NMS"（不管它们是不是同一类）


# ============================================================
# 2. 【你写】按类别做 NMS
# ============================================================
def nms(boxes, scores, class_ids, iou_thresh):
    """
    boxes     : (N, 4)
    scores    : (N,)
    class_ids : (N,)     每个框的类别
    返回      : 保留下来的【全局下标】数组（已排序）

    思路:
        对每一个出现过的类别 c：
            ① 找出所有属于类别 c 的框的【全局下标】
            ② 只把这批框喂给 nms_one_class
            ③ 它返回的是【这批框内部】的下标（0,1,2...）
               要换算成【全局下标】： idx[ 内部下标 ]
            ④ 加进 keep
    """
    keep = []

    for c in np.unique(class_ids):          # np.unique 拿到所有出现过的类别
        # ==================== 【你写 ①】 ====================
        # 属于类别 c 的那些框的【全局下标】
        #   提示: class_ids == c      → 得到一个布尔数组
        #         np.where(...)[0]    → 得到 True 的位置（也就是下标）
        idx = ...

        # ==================== 【你写 ②】 ====================
        # 对这批框单独做 NMS，把结果换算成全局下标，加进 keep
        #   提示: nms_one_class(boxes[idx], scores[idx], iou_thresh)
        #         它返回【内部下标】，要写成 idx[ 内部下标 ] 才是全局下标
        #         然后 keep.extend(...)
        keep.extend(...)

    return np.array(sorted(keep))


# ============================================================
# 测试区（我写好了，你只跑）
# ============================================================
if __name__ == "__main__":
    print("=" * 66)
    print(" 测试 1：类别【不同】但框高度重叠  ← 这是关键测试")
    print("=" * 66)
    boxes = np.array([[0, 0, 10, 10],
                      [1, 1, 11, 11],
                      [20, 20, 30, 30]], dtype=np.float32)
    scores = np.array([0.90, 0.80, 0.70], dtype=np.float32)
    class_ids = np.array([0, 2, 0])          # 0 = person, 2 = car

    print("  box0 = person  分数 0.90")
    print("  box1 = car     分数 0.80   ← 和 box0 重叠 0.68")
    print("  box2 = person  分数 0.70   ← 和谁都不重叠")
    print()
    print("  不分类别 (nms_one_class) →", nms_one_class(boxes, scores, 0.45),
          "   期望 [0 2]")
    print("  按类别   (nms)          →", nms(boxes, scores, class_ids, 0.45),
          "   期望 [0 1 2]")
    print()
    print("  ↑ 差别就在 box1：person 和 car 不该互相压制，所以 car 应该留下")

    print()
    print("=" * 66)
    print(" 测试 2：全是同一类别（结果应该和任务 4 完全一样）")
    print("=" * 66)
    boxes2 = np.array([[0, 0, 10, 10],
                       [1, 1, 11, 11],
                       [5, 5, 15, 15],
                       [20, 20, 30, 30]], dtype=np.float32)
    scores2 = np.array([0.90, 0.80, 0.70, 0.60], dtype=np.float32)
    cls2 = np.array([0, 0, 0, 0])

    print("  按类别 (nms) →", nms(boxes2, scores2, cls2, 0.45), "   期望 [0 2 3]")
    print("  阈值 0.80    →", nms(boxes2, scores2, cls2, 0.80), "   期望 [0 1 2 3]")
    print()
    print("  ↑ 和任务 4 的结果一致 = 你的新版本没改坏旧功能（回归测试）")

    print()
    print("=" * 66)
    print(" 测试 3：真实数据 —— 用 test1.jpg 那 3 个框验证")
    print("=" * 66)
    # 图里的 3 个框：person + 2 car，两两不重叠
    real_boxes = np.array([[560, 399, 604, 521],
                           [278, 416, 364, 489],
                           [252, 423, 291, 464]], dtype=np.float32)
    real_scores = np.array([0.9126, 0.7696, 0.6637], dtype=np.float32)
    real_cls = np.array([0, 2, 2])           # person, car, car

    print("  按类别 →", nms(real_boxes, real_scores, real_cls, 0.45),
          "   期望 [0 1 2]（三个都保留）")
