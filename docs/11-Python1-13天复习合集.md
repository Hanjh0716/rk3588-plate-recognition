# Python Day 1–13 复习合集

> **这份文档怎么用**
>
> 它不是教程（教程在 `03-Python练习计划.md` / `04-NumPy入门.md` / `06-OpenCV入门.md` / `08-异常处理.md`），
> 它是**压缩包 + 自测卷**。三轮复习法：
>
> | 轮次 | 做什么 | 花多久 |
> |---|---|---|
> | **第 1 轮** | 通读 §一 §二，边读边在心里回答每节的「自测」 | 40 分钟 |
> | **第 2 轮** | 直接跳到 §五 做 20 道自测题，**遮住答案**；错的回 §二 查 | 30 分钟 |
> | **第 3 轮** | 只做 §六 的默写题 + 看 §四 速查卡 | 15 分钟 |
>
> **判断标准**：§六 能默写出来 = 这 13 天真的到手了。

---

## 一、先看全局：这 13 天其实只有一条主线

很多人复习时是"一天一天背"，结果记不住——因为**知识不是按天长的，是按数据流长的**。

把它们串起来，就是一句话：

```
    【数据从哪来】          【怎么处理】              【结果去哪】
                                                      
  input() 输入        →   变量装起来        →    print 打印
  文本文件读进来      →   列表/字典整理      →    写回文件
  图片读进来(ndarray) →   NumPy 整体运算     →    imwrite 存图
                       →   OpenCV 改图       →    画框/写字
                       →   循环批量处理      →    20 张一起出
                       →   try/except 兜底   →    崩不掉 + 有报告
```

**每一天的位置：**

| 天 | 关键词 | 一句话 | 在项目里对应什么 |
|---|---|---|---|
| **1** | 变量、类型 | 数据装进盒子 | 以后每个 `img`、`shape`、`path` 都是变量 |
| **2** | 条件 | 程序会做选择 | 置信度阈值判断、分数合法性 |
| **3** | 循环 | 重复劳动交给机器 | 遍历目录下所有图片 |
| **4** | 列表 | 一次拿一堆数据 | 文件名列表、成功/失败列表 |
| **5** | 字典、字符串 | 键找值 + 字符串加工 | 路径拼接、词频统计、筛文件名 |
| **6** | 函数 | 把一段逻辑打包 | 以后每个处理步骤都是一个函数 |
| **7** | 文件读写 | 数据落盘 | `report.txt`、**`dataset.txt`（量化必需）** |
| **8** | NumPy 基础 | 图 = 多维数组 | **一切的底层表示** |
| **9** | NumPy 运算 | 别写 for 循环 | 归一化、二值化、按置信度筛选 |
| **10** | OpenCV 读写 | 图进内存 / 存出去 | 项目的入口和出口 |
| **11** | 缩放裁剪画框 | 改图 | **画车牌框的雏形** |
| **12** | 批量处理 | 把前面全用上 | 数据集预处理 |
| **13** | 异常处理 | 让程序崩不掉 | 处理脏数据（真实数据集必备） |

**一句话总结**：Day 1–7 学的是"怎么指挥计算机"，Day 8–13 学的是"怎么指挥计算机处理图像"。

---

## 二、逐天速查

> 每天三块：**代码卡**（能直接跑）/ **必记**（一句话）/ **坑**（踩过的）

### Day 1 — 变量、输入输出、类型

```python
name = "张三"                          # 赋值 = 把右边的值装进左边的名字
age  = int(input("年龄: "))             # input 返回的永远是字符串！
print(f"{name}，你出生于 {2025 - age} 年")   # f-string：{} 里能写任意表达式
print(f"平均分 {avg:.2f}")              # :.2f = 保留 2 位小数
type(name)                             # <class 'str'>
```

**必记**：`input()` 返回值**永远是 `str`**。想算数必须先 `int()` / `float()`。

**坑**：`input("年龄") + 1` → `TypeError`（字符串不能加数字）
**自测**：为什么 `"18" + 1` 报错，而 `int("18") + 1` 不报错？

---

### Day 2 — 条件判断

```python
if score > 100 or score < 0:        # ① 先处理"不合法"
    print("分数不合法")
elif score >= 90:                   # ② 再从上往下匹配
    grade = "A"
elif score >= 80:
    grade = "B"
else:                               # ③ 兜底
    grade = "F"
```

**必记**：`elif` **从上往下匹配，第一个成立的进去后就跳出**。所以 `>=90` 必须写在 `>=80` 前面。

**坑 1**：`if score > 100 or < 0:` ✗ —— 每个条件都要写完整的比较表达式（`or score < 0`）
**坑 2**：`if 90 <= score < 80:` 语法合法但**永远为 False**（这是链式比较，等于 `90<=score and score<80`）
**自测**：输入 95，为什么写在后面的 `elif score >= 80` 不会被触发？

---

### Day 3 — 循环

```python
# ① for：知道要跑多少次 / 要遍历一堆东西
for i in range(1, 101):             # 1..100，range 右端"不含"
    if i % 7 == 0:
        print(i)

# ② 嵌套循环：外层跑 1 次，内层跑完一整轮
for i in range(1, 10):
    for j in range(1, i + 1):
        print(f"{j}×{i}={i*j}", end="\t")
    print()

# ③ while：知道什么时候停，但不知道要跑几次
while True:
    guess = int(input("猜: "))
    if guess == target:
        break                       # 跳出整个循环
    print("大了" if guess > target else "小了")
```

**必记**：
- `range(5)` → 0,1,2,3,4；`range(1, 101)` → 1…100（**不含右端**）
- `break` = 跳出整个循环；`continue` = 跳过本次剩下的，进下一次
- **不知道循环几次用 `while`，遍历用 `for`**

**坑**：`while` 忘了改条件 → 死循环，`Ctrl + C` 中断
**自测**：`range(1, 10)` 一共几个数？（答：9 个）

---

### Day 4 — 列表

```python
scores = [88, 95, 72, 60, 100, 45, 83]

max(scores), min(scores), sum(scores) / len(scores)
scores[:3]                              # 前 3 个
scores[-3:]                             # 后 3 个（负数索引从尾巴数）
scores[::-1]                            # 倒序
60 in scores                            # 判断存在 → True/False

pass_list = [s for s in scores if s >= 60]      # 列表推导式：一行完成"筛选+收集"
```

**必记**：
- 切片 `[a:b]` **含头不含尾**（`[0:3]` 是第 0、1、2 个）
- 列表推导式 = 把「for + if + append」压成一行，项目里天天用

**坑（经典）**：
```python
scores.sort()          # 原地排序，返回 None ✗
x = scores.sort()      # x 是 None！不是排序后的列表
x = sorted(scores)     # ✅ 想拿到新列表用 sorted()
```
**自测**：`scores.sort()` 的返回值是什么？为什么不能 `x = scores.sort()` 然后 `print(x)`？

---

### Day 5 — 字典和字符串

```python
# ---- 字典：键 → 值 ----
count = {}
for w in words:
    count[w] = count.get(w, 0) + 1      # ★ 词频统计招牌写法，背下来

for word, n in count.items():           # items() 同时拿键和值
    print(word, n)

top5 = sorted(count.items(), key=lambda kv: kv[1], reverse=True)[:5]   # 按"值"降序取前 5
```

```python
# ---- 字符串 ----
s.split()                # 按空白切 → 列表
s.split(",")             # 按逗号切
s.strip()                # ★ 去掉两端空白（读文件的行必须用，行尾有 \n）
s.replace("a", "b")
s.upper() / s.lower()
s.startswith("img")      # 判断前缀 → 筛文件名常用
", ".join(words)         # 列表拼成字符串
```

**必记**：
- `d.get(键, 默认值)` = 键不存在时返回默认值，**不报错**；`d[键]` 不存在会抛 `KeyError`
- `count[w] = count.get(w, 0) + 1` 这一行是字典最重要的用法
- `os.path.basename(path)` 从路径取文件名（Day 12/13 天天用）

**坑**：`count[w] += 1` 在键第一次出现时会 `KeyError`
**自测**：`d = {"a": 1}`，`d["b"]` 和 `d.get("b")` 分别是什么结果？

---

### Day 6 — 函数

```python
def calc_stats(scores):
    """返回 (最高分, 最低分, 平均分)"""
    hi  = max(scores)
    lo  = min(scores)
    avg = sum(scores) / len(scores)
    return hi, lo, avg              # 多个返回值 = 返回一个元组

hi, lo, avg = calc_stats([90, 80, 70])      # 元组解包，一次接三个
```

**必记**：
- 函数没写 `return` → 返回 `None`
- `return a, b` 本质是返回元组 `(a, b)`，所以能一次拆开接
- 函数的两大好处：**能单独测试**、**改一处到处生效**

**坑**：Python 用**缩进（4 空格）**划分代码块，不用花括号。缩进错了代码含义就变了。
**自测**：一个函数没有 `return`，调用它得到什么？能对它做加法吗？

---

### Day 7 — 文件读写

```python
# ---- 读 ----
with open("scores.txt", "r", encoding="utf-8") as f:
    for line in f:                       # 一行一行读（处理大文件的标准写法）
        n = int(line.strip())            # ★ strip() 不能省，行尾带 \n
        ...

# ---- 写 ----
with open("result.txt", "w", encoding="utf-8") as f:
    f.write(f"最高分 {hi}\n")            # ★ \n 要自己加，写文件不会自动换行
```

**必记**：
- `with` 会自动关文件（等价于 `try/finally`），**永远用 `with`**
- 模式：`"r"` 读（默认）/ `"w"` 写（**清空重建**）/ `"a"` 追加
- 写文件**不会自动换行**

**坑**：`"w"` 会把原文件清空——想保留旧内容必须 `"a"`

**项目关联**：以后 RKNN 量化要写 `dataset.txt`（每行一个图片路径 + 校准集），用的就是这一天的知识。

**自测**：`open("x.txt", "w")` 时如果 x.txt 已经有一千行内容，会发生什么？

---

### Day 8 — NumPy 基础（图 = 数组）

```python
import numpy as np

a = np.array([[1, 2, 3],
              [4, 5, 6]])
a.shape        # (2, 3)  →  2 行 3 列
a[0]           # [1 2 3]      第 0 行
a[:, 0]        # [1 4]        第 0 列（: 表示"这一维全要"）
a[1, 2]        # 6            第 1 行第 2 列

np.zeros((3, 4))                    # 全 0
np.ones((2, 3))                     # 全 1
np.random.rand(100, 100)            # 0~1 随机
np.arange(12).reshape(3, 4)         # 0~11 重排成 3 行 4 列
```

**⭐⭐ 三条铁律（必须刻进脑子）**

1. **二维数组 = `(行, 列)`；图像 = `(高, 宽, 通道)`**
2. **先高后宽 / 先 y 后 x** —— 图像里是 `img[y, x]`，**不是** `img[x, y]`
3. OpenCV 读进来是 **BGR**，所以 `img[:, :, 0]` 是**蓝**通道（不是红！）

```python
img[y1:y2, x1:x2]      # 裁剪 = 切片（先高后宽）
img[:, :, 0]           # 取出第 0 个通道 = 一张二维图
```

**必记**：灰度图是 `(高, 宽)`（**二维**），彩色图是 `(高, 宽, 3)`（**三维**）。
这个区别会在 Day 14 转灰度时咬你——灰度图**没有** `[:, :, 0]` 可以取。

**自测**：一个 `(480, 640, 3)` 的数组，480 是高还是宽？`img[100, 200]` 取的是哪个位置？

---

### Day 9 — NumPy 运算（思维转变日）

```python
a = np.random.rand(100, 100)

a.mean(), a.max(), a.min()          # 统计
a + 10                              # ★ 整个数组一起加，不写循环
a * 2
np.where(a > 0.5, 1, 0)             # 条件选择：满足取 1，否则取 0
a[a > 0.5]                          # 布尔索引：取出所有满足条件的元素
a[a > 0.5] = 1                      # 原地修改（二值化就这么写）
a.sum(axis=0)                       # 每列求和；axis=1 是每行求和
```

**★ 核心思维转变**：**不要写 `for` 循环处理每个元素。**
NumPy 一次算完整个数组（底层是 C，快几十倍）。这是新手最大的坎。

**axis 记法**：`axis=0` = 沿着第 0 维（行）方向压缩 → 得到"每列一个结果"。
记不住就当场跑一下 `.shape` 验证，别硬背。

**项目关联**：车牌识别里"取出所有置信度 > 0.5 的检测框"就是 `a[a > 0.5]`。

**自测**：`(480, 640, 3)` 的图求 `mean(axis=2)`，结果的 shape 是什么？
（答：`(480, 640)`——三个通道压成一个，就是灰度图！）

---

### Day 10 — OpenCV 读图、存图

```python
import cv2

img = cv2.imread(path)         # ★ 失败返回 None，不抛异常！
if img is None:                # ★ 第一道防线，必须判
    print("读图失败:", path)

print(img.shape)               # (高, 宽, 3)
print(f"尺寸: {img.shape[1]} x {img.shape[0]}")   # 宽 x 高（先宽后高，因为给人看）

cv2.imwrite(out_path, img)     # ★ 失败返回 False，也不抛异常
```

**必记**：
- **`imread` 失败 = 返回 `None`（安静的失败）**，一路传下去会在后面炸出莫名其妙的错误
- 相对路径是相对**当前工作目录**，不是脚本所在目录 → 老老实实写绝对路径
- WSL 里 `cv2.imshow` 弹不出窗口（没有图形界面）→ 用 `imwrite` 存到 Windows 目录里看

```python
# 让同一份代码在 WSL 和板子上都能跑：有图形界面才弹窗
if os.environ.get("DISPLAY"):
    cv2.imshow("preview", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
```

**坑（你踩过）**：`cv2.imread('1.png')` 返回 `None` → 后面 `imshow` 断言
`size.width>0 && size.height>0` 失败。**根子就是没检查 `None`。**

**自测**：读错路径的图片，Python 会报错吗？程序接下来会怎样？

---

### Day 11 — 缩放、裁剪、画图

```python
h, w = img.shape[:2]                                # 取前两个值 = 高、宽
small = cv2.resize(img, (640, int(h * 640 / w)))    # ★ dsize = (宽, 高)
center = img[h//4 : h*3//4, w//4 : w*3//4]          # 裁剪 = 切片（先高后宽）

cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)      # ★ 点是 (x, y)
cv2.putText(img, "plate", (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)               # 半径 5，-1 = 实心
```

**⚠️ 本节是全项目最容易搞混的地方 —— 四套顺序同时存在**

| 东西 | 顺序 |
|---|---|
| `img.shape` / 数组索引 / 切片 | **先高后宽**（先 y 后 x） |
| `cv2.resize` 的 `dsize` | **先宽后高**（先 x 后 y） |
| `cv2.rectangle` / `putText` 的坐标点 | **先 x 后 y** |
| 喂给模型的 shape（NCHW） | 先 batch 后通道，再高宽 `(1,3,H,W)` |

**每次都要停下来想一秒，别靠手感。**

**其他必记**：
- 颜色是 `(B, G, R)`：**蓝色 `(255,0,0)`、绿色 `(0,255,0)`、红色 `(0,0,255)`** —— 记住 B 在第一个
  （和 CSS/画图软件的 RGB 顺序**正好相反**，所以别凭习惯写 `(255,0,0)` 当红色）
- 绘制函数（`rectangle` / `putText` / `circle`）**在传入的数组上原地修改**，不用接返回值
- `thickness = -1` 是**实心填充**
- **路径（字符串）≠ 图像（数组）**：`imread` 要字符串，`resize` / `rectangle` 要数组

**项目关联**：`cv2.rectangle` 就是你以后画车牌框用的函数——第 11 天已经学过一遍了。

**自测**：把一张 `(480, 640, 3)` 的图缩放到宽 320，新 shape 是多少？为什么"宽 320"写出来却像 `(320, 240)`？

---

### Day 12 — 批量处理（本阶段最重要的练习）

**骨架（建议背下来）：**

```python
import os
import glob
import cv2

input_dir  = os.path.expanduser("~/datasets/images")
output_dir = os.path.expanduser("~/datasets/output")
os.makedirs(output_dir, exist_ok=True)          # 目录不存在就建，已存在也不报错

files = sorted(glob.glob(os.path.join(input_dir, "*.jpg")))
total = len(files)                              # 常量：只用不改
if total == 0:                                  # 空目录在循环外判一次
    raise SystemExit(f"未找到图像：{input_dir}")

for index, path in enumerate(files, start=1):   # ★ start=1 → 进度从 [1/20] 开始
    name = os.path.basename(path)

    img = cv2.imread(path)
    if img is None:
        print(f"[{index}/{total}] 跳过: {name}")
        continue

    h, w = img.shape[:2]
    small = cv2.resize(img, (640, int(h * 640 / w)), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]                    # ★ 缩放后坐标要按新尺寸算！

    cv2.rectangle(small, (10, 10), (sw - 10, sh - 10), (0, 255, 0), 2)
    cv2.putText(small, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    out_path = os.path.join(output_dir, "processed_" + name)
    cv2.imwrite(out_path, small)
    print(f"[{index}/{total}] 处理中: {name}")
```

**必记的三个 os 函数**：

```python
os.path.expanduser("~/datasets")           # ~ 展开成 /home/user
os.path.join(a, b)                         # 拼路径（别手写 "/"，跨平台会挂）
os.path.basename(path)                     # 从路径里取文件名
os.makedirs(dir, exist_ok=True)            # 建目录（含中间层），已存在不报错
```

**五个坑（你全踩过，对照复习）**：

| 坑 | 正确做法 |
|---|---|
| `for ... else` 以为"是没进循环才执行" | `else` 是"循环**正常跑完**（没被 `break`）就执行"，和空目录无关 |
| 进度打出 `[0/20]`…`[19/20]`，永远到不了 `[20/20]` | `enumerate(files, start=1)` |
| 拿 `rectangle(...)` 的返回值 | 绘制函数是原地修改，返回值是 `None`，不用接 |
| `thickness=-1` 以为是"不画" | `-1` = **实心填充** |
| `putText` 起点写 `(500, 30)`，字被裁掉 | 起点 x 别超出图片宽度（可以先用 `cv2.getTextSize` 量一下） |
| `glob` 找不到文件 | 返回 `[]`（**不是异常**）→ 用 `if total == 0` 判断 |
| 输出写回 `images/` | 输入输出**目录分开**，输出名加 `processed_` 前缀 |

**自测**：`sorted(glob.glob(...))` 里的 `sorted` 有什么用？不加会怎样？

---

### Day 13 — 异常处理（让批处理崩不掉）

**⭐ 整篇最重要的一张表：两类失败，两道防线**

| | 表现 | 用什么接 |
|---|---|---|
| **安静的失败** | `imread` → `None`；`imwrite` → `False`；`glob` → `[]`；`os.path.exists` → `False` | **`if` 判断** |
| **抛出的异常** | `resize(None)`、坐标传了 float、没权限、磁盘满 | **`try / except`** |

**`try/except` 抓不住"安静的失败"** —— 这就是为什么要主动 `raise` 升级：

```python
img = cv2.imread(path)          # 安静的失败：返回 None
if img is None:
    raise ValueError("imread 返回 None（文件损坏 / 不是图片）")   # ★ 升级成异常
# ↑ 一旦 raise，立刻跳到最近的 except，后面的 resize/rectangle 全部跳过
```

**完整骨架（Day 13 成果）：**

```python
ok_list, fail_list = [], []                     # 两个"记账本"
total = len(files)

for index, path in enumerate(files, start=1):
    name = os.path.basename(path)               # 放 try 外面，except 里也要用
    try:
        img = cv2.imread(path)
        if img is None:                         # 第一道防线：if 抓安静的失败
            raise ValueError("imread 返回 None")
        # ... 正常处理 ...
        if not cv2.imwrite(out_path, small):    # 第二道防线：又一个安静的失败
            raise IOError(f"imwrite 返回 False: {out_path}")
        ok_list.append(name)
        print(f"[{index}/{total}] 成功: {name}")
    except Exception as e:                      # 所有异常汇到这一处
        fail_list.append((name, f"{type(e).__name__}: {e}"))
        print(f"[{index}/{total}] 失败: {name} -> {type(e).__name__}: {e}")

print(f"\n共 {total} 张：成功 {len(ok_list)}，失败 {len(fail_list)}")
for name, reason in fail_list:
    print(f"  ✗ {name}: {reason}")
```

**必记**：
- `except Exception as e:` —— `Exception` = "只要是程序运行错误我都接"；`as e` = 把异常对象绑给 `e`
- 读异常信息：`type(e).__name__`（类型）+ `str(e)`（消息）
- **不要写裸 `except:`** —— 它会连 `Ctrl+C` 一起吞掉（`KeyboardInterrupt` 不在 `Exception` 里）
- **也不要 `pass` 掉** —— 只统计"失败 3 张"却不写原因，等于没做错误处理
- 多个 `except` 时：**具体的写前面，`Exception` 兜底放最后**
- `finally` = 无论成功失败都执行（收尾：关文件、删临时文件）。**批处理用不到，知道就够**

**异常家族树（看一眼就懂为什么写 `Exception`）**

```
BaseException
├── SystemExit          ← raise SystemExit() / sys.exit()
├── KeyboardInterrupt   ← 你按 Ctrl+C   （★ 不在 Exception 里！）
└── Exception           ← ★ 你平时要接的就是这一层
    ├── ValueError / TypeError / AttributeError / NameError
    ├── LookupError → IndexError / KeyError
    ├── ArithmeticError → ZeroDivisionError
    ├── OSError → FileNotFoundError / PermissionError / IsADirectoryError
    └── ImportError → ModuleNotFoundError
```

**常见异常速查（记名字，见到不慌）**

| 类型 | 什么情况 | 例子 |
|---|---|---|
| `ValueError` | 类型对、**值不对** | `int("abc")` |
| `TypeError` | **类型不对** | `"a" + 1`、`cv2.resize(None, ...)` |
| `AttributeError` | 对象**没这个属性** | `None.shape` |
| `NameError` | **变量名没定义**（打错字） | 用了 `imag` 但定义的是 `img` |
| `IndexError` | 列表/字符串**越界** | `[1,2,3][99]` |
| `KeyError` | 字典**没这个键** | `{"a":1}["b"]` |
| `ZeroDivisionError` | 除以零 | `1 / 0` |
| `FileNotFoundError` | `open()` 的文件不存在 | **注意 `imread` 不抛它，只返回 `None`** |
| `PermissionError` | 没权限 | 读 `chmod 000` 的文件 |
| `ModuleNotFoundError` | `import` 不到模块 | **忘了 `source .venv/bin/activate` 时最常见** |
| `cv2.error` | OpenCV 自己的异常 | 断言失败 `(-215:Assertion failed)` |

**⭐ 报错三步读法（traceback）**

```
Traceback (most recent call last):
  File "day13.py", line 31, in <module>          ← ② 往上找最近一条"自己的文件"
    img = cv2.imread(path)
  File ".../cv2/__init__.py", line 100, in ...   ← ① 中间是库内部，先跳过
cv2.error: ... (-215:Assertion failed) ...       ← ③ 读最后一行：类型 + 消息
```

1. **看最后一行** —— 到底出了什么事（类型 + 消息）
2. **往上找最近一条自己的 `File "...", line N`** —— 在哪一行出的
3. 中间全是库的内部调用栈，**先忽略**

> 看到 `During handling of the above exception, another exception occurred:`
> = **你的 `except` 代码块里又炸了**，真正的问题在**下面那一段**。

**三条铁律（背下来）**

1. **安静的失败用 `if`，抛出的异常用 `try`** —— 两道防线，缺一不可
2. **永远别写裸 `except:`，也别 `pass` 掉** —— 用 `except Exception as e` 并把 `e` 记下来
3. **`try` 的范围要小** —— 只包"可能出事的那几行"
   *（例外：批量处理里把"整张图"当一个单元包起来是合理的，因为处置方式相同 → 跳过 + 记录）*

**Day 13 第二个任务：虚拟环境**

```bash
mkdir -p ~/projects/test-venv && cd ~/projects/test-venv
python3 -m venv .venv
source .venv/bin/activate              # ★ 提示符前面出现 (.venv) 才算成功
pip install opencv-python
python3 -c "import cv2; print(cv2.__version__)"
deactivate
```

**必记**：`ModuleNotFoundError` 十有八九 = **忘了激活虚拟环境**。
每天开工第一件事永远是：
```bash
cd ~/projects/py-basics && source .venv/bin/activate
```

**自测**：`cv2.imread` 读一张坏图，`try/except` 能直接抓到吗？为什么？
（答：抓不到，它返回 `None` 不抛异常，必须 `if img is None: raise` 升级。）

---

## 三、跨天主线：一个脚本的成长史

这是最有效的复习方式——**看同一个脚本是怎么被 13 天一点点"喂"大的**。

```python
# ===== Day 1-2：先能判断一件事 =====
path = input("图片路径: ")                      # D1: input 返回 str
if not path.endswith(".jpg"):                   # D2: 条件
    print("不是 jpg")

# ===== Day 3-4：从"一张"变成"一批" =====
files = []                                      # D4: 列表收集
for i in range(1, 21):                          # D3: 循环 20 次
    files.append(f"img{i}.jpg")

# ===== Day 5-6：整理 + 打包 =====
import os
names = [os.path.basename(p) for p in files]            # D5: 字符串/路径
def process(path):                                      # D6: 函数
    return os.path.basename(path).upper()

# ===== Day 7：结果落盘 =====
with open("report.txt", "w", encoding="utf-8") as f:    # D7: 文件写入
    f.write("\n".join(names))

# ===== Day 8-9：图片其实是数组 =====
import numpy as np
img = np.zeros((480, 640, 3), dtype=np.uint8)           # D8: shape = (高,宽,通道)
gray = img.mean(axis=2)                                 # D9: 向量化（不写循环）

# ===== Day 10-11：真正开始处理图片 =====
import cv2
img = cv2.imread(path)                                  # D10: 读（失败返回 None）
small = cv2.resize(img, (640, 480))                     # D11: dsize = (宽,高)
cv2.rectangle(small, (10, 10), (630, 470), (0, 255, 0), 2)   # D11: 点 = (x,y)
cv2.imwrite("out.jpg", small)                           # D10: 存（失败返回 False）

# ===== Day 12：批量 + 进度 =====
for index, path in enumerate(sorted(glob.glob("*.jpg")), start=1):
    print(f"[{index}/{total}] 处理中: {path}")

# ===== Day 13：崩不掉 + 记账 =====
try:
    ...
except Exception as e:
    fail_list.append((name, f"{type(e).__name__}: {e}"))
```

**结论：13 天没有一天是多余的——它们最后全都住在同一个脚本里。**
你现在看到的 `day13.py`，就是这 13 天的合成体。

---

## 四、速查卡（建议打印出来贴墙）

```bash
# ---- 每天开工 ----
cd ~/projects/py-basics && source .venv/bin/activate     # 提示符出现 (.venv)
```

```python
# ---- 路径（Day 5/12）----
os.path.expanduser("~/datasets")        # ~ → /home/user
os.path.join(a, b)                      # 拼路径，别手写 "/"
os.path.basename(path)                  # 取文件名
os.makedirs(d, exist_ok=True)           # 建目录，已存在不报错

# ---- 找文件（Day 12）----
files = sorted(glob.glob(os.path.join(input_dir, "*.jpg")))
if len(files) == 0: raise SystemExit("没找到图片")

# ---- OpenCV 五件套（Day 10/11）----
img   = cv2.imread(path)                          # 失败 → None
h, w  = img.shape[:2]                             # 先高后宽
small = cv2.resize(img, (640, int(h*640/w)))      # dsize 先宽后高
crop  = img[y1:y2, x1:x2]                         # 裁剪，先高后宽
cv2.rectangle(img, (x1,y1), (x2,y2), (0,255,0), 2)   # 点先 x 后 y
gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)     # 转灰度 → 变二维
cv2.imwrite(out, img)                             # 失败 → False

# ---- NumPy（Day 8/9）----
a.shape, a.dtype
a.mean(), a.max(), a[ a > 0.5 ]
np.where(a > 0.5, 1, 0)
a.sum(axis=0)                            # 每列；axis=1 每行

# ---- 错误处理（Day 13）----
if img is None: raise ValueError("读图失败")           # 防线一：安静的失败
try: ... except Exception as e: print(type(e).__name__, e)   # 防线二
```

**四套坐标顺序（抄在显示器边上）**

| | 顺序 |
|---|---|
| `img.shape` / 索引 / 切片 | **先高后宽**（y, x） |
| `resize` 的 `dsize` | **先宽后高**（x, y） |
| `rectangle` / `putText` 坐标 | **先 x 后 y** |
| 模型输入 NCHW | **(1, 3, H, W)** |

---

## 五、自测 20 题（先遮住答案）

1. `input()` 返回什么类型？想算数要怎么办？
2. `range(1, 101)` 里有几个数？最大的数是多少？
3. `break` 和 `continue` 的区别？
4. `scores.sort()` 的返回值是什么？
5. `scores[:3]` 取的是第几个到第几个？
6. `d["x"]` 和 `d.get("x")` 在键不存在时分别怎样？
7. 词频统计那行招牌代码怎么写？
8. 函数没写 `return`，返回什么？
9. 读文件时为什么必须 `line.strip()`？
10. `open(..., "w")` 对一个已有内容的文件做什么？
11. 一个 `(480, 640, 3)` 的数组，哪个是高？`img[100, 200]` 是什么位置？
12. OpenCV 的 `img[:, :, 0]` 是哪个颜色通道？
13. 灰度图的 shape 是几维？
14. `np.where(a > 0.5, 1, 0)` 在干什么？不用它怎么写？
15. `a.sum(axis=0)` 和 `a.sum(axis=1)` 分别得到什么？
16. `cv2.imread` 失败会怎样？`cv2.imwrite` 呢？
17. `cv2.resize(img, dsize)` 的 `dsize` 是 `(宽, 高)` 还是 `(高, 宽)`？画框坐标呢？
18. `enumerate(files, start=1)` 里的 `start=1` 解决什么问题？
19. 哪两类失败？分别用什么抓？
20. 报错应该看哪一行？`ModuleNotFoundError` 最常见的原因是什么？

<details>
<summary><b>👉 点开看答案</b></summary>

1. 永远返回 `str`；要算数先 `int()` / `float()` 转换。
2. 100 个；最大 100。（`range` 右端不含，所以是 1–100）
3. `break` 跳出整个循环；`continue` 跳过本次剩余、进下一次。
4. 返回 `None`（原地排序）→ 想要新列表用 `sorted(scores)`。
5. 第 0、1、2 个（**含头不含尾**）。
6. `d["x"]` → `KeyError`；`d.get("x")` → `None`（或你给的默认值）。
7. `count[w] = count.get(w, 0) + 1`
8. `None`。
9. 每行末尾带 `\n`，不 `strip()` 的话字符串会带着换行——做比较、当字典键、拼消息都会出怪问题。（`int("88\n")` 恰好能容忍换行，但**别依赖这个**，规范动作就是先 `strip()`。）
10. **清空重建**（原内容全丢）→ 想保留用 `"a"`。
11. 480 是高，640 是宽；`img[100, 200]` = 第 100 行、第 200 列（**先高后宽**）。
12. 蓝（B）——OpenCV 是 **BGR** 顺序，所以第 0 个是蓝。
13. 二维 `(高, 宽)`，没有通道维。
14. 把大于 0.5 的变 1、其余变 0；也可以写 `a[a > 0.5] = 1` 或 `(a > 0.5).astype(int)`。
15. `axis=0` → 每列一个结果（沿行方向压缩）；`axis=1` → 每行一个结果。
16. 都**不抛异常**：`imread` → `None`；`imwrite` → `False`。必须用 `if` 判断。
17. `dsize` 是 `(宽, 高)`；画框坐标是 `(x, y)`（**先 x 后 y**）。
18. 让进度从 `[1/20]` 开始，而不是 `[0/20]`，避免永远打不出 `[20/20]`。
19. **安静的失败**（`None`/`False`/`[]`）用 `if`；**抛出的异常**用 `try/except`。
20. 看**最后一行**（类型 + 消息），再往上找最近一条自己的文件+行号；`ModuleNotFoundError` 最常见原因是**忘了激活虚拟环境**。

</details>

---

## 六、合书默写题（这才是真验收）

> 不看任何资料，用纸笔或空白文件写。

1. **默写 Day 12 骨架**（5 分钟内）：遍历 `~/datasets/images/*.jpg` → 缩放到宽 640 → 画框写字 → 存到 `~/datasets/output/processed_xxx.jpg`，打印进度。
2. **默写 Day 13 骨架**（在上一题基础上加）：读图失败不崩、最后打印成功/失败张数并列出失败原因。
3. **写出四套坐标顺序**（shape / resize / rectangle / NCHW）。
4. **写出两类失败**，各举两个函数例子。
5. **写出 8 个异常类型名**，各配一个触发例子。
6. **不看资料说出**：`os.path.join`、`os.path.basename`、`os.makedirs(..., exist_ok=True)` 各有什么用。

**全对 → Python 部分可以毕业了，直接进 Day 14 综合验收。**

---

## 七、哪一天还很虚？回去补哪份

| 薄弱环节 | 回看哪份文档 |
|---|---|
| Day 1–7 语法（变量/条件/循环/列表/字典/函数/文件） | `docs/03-Python练习计划.md` |
| Day 8–9 NumPy（shape、维度顺序、向量化） | `docs/04-NumPy入门.md` |
| Day 10–12 OpenCV（读图/缩放/裁剪/画框/批量） | `docs/06-OpenCV入门.md`（§10–11 是 Day 11–12） |
| Day 13 异常处理（两道防线、traceback 读法） | `docs/08-异常处理.md` |
| 环境/虚拟环境出问题 | `docs/00-安装说明.md`、`docs/10-环境排查方法论.md` |
| Linux 命令生疏 | `docs/02-Linux速查表.md` |

---

## 八、下一步

复习完这份，接着做：

- [ ] **Day 13 收尾**：造一张坏图 (`echo "xx" > broken.jpg`)，跑一遍 day13.py，确认打印「成功 20，失败 1」并列出原因，然后 `rm broken.jpg`
- [ ] **Day 14 综合验收**：写 `day14.py`（遍历 → 缩放到宽 800 → 转灰度 → 底部黑条写 `文件名 | 尺寸 WxH` → 存 `~/datasets/output_grayscale/` → 全程不崩 → 写 `report.txt`）
- [ ] 完成后 → 进入**车牌检测阶段**（YOLO）

> **提醒**：Day 14 会用到 `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)` 和「灰度图是二维的」，
> 还有「在图片底部画黑条」其实是 NumPy 切片赋值（`img[-40:, :] = 0`）——
> 那正好是 Day 8/9 的知识。**这就是为什么 8、9 两天不能跳。**
