# OpenCV 入门（Day 10–11 配套）

> **一句话**：OpenCV 就是"图像的 NumPy"——图读进来就是一个数组，你在 Day 8–9 学的切片、`dtype`、`shape`、广播，到这里全能直接用。
>
> 所以真正的新东西不多，**难的是几个反直觉的约定**（先高后宽、先 y 后 x、BGR）。这篇把约定和坑讲透。

---

## 1. OpenCV 是什么，在你的项目里占什么位置

**OpenCV（Open Source Computer Vision Library）** 是计算机视觉的"标准库"：读写图片/视频、缩放裁剪、颜色转换、画图写字、边缘/轮廓/模板匹配、透视变换，还能直接加载 ONNX 之类的模型跑推理。

它是 C++ 写的，Python 里 `cv2` 只是薄薄一层壳——所以速度接近 C（不是"Python 慢"那种慢）。

在你这个车牌识别项目里，它负责**除模型之外的所有环节**：

| 环节 | 用到的 OpenCV 能力 | 什么时候 |
|---|---|---|
| 读摄像头帧 | `cv2.VideoCapture(0)` | 第 8 周 |
| 预处理 | `resize` / `cvtColor` / 归一化 | 全程 |
| 画结果 | `rectangle` / `putText` | 第 5 周起（画车牌框） |
| 车牌矫正 | 灰度、二值化、`findContours`、`warpPerspective` | 识别字符前（把歪的车牌摆正） |
| 保存/回放 | `imwrite` / `VideoWriter` | 调试、留证据 |

**Day 10 学的 5 个函数（`imread` / `imwrite` / `imshow` / `resize` / `cvtColor`）就是全部地基**，后面所有花活都是它们的组合。

---

## 2. 核心心智模型：一张图 = 一个 ndarray

```python
import cv2
img = cv2.imread("img0.jpg")

img.shape        # (480, 640, 3)   ← (高, 宽, 通道)
img.dtype        # dtype('uint8')  ← 每个值 0~255 的整数
img[y, x]        # 第 y 行、第 x 列那个像素 → [B, G, R]
img[100, 200]    # 高 100、宽 200 处的像素
```

用你熟的语言类比，它就是一个

```c
uint8_t buf[480][640][3];   // 行优先：buf[y][x][c]
```

三个必须刻进肌肉记忆的点：

1. **`shape` 是"先高后宽"**：`img.shape[0]` 是高，`img.shape[1]` 是宽。你 Day 10 要打印的 `尺寸 W x H` 得写成 `img.shape[1] x img.shape[0]`。
2. **取像素要写 `img[y, x]`**：先 y（行/高）后 x（列/宽）。写成 `img[x, y]` 不会报错——只会悄悄给你错位置的颜色，这是最难查的一类 bug。
3. **通道顺序是 BGR，不是 RGB**（下面第 3.5 节细说）。

顺手记住这几个和 NumPy 一模一样的操作：

```python
img.size                 # 总元素数 = 高 × 宽 × 通道
img.nbytes               # 占多少字节（480×640×3 = 921600 ≈ 0.88 MB）
img[y, x] = [255, 255, 255]        # 把这个像素改白
img[:, :, 0] = 0                   # 把蓝色通道整列清零（0 号通道是 B）
crop = img[100:300, 200:400]       # 切片 = 裁剪！这就是 Day 11 要做的
```

> ⚠️ `crop = img[100:300, 200:400]` 得到的是**视图**，改 `crop` 会改到原图。要独立副本就 `img[100:300, 200:400].copy()`。

---

## 3. 五个函数逐个讲

### 3.1 `cv2.imread(path, flag)` —— 读图

```python
img = cv2.imread("a.jpg")                  # 默认：3 通道彩色（BGR）
gray = cv2.imread("a.jpg", cv2.IMREAD_GRAYSCALE)   # 直接读成单通道灰度
raw  = cv2.imread("a.jpg", cv2.IMREAD_UNCHANGED)   # 原样读（PNG 带 alpha 时保留第 4 通道）
```

| flag | 数字 | 结果 |
|---|---|---|
| `IMREAD_COLOR`（默认） | 1 | 3 通道 BGR，**即使原图是灰度也会补成 3 通道** |
| `IMREAD_GRAYSCALE` | 0 | 单通道，`shape` 变成 `(H, W)` |
| `IMREAD_UNCHANGED` | -1 | 原样，含 alpha 通道时是 4 通道 |

**最重要的特性：读失败不抛异常，只返回 `None`。**

于是 `img.shape` 会报 `AttributeError: 'NoneType' object has no attribute 'shape'`——这个报错 90% 的人第一次都见过。所以**养成第一行判空**的习惯：

```python
img = cv2.imread(path)
if img is None:
    print(f"读不出来: {path}")
    return          # 或 continue（批量处理时）
```

`imread` 返回 `None` 的四个常见原因：

1. **路径不存在或拼错**（相对路径是相对"当前工作目录"，不是相对脚本文件！）
2. **路径里有中文/空格**（某些构建的 OpenCV 对非 ASCII 路径支持不好；Linux 上尤其常见）
3. 文件其实是坏的 / 后缀名骗人（把 `.txt` 改名成 `.jpg`）
4. 权限不足

排查三板斧：`ls -l 路径`、`pwd`（确认当前目录）、把图片拷成纯英文名再试。

### 3.2 `cv2.imwrite(path, img)` —— 存图

```python
ok = cv2.imwrite("out.jpg", img)                       # 返回 True/False
cv2.imwrite("out.jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])   # JPEG 质量 0~100，默认 95
```

**一定要看返回值**：写失败（目录不存在、路径非法）它也不抛异常，只返回 `False`，你可能半天后才发现文件根本没生成。

写不出中文路径时的兜底写法：

```python
ok, buf = cv2.imencode(".jpg", img)     # 编码进内存
if ok:
    buf.tofile("输出.jpg")              # 用 NumPy 的 tofile 绕过路径问题
```

> 小知识：JPEG 质量 90 和 95 肉眼看不出差别，文件小 30%。批量处理存中间结果时用 90 就够。

### 3.3 `cv2.imshow` / `waitKey` / `destroyAllWindows` —— 弹窗看图

```python
cv2.imshow("窗口标题", img)
cv2.waitKey(0)              # 等按键，0 = 一直等；写 1 就是等 1 毫秒（做视频时用）
cv2.destroyAllWindows()
```

- **`waitKey()` 不调用，窗口不会刷新内容，程序还会一直卡着**——这是新手最常见的"程序好像死了"。
- 窗口标题用英文，中文标题在某些平台会乱码。

**你在 WSL 里的特别注意**：`imshow` 需要图形界面。

```bash
echo $DISPLAY      # 有输出（通常 :0）才可能弹窗
```

- Windows 11 或 Win10 22H2 以上的 WSL2 一般自带 **WSLg**，能弹窗；
- 老版本 WSL 弹不出来，不必折腾 X server：**改成 `imwrite` 存文件，然后在 Windows 里用图片查看器打开**（输出目录用 `/mnt/d/...` 就能直接双击看）。调试图像时这个办法其实更舒服。

### 3.4 `cv2.resize(img, dsize)` —— 缩放

```python
new_w, new_h = 640, int(h * 640 / w)          # 保持宽高比
small = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
```

**最大的坑：`dsize` 是 `(宽, 高)`，和 `shape` 的顺序正好相反。**

```python
img.shape                       # (480, 640, 3) → 高 480、宽 640
cv2.resize(img, (640, 480))     # 传的是 (宽 640, 高 480) —— 同一个尺寸
```

搞反了不会报错，只会得到一张比例奇怪、甚至被拧成麻花的图。

插值方式怎么选：

| 场景 | 用哪个 | 原因 |
|---|---|---|
| **缩小** | `INTER_AREA` | 按区域平均，缩略图最干净，不会出现摩尔纹 |
| 放大 | `INTER_LINEAR`（默认）/ `INTER_CUBIC` | 平滑 |
| 最近邻 | `INTER_NEAREST` | 最快，但锯齿明显；标签图/掩码才用它 |

保持宽高比的两种写法：

```python
# ① 指定宽（最常用：宽度对齐模型输入）
scale = 640 / img.shape[1]
small = cv2.resize(img, (640, int(img.shape[0] * scale)))

# ② 按比例缩放
small = cv2.resize(img, None, fx=0.5, fy=0.5)    # 宽高都乘 0.5，dsize 传 None
```

### 3.5 `cv2.cvtColor(img, code)` —— 颜色空间转换

```python
rgb  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)     # 给 matplotlib / PIL / 模型用
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)    # 灰度，shape 变成 (H, W)
hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)     # 后面按颜色找车牌底色时有用
```

**为什么 OpenCV 用 BGR？** 历史原因：早期为了兼容 BMP 格式和某些相机的原始输出顺序。这个决定在 2000 年做的，现在改不动了（会破坏全世界几十亿行代码），所以只能记住。

**什么时候会被它坑？**

| 场景 | 症状 |
|---|---|
| `plt.imshow(img)` 显示 | 人脸发蓝、天空发红——红蓝通道被颠倒了 |
| 把图喂给 PyTorch/ONNX/RKNN | 通道顺序不对，精度悄悄掉，不报错 |
| 从 PIL 读图再 OpenCV 处理 | 一个 RGB 一个 BGR，混着用必错 |

**规矩：进了 OpenCV 世界就按 BGR 思考；一旦要出这个圈子（显示、喂模型），显式转一次。** 别靠记忆猜。

灰度公式（加权，不是简单平均——人眼对绿色更敏感）：

```
Gray = 0.299·R + 0.587·G + 0.114·B
```

---

## 4. 五个最常见的坑（背下来能省你几小时）

| # | 坑 | 症状 | 正确写法 |
|---|---|---|---|
| 1 | `shape` 记成 (宽,高) | 尺寸打印反了、报错位置诡异 | `高=shape[0]`、`宽=shape[1]` |
| 2 | 取像素写 `img[x, y]` | 不报错，颜色/位置全错 | `img[y, x]`（先 y 后 x） |
| 3 | `resize` 传 `(高, 宽)` | 图被拉变形 | `dsize` 是 `(宽, 高)` |
| 4 | 忘了 `.copy()` 就改切片 | 原图莫名被改 | 需要独立副本时 `.copy()` |
| 5 | 不判 `img is None` | `AttributeError: 'NoneType' ...` | 读图后立刻判空 |

再补两个：

6. **相对路径的基准是"当前工作目录"**，不是脚本所在目录 → 用 `os.path.expanduser("~/datasets/images")` 拼绝对路径最稳。
7. **不要用 `img.shape` 之外的方式猜通道数**：灰度图是 2 维，直接写 `h, w, c = img.shape` 会崩。稳妥写法：

```python
h, w = img.shape[:2]
c = 1 if img.ndim == 2 else img.shape[2]
```

---

## 5. 跑一遍：配套示例脚本

示例脚本在 `practice/02-python/day10_opencv_demo.py`，把 Day 10 的每个知识点都跑一遍并存成图，**全程不弹窗口**（WSL 里最省事）：

```bash
cd ~/projects/py-basics && source .venv/bin/activate
python3 day10_opencv_demo.py
```

它会在 `~/datasets/output/day10/` 下生成 `01_crop.jpg`、`02_gray.jpg`、`03_resize640.jpg`、`04_no_blue.jpg`、`05_quality90.jpg`，留着和原图对比着看。

**预期输出大概长这样**（数字随图片不同）：

```
用图: /home/user/datasets/images/img0.jpg
shape  = (1200, 1920, 3)   -> 高=1200 宽=1920 通道=3
dtype  = uint8   -> 每个像素 0~255 的整数
元素数 = 6,912,000  = 高×宽×通道
内存   = 6.59 MB
正中间像素 img[600, 960] = [.. .. ..]   <- 先 y 后 x
...
```

**如果报 `[错误] 读不出来`**：先 `ls ~/datasets/images/` 确认有图，再看路径有没有中文。

---

## 6. Day 10 作业（自己写，别看示例抄）

`docs/03-Python练习计划.md` 里 Day 10 的要求就是这几行，自己敲一遍：

```python
import cv2
img = cv2.imread("路径/图.jpg")
print("形状:", img.shape)      # 注意是 (高, 宽, 通道)
print("尺寸: {} x {}".format(img.shape[1], img.shape[0]))
cv2.imwrite("output.jpg", img)
```

**加分项**（做了才算真懂）：

1. 用同一张图，分别以彩色 / 灰度 / 原样三种 flag 读进来，打印三个 `shape`，解释为什么不同
2. 打印图片正中心那个像素的 B/G/R 三个值，然后把那个像素改成纯红 `[0, 0, 255]` 存图——在 Windows 里打开看是不是真的变成红点（**这题最能验证你有没有搞懂 BGR 和 [y,x]**）
3. 把图缩到宽 320，存下来，比较文件大小和原图的差别

---

## 7. 往后看：这些知识马上会用到

| 天数 | 用到什么 |
|---|---|
| **Day 11** | `resize` + 切片裁剪 + `rectangle` / `putText` / `circle` 画框写字——**这就是画车牌框的雏形** |
| **Day 12** | `glob` 遍历 `~/datasets/images/` + 上面全部，批量处理并存到 `~/datasets/output/` |
| **Day 13–14** | 加上 `try/except` 和 `img is None` 判断，做到"坏图不崩、最后统计成败" |
| 第 5 周 | YOLO 检测出车牌框后，用 `img[y1:y2, x1:x2].copy()` 把车牌裁出来交给识别模型 |
| 第 8 周 | `cv2.VideoCapture` 读摄像头，一帧一帧重复上面全过程 |

> 一句话记住 OpenCV 的学习方式：**参数别背，写错一次就记住了。** 但上面那张"坑表"里的 5 条，值得直接背下来——它们不报错，只给你错结果。

---

## 8. 报错速查（见到这些别慌）

| 报错 | 真正原因 | 怎么修 |
|---|---|---|
| `findDecoder imread_('1.png'): can't open/read file: check file path/integrity` | **文件没找到**，不是"图坏了"。相对路径的基准是**当前工作目录**，不是脚本所在目录 | `pwd` 看你在哪、`ls ~/datasets/images` 看图在哪，然后写绝对路径 |
| `cv2.error: ... (-215:Assertion failed) size.width>0 && size.height>0 in function 'imshow'` | 你给 `imshow` 传了 `None` —— 几乎总是**上一行 `imread` 已经失败了** | 先修 `imread`；中间加 `if img is None`，让报错落在真正出问题的那一行 |
| `AttributeError: 'NoneType' object has no attribute 'shape'` | 同上，还是 `imread` 返回了 `None` | 同上 |
| `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` / `cannot connect to X server` | 当前环境没有图形界面（WSL 里没开 WSLg） | `echo $DISPLAY` 确认；改用 `imwrite` 存盘后在 Windows 里看 |
| 中文路径读图失败（不报错，只是 None） | 某些构建对非 ASCII 路径支持不好 | 图片改英文名，或写图时用 `imencode` + `tofile` 兜底 |

**通用原则**：OpenCV 的报错**最后一行**才是原因，前面那些 `WARN` 只是提示。像 `imshow` 这种"接盘侠"，它报的错基本都不是它自己的问题——**报错行往往不是出错行，往前找一行**。

Day 10 最稳的写法模板（路径 + 判空一次到位）：

```python
import os
import sys

import cv2

path = os.path.expanduser("~/datasets/images/img0.jpg")   # 绝对路径，别用 "1.png"
img = cv2.imread(path)
if img is None:
    sys.exit(f"读不出来: {path}（路径不存在 / 含中文 / 文件损坏）")

print("shape:", img.shape)
```

### 关于 `imshow`：WSL 里为什么弹不出窗口

报错长这样：

```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" ...
This application failed to start because no Qt platform plugin could be initialized.
Available platform plugins are: xcb.
Aborted
```

**先记住结论：这不是你的代码错，也不是 OpenCV 装坏了，是这台 WSL 根本没有图形界面。**

`imshow` 要靠窗口系统把图画出来（Linux 上走 X11，OpenCV 用的是 Qt 的 `xcb` 插件）。它"找到了插件文件但初始化不了"，因为**没有 X 显示服务器可以连**（或缺少 `libxcb` 系列系统库）。Qt 出这种错会直接 `abort()` 杀进程，所以你看到的是 `Aborted` 而不是 Python 的 traceback。

三步确认：

```bash
echo $DISPLAY                                   # 空 = 没有显示服务器，装什么库都没用
ls /mnt/wslg 2>/dev/null                        # 有内容 = 这台 WSL 带 WSLg（Win11 / Win10 22H2+）
ls /tmp/.X11-unix 2>/dev/null                   # 有 X0 = 有 X server 在跑
ldd .venv/lib/python3*/site-packages/cv2/qt/plugins/platforms/libqxcb.so | grep "not found"
                                                # 缺哪些系统库，这里会列出来
```

三条出路，**推荐第 1 条**：

1. **不用 `imshow`，改成存文件**——这也是本教程 Day 10–14 的标准做法（调试图像时在 Windows 里看更舒服）：

```python
out = os.path.expanduser("~/datasets/output/day10_out.jpg")
print("存成功?", cv2.imwrite(out, img))

# 只有真的有图形界面时才弹窗，没有就跳过（这样代码在板子上也能跑）
if os.environ.get("DISPLAY"):
    cv2.imshow("window", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("没有图形界面，跳过 imshow，去看:", out)
```

2. **确认有 `DISPLAY` 之后再补库**（只在"有 X server 但缺库"时才有用）：

```bash
sudo apt install -y libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0
```

3. **开 WSLg**（需要 Windows 11 或 Win10 22H2 以上）：在 Windows PowerShell 里 `wsl --update`，然后 `wsl --shutdown` 重开。老版本 Windows 想弹窗得自己搭 VcXsrv 之类——**为这个项目不值得折腾**。

> **给板子写代码时就按第 1 条写。** RK3588 上跑推理时通常是无桌面环境，程序里到处 `imshow` 到了板子上全会崩。

---

## 9. 最小闭环逐行拆解（你 Day 10 跑通的那 7 行）

```python
import glob
import os

import cv2

src = sorted(glob.glob(os.path.expanduser("~/datasets/images/*.jpg")))[0]
img = cv2.imread(src)
print("形状:", img.shape)

dst = os.path.expanduser("~/datasets/output/day10_test.jpg")
print("成功?", cv2.imwrite(dst, img))
```

这一条链就是图像处理的全部套路：**找文件 → 读成数组 → 看结构 → 写回磁盘**。

| 代码 | 干了什么 | 关键点（容易糊涂的地方） |
|---|---|---|
| `os.path.expanduser("~/...")` | 把 `~` 换成 `/home/user` | **Python 不认 `~`**！`~` 是 shell 的写法。直接写 `cv2.imread("~/a.jpg")`，它会去找一个名字叫 `~` 的目录，然后返回 `None`。路径里带 `~`，一律先 `expanduser` |
| `glob.glob(".../*.jpg")` | 拿通配符去问文件系统："有哪些文件匹配？"，返回**字符串列表** | `*` 可以匹配任意字符；没匹配到返回**空列表 `[]`**（不报错） |
| `sorted(...)` | 给列表排序 | 不排的话顺序由文件系统决定（ext4 是哈希序），"第一张"每次跑可能都不一样 |
| `[0]` | 取出第一个路径（一个字符串） | **空列表上取 `[0]` 会 `IndexError: list index out of range`**，这就是"目录里没有匹配文件"的样子 |
| `cv2.imread(src)` | 解码 JPEG → NumPy 数组；默认彩色 BGR | 失败只返回 `None`，不抛异常 |
| `img.shape` | `(高, 宽, 通道)`，例如 `(1200, 1920, 3)` | 打印"尺寸"要写 `shape[1] x shape[0]`（宽 x 高） |
| `cv2.imwrite(dst, img)` | 按**后缀名**决定格式（`.jpg`→JPEG、`.png`→PNG），编码写盘 | ① **它不会自动创建目录**，目录不存在就返回 `False`；② 返回值要看；③ JPEG 是**有损**压缩，存出来的和读进来的不完全一样，要无损就存 `.png` |

要"一成不变"的稳妥版（多加两行判断，报错就一目了然）：

```python
files = sorted(glob.glob(os.path.expanduser("~/datasets/images/*.jpg")))
if not files:
    sys.exit("这个目录里没有匹配 *.jpg 的文件")

img = cv2.imread(files[0])
if img is None:
    sys.exit(f"读不出来: {files[0]}")

print(f"共 {len(files)} 张，这次用 {files[0]}，shape={img.shape}")
```

**三个"改一下看结果"的实验**（做一遍胜过读十遍）：

1. 把 `*.jpg` 改成 `*.png` → `[0]` 立刻抛 `IndexError`（因为目录里没有 png）——这就是"空列表"的后果
2. 把 `[0]` 改成 `[5]`、`[-1]` → 换成别的图（`-1` 是最后一张，Python 的负索引）
3. 把输出后缀改成 `.png` → 文件变大但无损；再把 `[0]` 那行的 `sorted` 去掉多跑几次，体会"顺序会乱"

---

## 10. Day 11：缩放、裁剪、画框（先说最容易混的一点）

### 路径（字符串）和图像（数组）是两种东西

| | 长什么样 | 谁能吃它 |
|---|---|---|
| **路径** | `"/home/user/datasets/images/img0.jpg"` 一串字符 | `cv2.imread(路径)`、`cv2.imwrite(路径, 图)` |
| **图像** | `imread` 返回的那个 NumPy 数组 | `cv2.resize(图, ...)`、`cv2.cvtColor(图, ...)`、切片、`imwrite` 的**第二个**参数 |

搞反了就是这两种报错：

- 给 `resize` 传路径字符串 → `TypeError: Expected Ptr<cv::UMat> for argument 'src'`
- 给 `imread` 传数组 → 同样报类型错（它只要文件名）

**口诀：`imread` / `imwrite` 这一对是"进出文件"的，认路径；中间所有处理函数是"处理图像"的，认数组。**

```python
path  = sorted(glob.glob(os.path.expanduser("~/datasets/images/*.jpg")))[0]   # 路径（字符串）
img   = cv2.imread(path)                                                     # 读 → 数组
if img is None:
    sys.exit("读不出来")
small = cv2.resize(img, (640, 480))                                          # 数组 → 数组
cv2.imwrite(os.path.expanduser("~/datasets/output/small.jpg"), small)        # 数组 → 文件
```

### 两种函数风格（Day 11 最容易踩的第二个点）

| 风格 | 代表函数 | 怎么用 |
|---|---|---|
| **返回新数组**，原图不动 | `resize`、`cvtColor`、切片 | `new = cv2.resize(img, ...)` |
| **原地修改**，返回 `None` | `rectangle`、`putText`、`circle`、`line` | `cv2.rectangle(img, ...)` ← 画完 `img` 自己就变了 |

所以想保留干净的原图，先 `img.copy()` 再画。

### resize：`dsize` 是 (宽, 高)

```python
small = cv2.resize(img, (640, 480), interpolation=cv2.INTER_AREA)   # 得到 shape (480, 640, 3)
```

- 强制 `(640, 480)` 会**改变宽高比**（图被拉伸变形）。要保持比例：

```python
w = 640
h = int(img.shape[0] * w / img.shape[1])
small = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
```

- 缩小用 `INTER_AREA`，放大用 `INTER_LINEAR`（默认）

### 裁剪：切片就是裁剪

```python
h, w = img.shape[:2]
crop = img[h // 4: h // 4 * 3, w // 4: w // 4 * 3].copy()     # [y1:y2, x1:x2]，先纵后横
```

### 画框 + 写字

```python
cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)          # 左上角、右下角、颜色、线宽
cv2.putText(img, "plate", (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)       # 文字、左下角坐标、字体、字号、颜色、线宽
```

四个必须记住的细节：

1. **颜色是 BGR 顺序**：`(0,255,0)` 绿、`(0,0,255)` 红、`(255,0,0)` 蓝
2. **坐标必须是整数**（Python 的 float 会报错），比例算出来记得 `int()`
3. **`putText` 的坐标是文字的"左下角"**，所以写 `y1 - 10` 才会落在框的上方
4. **`putText` 不支持中文**（HERSHEY 字体），中文会渲染成 `????`；要写中文得换 PIL

> 在缩放到 640 宽的图上画框时，坐标要按**缩放后**的尺寸算——先 resize 再按新尺寸画，或按比例换算。

---

## 11. Day 12：批量处理（进度打印 + 五个坑）

批处理的骨架就三件事：**遍历目录 → 逐个处理 → 打印进度**。坑全在后面两件事上。

### 坑 1：`for ... else` 不是"没进循环才执行"

```python
for f in files:
    ...
else:
    print("没有找到任何图像文件。")     # ← 处理了 20 张，这句话照样打印
```

Python 里 `for...else` 的 `else` 含义是**"循环正常跑完（中途没有被 `break` 打断）"**，**不是**"循环一次都没进"。
所以它一定会在循环结束后执行——看起来就像"最后该出现的信息被顶掉了"。

要判断"目录里没有文件"，正确做法是**在循环之前**判：

```python
if not files:
    sys.exit(f"{input_dir} 里没有匹配的文件")
```

### 坑 2：进度条 off-by-one（永远到不了 `[20/20]`）

```python
total = len(files)              # 20
for f in files:
    ...
    total -= 1                  # ← 同一个变量既当"总数"又当"倒计时"
    print(f"[{len(files) - total}/{len(files)}]")
```

| 第几张 | 上面的写法打印 | 想要的 |
|---|---|---|
| 第 1 张 | `[0/20]` | `[1/20]` |
| 第 2 张 | `[1/20]` | `[2/20]` |
| … | … | … |
| 第 20 张 | `[19/20]` | `[20/20]` |

进度是在"减 1 之后"算的，所以最大值只能到 `总数 - 1`。

**清晰写法：把"总数"和"当前第几张"分成两个变量**，`enumerate` 一次到位：

```python
total = len(files)
for i, path in enumerate(files, start=1):
    print(f"[{i}/{total}] 处理中: {os.path.basename(path)}")
```

> 一条经验：**"总数"是常量，别拿它当计数器用。** 一个变量身兼两职，早晚算错。

### 坑 3：绘制函数到底要不要接返回值？用一行验证

```bash
python3 -c "
import cv2, numpy as np
img = np.zeros((50, 50, 3), np.uint8)
print('putText   返回:', type(cv2.putText(img, 'x', (5, 20), 0, 0.5, (0, 255, 0), 1)))
print('rectangle 返回:', type(cv2.rectangle(img, (0, 0, 5, 5), (0, 255, 0), 1)))
"
```

- 打印 `NoneType` → **千万别写** `img = cv2.rectangle(img, ...)`：`img` 会变成 `None`，下一行用到它就崩（见[这个 Stack Overflow 问题](https://stackoverflow.com/questions/20452204/why-does-cv2-rectangle-return-none-instead-of-an-image)）
- 打印 `ndarray` → 你这份版本会返回图像本身，赋值无害

**结论：不管哪种情况，都单独一行写，不赋值。** `cv2.rectangle(img, ...)` —— 这样在任何版本上都对。

### 坑 4：`thickness = -1` 是"实心填充"

```python
cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), -1)   # 把中心涂成实心蓝色，图被盖住
cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)    # 空心框、线宽 2 —— 画车牌框用这个
```

`-1` 表示填充内部。调试、画车牌框都用正的线宽。

### 坑 5：`putText` 起点太靠右，文字会被裁掉

图宽 640，文字起点 `x=500`，文件名稍长就超出右边界——**超出部分直接消失，不报错**。起点从小值开始（如 `(10, 30)`），或按 `img.shape[1]` 估一下宽度。

### Day 12 骨架（对照自己的代码改）

```python
files = sorted(glob.glob(os.path.join(input_dir, "*.jpg")))
if not files:
    sys.exit("没有找到任何图像文件")

total = len(files)
for i, path in enumerate(files, start=1):
    filename = os.path.basename(path)
    print(f"[{i}/{total}] 处理中: {filename}")

    img = cv2.imread(path)
    if img is None:                       # Day 13 的内容，提前加上更稳
        print(f"        [跳过] 读不出来: {filename}")
        continue

    img_small = cv2.resize(img, (640, 480), interpolation=cv2.INTER_AREA)
    cv2.rectangle(img_small, (x1, y1), (x2, y2), (255, 0, 0), 2)
    cv2.putText(img_small, filename, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    out_path = os.path.join(output_dir, "processed_" + filename)   # Day 12 要求加前缀
    if not cv2.imwrite(out_path, img_small):
        print(f"        [失败] 写不进去: {out_path}")
```

---

## 13. Day 13：错误处理（让批处理"崩不掉"）

### 先分清两类失败——这是这天的核心

| 类型 | 谁是这样 | 怎么处理 |
|---|---|---|
| **安静的失败**：不报错，只返回特殊值 | `cv2.imread` 读不出来 → 返回 `None`；`cv2.imwrite` 写不进去 → 返回 `False` | **只能用 `if` 判断** |
| **抛异常**：程序直接中断 | `cv2.resize(None)`、坐标传了 float、文件不存在、没权限、磁盘满 | **`try / except`** |

**关键认知：`try/except` 抓不住 `None` 和 `False`。** 很多人以为包上 try 就万事大吉，结果"读不出来的图"照样让程序崩——因为它在 `if` 那一关，不在异常那一关。**两道防线都要有。**

### 骨架：把"安静的失败"主动变成异常，统一处理

```python
ok_list, fail_list = [], []

for i, path in enumerate(files, start=1):
    name = os.path.basename(path)
    try:
        img = cv2.imread(path)
        if img is None:
            raise ValueError("imread 返回 None（文件损坏 / 不是图片）")     # ① 把安静失败升级成异常

        small = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
        cv2.rectangle(small, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(small, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        out_path = os.path.join(output_dir, "processed_" + name)
        if not cv2.imwrite(out_path, small):
            raise IOError(f"imwrite 返回 False: {out_path}")              # ② 同上

        ok_list.append(name)
        print(f"[{i}/{total}] OK   {name}")
    except Exception as e:                                                # ③ 写 Exception，别裸 except
        fail_list.append((name, f"{type(e).__name__}: {e}"))
        print(f"[{i}/{total}] 失败 {name} -> {type(e).__name__}: {e}")

print(f"\n成功 {len(ok_list)} 张，失败 {len(fail_list)} 张")
for name, reason in fail_list:
    print(f"  ✗ {name}: {reason}")
```

**这个"把 None/False 主动 `raise` 成异常"的技巧很有用**：两类失败最后都走同一个 `except`，统计和记录只写一遍。

### 不要写裸 `except:`

```python
except:                 # ❌ 连 Ctrl+C 都吞掉，还会把真正的 bug（变量名拼错等）藏起来
    pass                # ❌ 什么都不打印 = 自己给自己埋雷

except Exception as e:  # ✅ 并且一定要把 e 打印出来 / 记进失败列表
    ...
```

**"到底是什么错"和"有几张错了"同样重要。** 只统计数量不记原因，出了问题你还得再跑一遍。

### `finally` 什么时候用

`finally` 里的代码**不管成功失败都会执行**，用来收尾（关文件、删临时文件）。这个批处理脚本用不上；但 Day 14 要写 `report.txt` 时就有用了：

```python
f = open("report.txt", "w")
try:
    f.write(...)
finally:
    f.close()          # 中途抛异常也能保证关掉
```

### 怎么"测"错误处理？——自己造错误

别等错误自然发生，**主动造几张坏图**：

```bash
cd ~/datasets/images
echo "这不是图片" > broken.jpg                    # 假 jpg：imread 会返回 None
cp img0.jpg noperm.jpg && chmod 000 noperm.jpg    # 无权限：会抛 PermissionError

chmod 555 ~/datasets/output                       # 让 imwrite 失败（返回 False）
# 测完记得恢复：chmod 755 ~/datasets/output
```

**验收标准**：程序跑完**不崩**，最后统计出"成功 20 张，失败 2 张"，并列明各自的原因。

测完把造出来的假图删掉（`rm broken.jpg noperm.jpg`），否则它们会一直留在 `~/datasets/images/` 里影响 Day 14。

### 第二个任务：自己建一个虚拟环境

```bash
mkdir -p ~/projects/test-venv && cd ~/projects/test-venv
python3 -m venv .venv
source .venv/bin/activate
pip install opencv-python
python3 -c "import cv2; print(cv2.__version__)"
deactivate
```

为什么要专门练这个：**"每个项目一个独立环境"是纪律**。以后装 RKNN-Toolkit2 时你要建一个 `python3.10` 的环境（因为 3.14 装不上），现在先把"建环境 → 激活 → 装库 → 验证 → 退出"这套动作练熟。`pip` 会自动走你 setup 时配好的清华镜像，不用再配。
