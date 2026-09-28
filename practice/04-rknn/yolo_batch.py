# ============================================================
# 阶段① / Day 2-B：批量体检 —— 20 张图一起跑，看谁有"清晰检测"
# ============================================================
# 用法:
#   cd ~/projects/rknn
#   source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn
#   python3 yolo_batch.py            # 不要带参数
#
# 目的:
#   单张图看不出"是图的问题还是代码的问题"。批量跑完对比一下：
#     · 大部分图都是 0 个框      -> 图和模型不匹配（多半是合成图）
#     · 某几张图有高置信度框     -> 代码没问题，看那几张就行
#     · 所有图框都很多、位置很乱 -> 前后处理有问题
#
# 依赖 yolo_infer.py 里的函数（模块复用，不重复写一遍）
# ============================================================

import os
import glob

import numpy as np
import cv2
import onnxruntime as ort

from yolo_infer import (
    MODEL_PATH, ANCHORS, STRIDES, COCO_NAMES,
    letterbox, decode_scale, nms,
)


IMG_DIR = os.path.expanduser("~/datasets/images")
OUT_DIR = os.path.expanduser("~/datasets/output_detect")
SCAN_TH = 0.25          # 先宽松地全捞出来，再分级统计
IOU_TH = 0.45


def main():
    sess = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    in_name = sess.get_inputs()[0].name
    out_names = [o.name for o in sess.get_outputs()]

    files = []
    for e in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"):
        files += glob.glob(os.path.join(IMG_DIR, e))
    files = sorted(files)

    if not files:
        print(f"{IMG_DIR} 里没有图片")
        raise SystemExit(1)

    print(f"{IMG_DIR} 共 {len(files)} 张\n")
    print(f"{'文件':<22}{'尺寸':>11}{'@0.5':>7}{'@0.7':>7}   最高置信度 / 类别")
    print("-" * 80)

    rows = []
    for p in files:
        nm = os.path.basename(p)
        img = cv2.imread(p)
        if img is None:
            print(f"{nm:<22}{'读图失败':>11}")
            continue

        H, W = img.shape[:2]
        box, r, pl, pt, cw, ch = letterbox(img)
        blob = box[:, :, ::-1].astype(np.float32) / 255.0
        blob = np.ascontiguousarray(np.transpose(blob, (2, 0, 1))[None, ...])
        outs = sess.run(out_names, {in_name: blob})

        allb, alls, allc = [], [], []
        for i, out in enumerate(outs):
            b, s, c, _ = decode_scale(out, STRIDES[i], ANCHORS[i], SCAN_TH)
            if len(b):
                allb.append(b); alls.append(s); allc.append(c)

        if not allb:
            print(f"{nm:<22}{W:>5}x{H:<6}{0:>7}{0:>7}   -")
            rows.append((nm, 0, 0, "-", 0.0))
            continue

        b = np.concatenate(allb); s = np.concatenate(alls); c = np.concatenate(allc)
        cxx = (b[:, 0] + b[:, 2]) / 2
        cyy = (b[:, 1] + b[:, 3]) / 2
        bww = b[:, 2] - b[:, 0]
        bhh = b[:, 3] - b[:, 1]
        m = ((cxx >= pl) & (cxx <= pl + cw) &
             (cyy >= pt) & (cyy <= pt + ch) & (bww > 2) & (bhh > 2))
        b, s, c = b[m], s[m], c[m]
        k = nms(b, s, c, IOU_TH)
        b, s, c = b[k], s[k], c[k]

        n5 = int((s >= 0.5).sum())
        n7 = int((s >= 0.7).sum())
        top = f"{s.max():.3f} {COCO_NAMES[int(c[s.argmax()])]}" if len(s) else "-"
        print(f"{nm:<22}{W:>5}x{H:<6}{n5:>7}{n7:>7}   {top}")
        rows.append((nm, n5, n7, top, float(s.max()) if len(s) else 0.0))

        # 存标注图（只画 @0.5 以上，避免满屏绿框）
        os.makedirs(OUT_DIR, exist_ok=True)
        vis = img.copy()
        thick = max(2, W // 800)
        for i in range(len(b)):
            if s[i] < 0.5:
                continue
            x1 = int(np.clip((b[i][0] - pl) / r, 0, W - 1))
            y1 = int(np.clip((b[i][1] - pt) / r, 0, H - 1))
            x2 = int(np.clip((b[i][2] - pl) / r, 0, W - 1))
            y2 = int(np.clip((b[i][3] - pt) / r, 0, H - 1))
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), thick)
            lab = f"{COCO_NAMES[int(c[i])]} {s[i]:.2f}"
            cv2.putText(vis, lab, (x1 + 4, max(y1 - 8, 24)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        cv2.imwrite(os.path.join(OUT_DIR, "batch_" + nm), vis)

    print("-" * 80)
    rows.sort(key=lambda x: -x[4])
    print("\n按最高置信度排序（前 8）：")
    for nm, n5, n7, top, mx in rows[:8]:
        print(f"  {nm:<22} @0.5={n5:>3}  @0.7={n7:>3}   最高 {top}")

    print(f"\n标注图已存到 {OUT_DIR}/batch_*.jpg")
    print("看 Windows 里的文件夹：")
    print(f'  explorer.exe "$(wslpath -w {OUT_DIR})"')
    print("\n★ 把上面置信度最高的 1~2 张图（原图 + batch_ 标注图）拷给我看：")
    print('  mkdir -p "/mnt/d/嵌入式AI-车牌识别/practice/04-rknn/_debug"')
    print('  cp "<最高分那张原图>" "/mnt/d/嵌入式AI-车牌识别/practice/04-rknn/_debug/orig.jpg"')
    print(f'  cp "{OUT_DIR}/batch_<同名>" "/mnt/d/嵌入式AI-车牌识别/practice/04-rknn/_debug/detect.jpg"')


if __name__ == "__main__":
    main()
