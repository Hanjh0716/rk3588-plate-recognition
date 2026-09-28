# 嵌入式 AI 车牌识别（RK3588）· 学习记录

```
第5层  应用层   车牌识别 + 云台 + 上位机        
第4层  算法层   检测 / 后处理 / 识别            
第3层  运行层   推理 / CPU / NPU                
第2层  格式层   ONNX / RKNN / 量化              
第1层  环境层   WSL2 / Python / 依赖管理        
```

## 这个仓库里有什么

### 📘 主线文档（建议按顺序读）

| 文档 | 内容 |
|---|---|
| [01-总路线图](docs/01-总路线图.md) | 整体规划、时间表、硬件采购策略 |
| [16-系统教材-从一张图到车牌号](docs/16-系统教材-从一张图到车牌号.md) | ⭐⭐ **主线教材**：10 章层层相扣，从"图像=数组"讲到"车牌号出来" |
| [15-项目全局地图](docs/15-项目全局地图.md) | ⭐⭐ 五层结构 + 每个知识点的"一句话本质" |
| [17-my_final逐段讲解](docs/17-my_final逐段讲解.md) | 自己写的那条流水线，逐段拆解 |

### 📗 分阶段教材

| 文档 | 阶段 |
|---|---|
| [02-Linux速查表](docs/02-Linux速查表.md) | 第 1 周：20 个常用命令 |
| [03-Python练习计划](docs/03-Python练习计划.md) | 第 2–3 周：14 天计划 |
| [04-NumPy入门](docs/04-NumPy入门.md) | 第 4 周：数组与向量化 |
| [06-OpenCV入门](docs/06-OpenCV入门.md) | 第 4 周：读图 / 缩放 / 画框 / 批处理 |
| [08-异常处理](docs/08-异常处理.md) | Day 13：try/except + traceback 阅读法 |
| [11-Python1-13天复习合集](docs/11-Python1-13天复习合集.md) | 复习：13 天压缩包 + 自测 20 题 |
| [12-目标检测与YOLO入门](docs/12-目标检测与YOLO入门.md) | 阶段①：检测输出 / 解码 / NMS / letterbox |

### 📙 环境与部署

| 文档 | 内容 |
|---|---|
| [00-安装说明](docs/00-安装说明.md) | WSL2 + Ubuntu + Python 环境 |
| [09-RKNN-Toolkit2环境安装](docs/09-RKNN-Toolkit2环境安装.md) | PC 端模型转换环境（含 10 个坑的解法） |
| [10-环境排查方法论](docs/10-环境排查方法论.md) | ⭐ 遇到环境问题该怎么想 |
| [14-模型格式与工具链](docs/14-模型格式与工具链.md) | ONNX / RKNN / Toolkit2 是什么 |
| [05-上板验机清单](docs/05-上板验机清单.md) | 板子到手先跑这个 |

### 📕 其他

| 文档 | 内容 |
|---|---|
| [13-毕业设计选题评估](docs/13-毕业设计选题评估.md) | 把项目延伸成毕设的可行性评估 |
| [07-后续学习与项目](docs/07-后续学习与项目.md) | 项目做完之后干什么 |
| [踩坑记录](docs/踩坑记录.md) | 每天记一条 |

### 💻 代码

```
practice/
├── 02-python/          Python 练习（OpenCV 演示、异常处理演示）
└── 04-rknn/
    ├── onnx2rknn.py    ONNX → RKNN 转换 + PC 仿真推理
    ├── yolo_inspect.py 看清模型输出的形状和数值范围
    ├── yolo_probe.py   看清 255 个通道的排布
    ├── yolo_infer.py   YOLO 推理 + 后处理（参考实现）
    ├── yolo_batch.py   批量体检
    ├── my_yolo.py      
    ├── my_nms.py       
    ├── my_nms2.py      
    └── my_final.py    
setup/                  一键环境安装脚本（Windows）
```

---



### 1.实现了完整的 YOLO 后处理

从模型的原始输出 `(1, 255, 80, 80)` 到图上的框，**每一环都是自己写的**：

```
拆通道 → 解码 → 置信度(obj × cls) → 内容区过滤 → NMS → 反向映射 → 画框
```

**验收方式**：和参考实现对比，结果**一字不差**：

```
参考实现:  person 0.9126 (3582,2041)-(3864,2824)
           car    0.7696 (1779,2150)-(2329,2616)
           car    0.6637 (1613,2198)-(1862,2458)

自己写的:  完全相同（12 个数字）
```

### 2. 一次真实的"实验设计错误"复盘

用一张**没有任何物体**的壁纸去测试"检测目标"的功能，得出"objectness 通道是坏的"这个**错误结论**；
换成真实照片后，结论完全反转。

> **测出来的结论，只在你测的那个条件下成立。**

完整记录见 [12-目标检测与YOLO入门](docs/12-目标检测与YOLO入门.md)。

### 3. 环境排查方法论

装 RKNN 工具链时踩的 10 个坑（conda ToS、`iJIT_NotifyEvent`、`onnx.mapping`、protobuf 冲突、execstack…），
每个都记了**现象 → 排查过程 → 根因 → 解法**。

---

## 技术栈

| 层 | 用到的东西 |
|---|---|
| 环境 | WSL2 / Ubuntu / conda / venv / pip |
| 语言 | Python / NumPy / OpenCV |
| 模型 | PyTorch(CPU) / ONNX / ONNX Runtime |
| 部署 | RKNN-Toolkit2 / librknnrt / rknn_toolkit_lite2 / INT8 量化 |
| 硬件 | Orange Pi 5 Plus（RK3588，6 TOPS NPU） |

---

## 学习路径（五层结构）

```
第5层  应用层    我要做一个什么系统？        车牌识别 + 云台伺服 + 上位机
第4层  算法层    怎么从图里找出车牌、读出字？ YOLO 检测 + LPRNet 识别
第3层  运行层    模型在哪跑、怎么拿结果？     onnxruntime / NPU / librknnrt
第2层  格式层    模型怎么变成硬件能执行的？   PyTorch → ONNX → RKNN
第1层  环境层    装在哪、怎么不打架？         WSL2 / Python 环境 / 依赖
```

**这五层从下往上依赖**——所以"低层的问题会伪装成高层的 bug"。
排查问题时**从下往上查**。

详见 [15-项目全局地图](docs/15-项目全局地图.md)。

---



## 环境安装（Windows）

1. 双击 `setup\1-安装WSL.bat` → 点"是" → 重启 → 设置 Ubuntu 用户名密码
2. 双击 `setup\2-配置Python环境.bat`
3. 双击 `setup\3-验证环境.bat`
4. 双击 `setup\4-备份环境.bat`（可选，能一键恢复）

详见 [00-安装说明](docs/00-安装说明.md)。

---

## 硬件

**已购**：Orange Pi 5 Plus 8GB + 64GB eMMC 模块 + M.2 WiFi6 模块
（RK3588 满血版，6 TOPS NPU，双 2.5G 网口、M.2 NVMe）

| 项目 | 参考价 |
|---|---|
| Orange Pi 5 Plus 8GB | ¥700–800 |
| 5V/4A 以上 Type-C 电源 | ¥40–60 |
| 散热片 + 风扇 | ¥30–60 |
| 32GB A2 microSD | ¥40 |
| USB 免驱摄像头 1080p | ¥100–200 |
| USB-TTL 串口模块（CH340 3.3V） | ¥15 |

**省钱方案**：二手（闲鱼）、先用手机当摄像头、4GB 代替 8GB。

---



---

## 说明

- 所有环境路径基于 **WSL2 Ubuntu**，用户名和路径请按自己的改
- 模型文件（`.onnx` / `.rknn`）和数据集**未包含**在本仓库（体积原因），需自行获取
- 文档里引用的参考数据来自 [rknn_model_zoo](https://github.com/airockchip/rknn_model_zoo) 官方 benchmark

---

