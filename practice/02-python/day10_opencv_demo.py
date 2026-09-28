# ============================================================
# Day 10 配套示例：OpenCV 读图 / 看结构 / 存图
# ============================================================
# 用法:
#     cd ~/projects/py-basics && source .venv/bin/activate
#     python3 day10_opencv_demo.py
#
# 需要: ~/datasets/images/ 里至少有一张 jpg/png
# 输出: ~/datasets/output/day10/  下的几张图（全程不弹窗口，WSL 里最省事）
#
# 讲解见: docs/06-OpenCV入门.md
# ============================================================

import glob
import os

import cv2

IMAGE_DIR = os.path.expanduser("~/datasets/images")
OUT_DIR = os.path.expanduser("~/datasets/output/day10")


def find_first_image():
    """在图片目录里找第一张图（不硬编码文件名，你换图也不用改代码）"""
    for pattern in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        files = sorted(glob.glob(os.path.join(IMAGE_DIR, pattern)))
        if files:
            return files[0]
    return None


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    path = find_first_image()
    if path is None:
        print(f"[错误] {IMAGE_DIR} 里没有图片，先放几张进去")
        print("       参考 docs/03-Python练习计划.md 的 Day 10「准备」")
        return
    print(f"用图: {path}")
    print()

    # ---------- 1. imread：读图 ----------
    # 默认读成 3 通道彩色，而且通道顺序是 BGR（不是 RGB！）
    img = cv2.imread(path)

    # 读失败不会抛异常，只会返回 None —— 必须自己判，否则下一行就 AttributeError
    if img is None:
        print("[错误] 读不出来：检查路径是否正确、文件是否损坏、路径里有没有中文")
        return

    # ---------- 2. 看清它的结构（这就是 Day 8-9 学的 ndarray）----------
    h, w, c = img.shape          # 顺序是：高、宽、通道
    print(f"shape  = {img.shape}   -> 高={h} 宽={w} 通道={c}")
    print(f"dtype  = {img.dtype}   -> 每个像素是 0~255 的整数")
    print(f"元素数 = {img.size:,}  = 高 x 宽 x 通道 = {h} x {w} x {c}")
    print(f"内存   = {img.nbytes / 1024 / 1024:.2f} MB")
    print(f"尺寸打印: {w} x {h}      <- 注意是 宽 x 高，和 shape 的顺序相反")
    print()

    # ---------- 3. 取一个像素：img[y, x]，先 y 后 x ----------
    y, x = h // 2, w // 2
    pixel = img[y, x]
    print(f"正中间像素 img[{y}, {x}] = {pixel}   <- 先 y 后 x")
    b, g, r = pixel
    print(f"  拆开是 B={b} G={g} R={r}   <- OpenCV 是 BGR，不是 RGB")
    print()

    # ---------- 4. 切片 = 裁剪（Day 11 的裁剪就靠它）----------
    # 语法是 img[y1:y2, x1:x2]，先纵后横
    crop = img[h // 4: h // 4 * 3, w // 4: w // 4 * 3].copy()
    ok = cv2.imwrite(os.path.join(OUT_DIR, "01_crop.jpg"), crop)
    print(f"裁剪中心区域: {crop.shape}  ->  01_crop.jpg (写入{'成功' if ok else '失败'})")

    # ---------- 5. BGR -> RGB：要出 OpenCV 圈子时必须转 ----------
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    print(f"转成 RGB 后 img[0,0]: {img[0, 0]} -> {rgb[0, 0]}   <- 0 号和 2 号通道换了个位置")
    print()

    # ---------- 6. 灰度：shape 少一维 ----------
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f"灰度图 shape = {gray.shape}   <- 没有通道这一维了（是二维数组）")
    cv2.imwrite(os.path.join(OUT_DIR, "02_gray.jpg"), gray)

    # ---------- 7. resize：dsize 是 (宽, 高)，和 shape 相反 ----------
    scale = 640 / w
    new_w, new_h = 640, int(h * scale)
    small = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    print(f"缩放到宽 640: {img.shape} -> {small.shape}")
    print(f"  dsize 传的是 (宽, 高) = ({new_w}, {new_h})，缩小用 INTER_AREA 最干净")
    cv2.imwrite(os.path.join(OUT_DIR, "03_resize640.jpg"), small)
    print()

    # ---------- 8. 改像素 / 改通道：numpy 是引用语义，改副本要 copy ----------
    img_copy = img.copy()
    img_copy[:, :, 0] = 0        # 0 号通道是 B（蓝），全部清零 = 去掉蓝色
    cv2.imwrite(os.path.join(OUT_DIR, "04_no_blue.jpg"), img_copy)
    print("把蓝色通道清零 -> 04_no_blue.jpg（打开看：整张图会偏黄/偏暖）")

    # 也可以只点一个红点，验证你真的搞懂了 [y, x] 和 BGR
    dot = img.copy()
    dot[h // 2, w // 2] = [0, 0, 255]     # BGR 里的 [0,0,255] 是纯红
    cv2.imwrite(os.path.join(OUT_DIR, "05_red_dot.jpg"), dot)
    print(f"在中心 ({x}, {y}) 点了一个红点 -> 05_red_dot.jpg")
    print()

    # ---------- 9. imwrite 的返回值和 JPEG 质量 ----------
    ok = cv2.imwrite(os.path.join(OUT_DIR, "06_quality90.jpg"), img,
                     [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"imwrite 返回 {ok}   <- 一定要看：写失败它不报错，只返回 False，")
    print("                       最常见的原因是输出目录不存在")
    print()

    # ---------- 10.（可选）弹窗看图 ----------
    # WSL 里要 WSLg（Win11 / Win10 22H2+）或 X server 才能弹窗。
    # 判断方法: echo $DISPLAY   有输出才可能弹出来。
    # 弹不出来别折腾，直接去 Windows 里双击 ~/datasets/output/day10/ 下的图看。
    #
    # cv2.imshow("preview", small)
    # cv2.waitKey(0)            # 不调用它，窗口不刷新、程序还会卡住
    # cv2.destroyAllWindows()

    print(f"完成，输出目录: {OUT_DIR}")
    print("去 Windows 里打开对比：原图 / 裁剪 / 灰度 / 宽640 / 无蓝 / 红点")


if __name__ == "__main__":
    main()
