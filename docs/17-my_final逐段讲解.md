# `my_final.py` 逐段讲解

> **这份文件是什么**：把你亲手写完的那条流水线，从第一行到最后一行拆开讲清楚。
>
> **配合阅读**：`docs/16-系统教材-从一张图到车牌号.md` 第 5、6、7、10 章。
> **对应关系**：这份代码 = 教材第 10 章那张"一张图的完整旅程"流程图。

---

## 零、先看全局

**这个文件只干一件事**：

```
一张图  ──→  图上的几个框
```

**整个文件分 4 个部分：**

| 部分 | 名字 | 干什么 | 谁写的 |
|---|---|---|---|
| **§0** | 依赖与常量 | import 工具 | 样板 |
| **§1** | `letterbox()` | 保比例缩放到 640×640 | 样板（但**要读懂**） |
| **§2** | 粘贴区三个函数 | `decode_scale` / `iou_many` / `nms` | **你自己写的** |
| **§3** | `collect_one_scale()` | 一个尺度 → 一批候选框 | **你自己写的（核心）** |
| **§4** | 主流程 8 个阶段 | 串起来 | 一半你一半样板 |

**主流程的 8 个阶段：**

```
[1] 读图 + letterbox                    ← 第一段：你的活（预处理）
[2] 转 blob（BGR→RGB / 除255 / HWC→CHW / 加batch）
[3] 推理 → 3 个输出数组                 ← 第二段：模型的活（黑盒）
[4] collect_one_scale × 3  →  拼接      ← 第三段：你的活（后处理）
[5] 内容区过滤
[6] NMS
[7] 反向映射回原图
[8] 画框 + 存图
```

---

# §0　依赖与常量

```python
import os
import numpy as np
import cv2
import onnxruntime as ort

from yolo_infer import COCO_NAMES          # 80 个类别名，借用
```

| 行 | 作用 | 属于哪一层 |
|---|---|---|
| `import os` | 路径处理（`os.path.expanduser` 把 `~` 展开成 `/home/user`） | 第 1 层 环境 |
| `import numpy as np` | **数组运算**——解码、过滤、NMS 全靠它 | 第 4 层 算法 |
| `import cv2` | 读图、缩放、画框、存图 | 第 4 层 算法 |
| `import onnxruntime as ort` | **跑 ONNX 模型** | 第 3 层 运行 |
| `from yolo_infer import COCO_NAMES` | 80 个类别名的字符串列表 | — |

> **为什么 `COCO_NAMES` 要"借"？** 它只是一串字符串（`"person"`, `"car"`, …），
> **抄 80 行没有学习价值**。**能复用的东西就复用**——这是工程习惯。

---

# §1　`letterbox()` —— 保比例缩放

## 它解决什么问题

模型**只吃 640×640**，但你的照片是 4096×3072。
**直接拉伸会改变宽高比 → 车牌被压扁 → 模型认不出。**

所以要：**保持比例缩放 + 空白处填灰边**。

```
4096×3072
   ↓ r = min(640/3072, 640/4096) = 0.15625     ← 取小的，保证装得下
 640×480
   ↓ 高度还差 640-480 = 160
 上下各填 80 像素灰边
   ↓
 640×640
```

## 代码逐行

```python
def letterbox(img, size=640):
    h, w = img.shape[:2]                            # ① 取高和宽
    r = min(size / h, size / w)                     # ② 缩放系数
    nh, nw = int(round(h * r)), int(round(w * r))   # ③ 缩放后的高宽
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)  # ④
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)               # ⑤
    top = (size - nh) // 2                                                  # ⑥
    left = (size - nw) // 2
    canvas[top:top + nh, left:left + nw] = resized                          # ⑦
    return canvas, r, left, top, nw, nh                                     # ⑧
```

| 行 | 在干什么 | 用到的旧知识 |
|---|---|---|
| ① | `img.shape[:2]` 取前两个 = **高、宽** | Day 8「先高后宽」 |
| ② | `min(...)` 取小的，**保证图能装进 640** | — |
| ③ | `round` 再 `int`，避免浮点尺寸 | — |
| ④ | `cv2.resize` 的 `dsize` 是 **`(宽, 高)`** | Day 11「顺序陷阱」 |
| ⑤ | 造一张纯灰画布（**114 是 YOLO 的标准灰**） | `np.full` |
| ⑥ | **居中**填充：上下各一半 | — |
| ⑦ | 把缩放后的图**贴**到灰布中间 | Day 8 切片赋值 |
| ⑧ | **返回 6 个值**——关键是 `r / left / top`，后面"退货"要用 | Day 6 多返回值 |

## ⭐ 返回值为什么是 6 个

```
canvas  ← 喂给模型的图
r       ← 缩放系数 0.1562      ┐
left    ← 左填充 0             ├─ ★ 反向映射要用这三个
top     ← 上填充 80            ┘
nw, nh  ← 缩放后尺寸（调试用）
```

> **第 7 章那句话**：`letterbox()` 输出 `r, left, top`，就是为了最后"退货"用的。
> **90% 的教程漏讲这一步**，而它是框画错位置的第一大原因。

---

# §2　粘贴区：你写的三个函数

这三个函数**你已经单独写过、单独验证过**，这里只是搬进来用。

| 函数 | 输入 | 输出 | 在哪验证过 |
|---|---|---|---|
| `decode_scale(out, stride, anchors)` | 一个尺度的原始输出 `(1,255,H,W)` | `cx,cy,w,h` 各 `(3,H,W)` | 任务 3c |
| `iou_many(box, boxes)` | 一个框 `(4,)` + 一堆框 `(N,4)` | `(N,)` 的 IoU | 任务 4b |
| `nms(boxes, scores, iou_thresh)` | 框 + 分数 | 保留下来的**下标** | 任务 4c / 6 |

**外加两张配置表：**

```python
STRIDES = [8, 16, 32]
ANCHORS = [ [[10,13],[16,30],[33,23]],          # 尺度0 (80x80)
            [[30,61],[62,45],[59,119]],         # 尺度1 (40x40)
            [[116,90],[156,198],[373,326]] ]    # 尺度2 (20x20)
```

> ⚠️ **下标必须对齐**：`outs[0]` 是 80×80 → 用 `STRIDES[0]=8` 和 `ANCHORS[0]`。
> 这个对应关系来自 `640 ÷ 80 = 8`。

---

# §3　`collect_one_scale()` —— 核心函数

## 它解决什么问题

**把"一个尺度的原始输出"变成"一批候选框"。**

```
输入: (1, 255, 80, 80)          ← 模型吐出来的密码
输出: boxes (N,4) + scores (N,) + class_ids (N,)   ← 人能用的框
```

**它是整个文件的心脏**——主流程只是把它调 3 次然后拼接。

## 代码逐行

```python
def collect_one_scale(out, stride, anchors, conf_thresh):
    o = out[0]                                  # ①
    H, W = o.shape[-2], o.shape[-1]             # ②
    o = o.reshape(3, 85, H, W)                  # ③

    cx, cy, w, h = decode_scale(out, stride, anchors)      # ④
```

| 行 | 在干什么 | 形状变化 |
|---|---|---|
| ① | **去掉 batch 维** | `(1,255,H,W)` → `(255,H,W)` |
| ② | **从数组读**网格大小（用负索引，永远对） | `H, W` |
| ③ | **把 255 拆成 `3 anchor × 85 通道`** | `(255,H,W)` → `(3,85,H,W)` |
| ④ | **解码**（调用你写的函数） | → `cx,cy,w,h` 各 `(3,H,W)` |

```python
    # ---- ① 中心+宽高 → 左上+右下 ----
    x1 = cx - w / 2
    y1 = cy - h / 2
    x2 = cx + w / 2
    y2 = cy + h / 2
```

**为什么要这一步？** 因为**模型给的是"中心点 + 宽高"，而 `cv2.rectangle` 要的是"左上角 + 右下角"。**

```
      cx,cy
        ●              ┌──────────┐
       ╱ ╲             │          │
      ╱   ╲     →      │          │
     └─────┘           └──────────┘
      w × h            (x1,y1)  (x2,y2)

   中心 + 宽高          左上 + 右下
```

| 方向 | 公式 |
|---|---|
| 中心+宽高 → 角点 | `x1 = cx - w/2`, `x2 = cx + w/2` |
| 角点 → 中心+宽高 | `cx = (x1+x2)/2`, `w = x2-x1` |

> **这两个方向你都在用**：#4 用前一个，#5 的内容区过滤用后一个。

```python
    # ---- ② 置信度 ----
    obj     = o[:, 4]              # (3, H, W)    "这里有东西吗"
    cls     = o[:, 5:]             # (3, 80, H, W) 80 个类别分数
    cls_max = cls.max(axis=1)      # (3, H, W)    每个格子的最大类分数
    cls_id  = cls.argmax(axis=1)   # (3, H, W)    最大分数对应的类别下标
    conf    = obj * cls_max        # (3, H, W)    ★ 最终置信度
```

**这一段是全文件最需要理解的地方：**

| 量 | 通道 | 形状 | 含义 |
|---|---|---|---|
| `obj` | 第 4 个 | `(3,H,W)` | "这格里有东西吗" |
| `cls` | 第 5~84 个 | `(3,80,H,W)` | 80 个类别的分数 |
| `cls_max` | — | `(3,H,W)` | 挑出最高的那个分数 |
| `cls_id` | — | `(3,H,W)` | 记住**是哪个类别** |
| **`conf`** | — | `(3,H,W)` | **`obj × cls_max`** ← 最终依据 |

**⭐ 两个关键点：**

**1. 为什么 `axis=1`？**

```
cls 的形状: (3, 80, H, W)
              ↑   ↑
           anchor 类别(80) ← 要"压掉"的就是这一维，它在第 1 位
```

**"沿某一维压缩"就是 `axis=那一维的编号`**（Day 9 学的）。
压掉之后 → `(3, H, W)` ✓

**2. 为什么 `conf` 是相乘？**

| obj | cls_max | 潜台词 | 处理 |
|---|---|---|---|
| 0.9 | 0.95 "车" | 有东西，而且是车 | ✅ |
| 0.9 | 0.01 "车" | 有东西，但不知道是啥 | ❌ 丢弃 |
| 0.01 | 0.95 "车" | 自相矛盾 | ❌ 丢弃 |

**两个条件必须同时成立** → 用乘法（Day 2 的 `and` 逻辑）。

> **obj 的真正作用**：模型给 25200 个候选，**大多数在天空/路面/墙上**。
> **obj 就是用来干掉这些背景垃圾的。**
>
> **实测证据**：不用 obj → 2094 个候选、402 个框（全是误检）；用 obj → 44 个候选、3 个框 ✓

```python
    # ---- ③ 过滤 + 拉平成 (N,4) ----
    mask = conf > conf_thresh           # (3,H,W) 的布尔数组
    boxes = np.stack([x1[mask], y1[mask], x2[mask], y2[mask]], axis=1)
    return boxes.astype(np.float32), conf[mask].astype(np.float32), cls_id[mask].astype(np.int32)
```

| 行 | 在干什么 |
|---|---|
| `mask = conf > 0.5` | 布尔数组，`True` 表示"这个格子值得留" |
| `x1[mask]` | **布尔索引**：取出所有 `True` 位置的值 → 一维数组 `(M,)` |
| `np.stack([...], axis=1)` | 把 4 个一维数组**竖着拼**成 `(M, 4)` |
| `.astype(...)` | 统一 dtype（float32 / int32） |

**`np.stack` 的效果：**

```
x1[mask] = [560.1, 278.3, 252.0]     ┐
y1[mask] = [399.2, 416.5, 423.1]     │  np.stack(..., axis=1)
x2[mask] = [603.9, 364.0, 291.2]     │  ────────────────────→   (M, 4)
y2[mask] = [521.3, 489.4, 464.8]     ┘

结果: [[560.1, 399.2, 603.9, 521.3],
       [278.3, 416.5, 364.0, 489.4],
       [252.0, 423.1, 291.2, 464.8]]
```

**这就是"一堆框"的标准格式 `(N, 4)`**——`nms()` 要的就是它。

> **`mask` 一物三用**：`x1[mask]`、`conf[mask]`、`cls_id[mask]` 用的都是**同一个 mask**，
> 所以三条数据**一一对应**，不会错位。**这是关键。**

---

# §4　主流程 8 个阶段

## `[1]` 读图 + letterbox

```python
img = cv2.imread(IMG_PATH)
H0, W0 = img.shape[:2]                     # 原图的高宽（后面裁剪要用）
box, r, pad_left, pad_top, content_w, content_h = letterbox(img)
```

| 变量 | 值（test1.jpg） | 用途 |
|---|---|---|
| `H0, W0` | 3072, 4096 | 反向映射后裁剪用 |
| `r` | 0.1562 | 反向映射 |
| `pad_left, pad_top` | 0, 80 | 反向映射 + 内容区过滤 |
| `content_w, content_h` | 640, 480 | 内容区过滤 |

## `[2]` 转 blob —— 4 个变换挤在 2 行

```python
blob = box[:, :, ::-1].astype(np.float32) / 255.0
blob = np.ascontiguousarray(np.transpose(blob, (2, 0, 1))[None, ...])
```

**拆成 4 个动作：**

| # | 写法 | 变换 | 为什么 |
|---|---|---|---|
| 1 | `box[:, :, ::-1]` | **BGR → RGB** | OpenCV 读进来是 BGR，模型要 RGB |
| 2 | `.astype(np.float32) / 255.0` | **归一化 0~255 → 0~1** | 训练时就这么喂的 |
| 3 | `np.transpose(blob, (2,0,1))` | **HWC → CHW** | 图是"先高后宽"，模型要"先通道" |
| 4 | `[None, ...]` | **加 batch 维** | 模型接口是 `(N,C,H,W)` |

```
(640,640,3)  →  (3,640,640)  →  (1,3,640,640)
                    ↑                ↑
              HWC→CHW          加 batch 维
```

| 附加 | 作用 |
|---|---|
| `np.ascontiguousarray` | 让内存连续（转置后内存不连续，某些运行时要求连续） |

> **`[None, ...]` 和 `[:, None, None]` 是同一个技巧**——"插一个长度为 1 的新维度"。

## `[3]` 推理

```python
sess = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
outs = sess.run([o.name for o in sess.get_outputs()],
                {sess.get_inputs()[0].name: blob})
```

| 部分 | 作用 |
|---|---|
| `InferenceSession(...)` | **加载模型**（= 你的 `rknn.load_onnx` + `build` + `init_runtime`） |
| `providers=["CPUExecutionProvider"]` | 用 CPU 跑（PC 上没 NPU） |
| `sess.run(输出名, {输入名: 数据})` | **推理**——喂进去，拿输出 |

**`outs` 是 3 个数组：**
```
(1, 255, 80, 80)   (1, 255, 40, 40)   (1, 255, 20, 20)
```

## `[4]` 三个尺度收集 → 拼接

```python
all_boxes, all_scores, all_cls = [], [], []
for i, out in enumerate(outs):
    b, s, c = collect_one_scale(out, STRIDES[i], ANCHORS[i], CONF_THRESH)
    if len(b):
        all_boxes.append(b); all_scores.append(s); all_cls.append(c)

boxes      = np.concatenate(all_boxes)
scores     = np.concatenate(all_scores)
class_ids  = np.concatenate(all_cls)
```

| 写法 | 作用 |
|---|---|
| `enumerate(outs)` | 同时拿 **(下标 i, 元素 out)** |
| `STRIDES[i]` / `ANCHORS[i]` | 用下标从配置表取**对应**的参数 |
| `np.concatenate(...)` | 把三个 `(N,4)` **摞成一个** `(N总,4)` |

**结果：** `44` 个候选（6 + 24 + 14）

> **`np.concatenate` 和 `np.stack` 的区别**（容易混）：
> - `stack` = **加一维**：`[a(N,), b(N,)]` → `(N,2)`
> - `concatenate` = **接起来**：`[a(N,4), b(M,4)]` → `(N+M,4)`

## `[5]` 内容区过滤

```python
cx_all = (boxes[:, 0] + boxes[:, 2]) / 2
cy_all = (boxes[:, 1] + boxes[:, 3]) / 2
inside = ((cx_all >= pad_left) & (cx_all <= pad_left + content_w) &
          (cy_all >= pad_top)  & (cy_all <= pad_top  + content_h))
boxes, scores, class_ids = boxes[inside], scores[inside], class_ids[inside]
```

**为什么要这一步？** letterbox 填的灰边**在原图里不存在**，落在灰边上的框全是噪声。

```
      ┌──────────────┐
      │  灰边（没有画面）│  ← 框中心落在这一带 = 垃圾
      ├──────────────┤ y = pad_top
      │              │
      │   真正的画面   │  ← 只有这里面的框才可信
      │              │
      ├──────────────┤ y = pad_top + content_h
      │  灰边         │
      └──────────────┘
```

**用框的"中心"判断，不是用角点**——因为框可能跨过边界。

| 写法 | 说明 |
|---|---|
| `boxes[:, 0]` | 所有框的 x1（**切片保留二维**） |
| `(x1 + x2) / 2` | 框中心 x |
| `&` | **按位与**，处理数组的"且" |
| **每个条件都加括号** | 因为 `&` 的优先级比 `>=` 高 |

> ⚠️ **只能用 `&`，不能用 `and`**：`and` 只能处理单个布尔值，不能逐元素算。

**实测**：`44 → 44`（一个都没删）—— 说明经过 obj 过滤后，**剩下的候选全是正经货**。

## `[6]` NMS

```python
keep = nms(boxes, scores, IOU_THRESH)
boxes, scores, class_ids = boxes[keep], scores[keep], class_ids[keep]
order = scores.argsort()[::-1]
boxes, scores, class_ids = boxes[order], scores[order], class_ids[order]
```

| 行 | 作用 |
|---|---|
| `nms(...)` | **去重**：返回保留下来的**下标** |
| `boxes[keep]` | **花式索引**：用整数数组取出对应行 |
| `argsort()[::-1]` | 按分数**从高到低**排序 |

**结果：** `44 → 3`

> **`boxes[keep]` 和 `boxes[inside]` 都是"用数组当前标"**，
> 区别只是：一个是整数数组（选特定行），一个是布尔数组（按条件选）。

## `[7]` 反向映射回原图 ⭐

```python
ob = boxes.copy()
ob[:, [0, 2]] = (ob[:, [0, 2]] - pad_left) / r     # x1 和 x2
ob[:, [1, 3]] = (ob[:, [1, 3]] - pad_top ) / r     # y1 和 y2
ob[:, [0, 2]] = np.clip(ob[:, [0, 2]], 0, W0 - 1)
ob[:, [1, 3]] = np.clip(ob[:, [1, 3]], 0, H0 - 1)
```

**公式：**

```
x_原图 = (x_letterbox - pad_left) / r
y_原图 = (y_letterbox - pad_top ) / r
```

| 步骤 | 为什么 |
|---|---|
| `- pad` | 填的灰边在原图里**不存在**，坐标要从画面起点算 |
| `/ r` | 缩放时乘过 `r`，所以要除回来 |
| `clip` | 别让框跑出画面 |

**`[:, [0, 2]]` 这个写法：**

```
ob[:, [0, 2]]  →  取出所有行的第 0 列和第 2 列（x1 和 x2）
ob[:, [1, 3]]  →  第 1 列和第 3 列（y1 和 y2）
```

> **为什么 x 和 y 要分开写？** 因为 `pad_left` 和 `pad_top` 不一样，`x` 只减左填充，`y` 只减上填充。

**实测（test1.jpg 那个行人）：**

```
letterbox 坐标 (559.61, 398.76) - (603.89, 521.30)
                          ↓ 减 pad、除 r
原图坐标       (3582, 2041) - (3864, 2824)      ← 和 yolo_infer.py 完全一致
```

## `[8]` 画框 + 存图

```python
for i in range(len(ob)):
    x1, y1, x2, y2 = [int(v) for v in ob[i]]
    label = f"{nm} {scores[i]:.2f}"
    cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(vis, label, (x1 + 2, max(y1 - 6, 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
cv2.imwrite(out_path, vis)
```

| 行 | 注意 |
|---|---|
| `[int(v) for v in ...]` | `cv2.rectangle` 要**整数**坐标 |
| `(x1, y1), (x2, y2)` | ⚠️ **点是 `(x, y)` 顺序**（Day 11 的顺序陷阱） |
| `(0, 255, 0)` | **BGR 顺序**：绿 = `(0,255,0)` |
| `max(y1 - 6, 20)` | 别让文字跑出画面顶部 |
| `cv2.imwrite` | 存图（**失败返回 False，不抛异常**） |

---

# 五、数据流全景（跟着走一遍）

| 阶段 | 数据 | 形状/值 |
|---|---|---|
| 读图 | `img` | `(3072, 4096, 3)` |
| letterbox | `box` | `(640, 640, 3)` ＋ `r=0.1562, pad_top=80` |
| 转 blob | `blob` | `(1, 3, 640, 640)` |
| 推理 | `outs` | 3 个数组 `(1,255,80,80)` 等 |
| 拆通道 | `o` | `(3, 85, H, W)` |
| 解码 | `cx,cy,w,h` | 各 `(3, H, W)` |
| 置信度 | `conf` | `(3, H, W)` |
| 过滤+拉平 | `boxes` | `(N, 4)`，N=44 |
| 内容区过滤 | `boxes` | 还是 44 |
| NMS | `boxes` | **3** |
| 反向映射 | `ob` | `(3, 4)` 原图坐标 |
| 画框 | `vis` | 图上有 3 个绿框 |

---

# 六、这个文件的设计要点（值得记住的）

| # | 设计 | 好处 |
|---|---|---|
| 1 | **配置表 + 循环**（`STRIDES`/`ANCHORS`） | 一份代码处理三个尺度 |
| 2 | **单点 → 向量化 → 通用化** | 每一步都有验证，不会"改坏" |
| 3 | **同一个 `mask` 筛所有数据** | 三条数据一一对应，不会错位 |
| 4 | **`letterbox` 返回 `r/pad`** | 为最后"退货"留好凭证 |
| 5 | **函数职责单一** | `decode_scale` 只解码，`nms` 只去重，`collect_one_scale` 只管一个尺度 |
| 6 | **每阶段打印中间结果** | 出错时一眼看出在哪一步 |

---

# 七、如果想改，改哪里

| 想改什么 | 改哪里 |
|---|---|
| 换图片 | `IMG_PATH` |
| 换模型 | `MODEL_PATH` |
| 松/严一点 | `CONF_THRESH`（越低框越多） |
| 去重更狠 | `IOU_THRESH`（越低删得越狠） |
| 只画某一类 | 在 `[7]` 前面加 `class_ids == 某个类` 的筛选 |
| 把框里的图裁出来 | 在 `[7]` 里加 `img[y1:y2, x1:x2]` |
| 处理一整个目录 | 把 `[1]~[8]` 包成一个函数，外面套 `for path in files` |

> **最后一行就是下一步**：把 `[1]~[8]` 包成 `process_image(path)`，
> 外面套一个 `glob` 循环——**你就有了一个批量检测脚本**（Day 12 学过）。

---

# 八、一页总结

```
§0  import                → 工具
§1  letterbox()           → 保比例缩放 + 灰边，返回 r/pad（★ 退货凭证）
§2  三个函数（你写的）      → 解码 / IoU / NMS
§3  collect_one_scale()   → ★ 核心：一个尺度 → 一批框
                             ├ 去 batch → 拆通道 → 解码
                             ├ 中心宽高 → 左上右下
                             ├ conf = obj × max(cls)
                             └ mask 过滤 + stack 成 (N,4)
§4  主流程 [1]~[8]        → 读图 → letterbox → blob → 推理 →
                             收集×3 → 内容区过滤 → NMS →
                             反向映射 → 画框
```

> **这张图和教材第 10 章的流程图是同一件事**——
> 只是那里是"概念上的流程"，这里是"具体的代码"。
