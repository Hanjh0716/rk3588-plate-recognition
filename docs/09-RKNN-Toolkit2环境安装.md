# RKNN-Toolkit2 环境安装（PC 端模型转换）

> **目的**：在这台电脑的 WSL 里装好模型转换工具，把 YOLO 的 ONNX 转成 `.rknn`。
>
> **重点**：这是**纯电脑上的活，不需要板子**（转换 + 仿真推理都能在 PC 上跑完）。所以它完全符合你路线图里"先零成本在电脑上练到有把握"的原则。

---

## 0. 三个硬约束（先看，能省你半天）

| 约束 | 说明 |
|---|---|
| **装在哪** | **只能装在 WSL/Ubuntu（x86_64 Linux）**。Windows 原生 Python 装不了——官方只有 Linux 版 |
| **系统与 Python** | 官方支持：Ubuntu 18.04(3.6/3.7)、20.04(3.8/3.9)、**22.04(3.10/3.11)**、24.04(3.12) |
| **版本必须对齐** | 板端 `librknnrt` 是 **2.3.0**（你已验证）→ PC 端也装 **2.3.0** |

**你的情况**：WSL 里系统 Python 是 **3.14**（太新，官方不支持）→ **必须单独建一个 3.10 环境**，别动 `py-basics`。

---

## 1. 安装：conda 路线（推荐）

### ① 装 miniconda（走清华镜像，快）

```bash
wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p ~/miniconda3
~/miniconda3/bin/conda init bash
exec bash                     # 让 conda 生效（或重开终端）
conda --version
```

> 如果上面的 wget 404，就去 <https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/> 手动找最新版。

### ② 给 conda 配国内源

```bash
cat > ~/.condarc << 'EOF'
channels:
  - defaults
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
show_channel_urls: true
EOF
conda config --show channels
```

### ③ 建 Python 3.10 环境

```bash
conda create -n rknn python=3.10 -y
conda activate rknn
python -V                     # 必须是 3.10.x
```

### ④ 先装 PyTorch **CPU 版**（关键，别跳过）

```bash
conda install -y pytorch==2.2.0 torchvision cpuonly -c pytorch
python -c "import torch; print(torch.__version__)"
```

> **为什么必须先装它**：`rknn-toolkit2` 依赖 `torch<=2.2.0`。如果让 pip 自己去 PyPI 拉，会下一个**带 CUDA 的巨型包（1–2GB）**，而且你根本用不到显卡。
> 走 conda 的 `cpuonly` 只要 ~200MB。

### ⑤ 装 RKNN-Toolkit2

```bash
pip install rknn-toolkit2==2.3.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
pip show rknn-toolkit2 | head -3
```

**磁盘占用**：conda 环境 + 依赖一共约 **2–3GB**。装之前先看空间：

```bash
df -h ~        # 建议至少留 10GB
```

---

## 2. 验证（三步，全在 PC 上）

```bash
# ① 能导入
conda activate rknn
python -c "from rknn.api import RKNN; print('rknn-toolkit2 导入成功')"

# ② 能看到版本
pip show rknn-toolkit2 | grep -i version

# ③ 建一个 RKNN 对象（工具链真正初始化）
python -c "from rknn.api import RKNN; r=RKNN(); print('RKNN 对象创建成功')"
```

三步都过 = 环境装好了。

---

## 3. 第一个练习：ONNX → RKNN + **仿真推理**

这是第 6 周的核心技能。**全程不需要板子**：工具链可以在 PC 上模拟 NPU 跑推理。

### ① 拿一个 ONNX（国内 CDN，不用翻墙）

```bash
mkdir -p ~/projects/rknn/model && cd ~/projects/rknn/model
wget https://ftrg.zbox.filez.com/v2/delivery/data/95f00b0fc900458ba134f8b180b3f7a1/examples/yolov5/yolov5s.onnx
ls -lh
```

### ② 转换 + 仿真

用 `practice/04-rknn/onnx2rknn.py`（已写好，含逐行注释）：

```bash
conda activate rknn
python3 /mnt/d/嵌入式AI-车牌识别/practice/04-rknn/onnx2rknn.py ~/projects/rknn/model/yolov5s.onnx
```

**期望输出**：生成 `yolov5s_rk3588.rknn`，并打印出输出张量的形状（仿真推理成功）。

### ③ 把 `.rknn` 拷到板子上跑（等有网络时）

```bash
scp ~/projects/rknn/model/yolov5s_rk3588.rknn orangepi@板子IP:~/
```

---

## 4. 依赖里两个会咬你的坑

| 坑 | 说明 |
|---|---|
| `numpy<=1.26.4` | 别手动 `pip install -U numpy` 升到 2.x，否则工具链会崩 |
| `torch<=2.2.0` | 别装最新 torch。**先在 conda 里装好 CPU 版 2.2.0**，再让 pip 装 toolkit2 |

另外注意工具链内部还固定了：`protobuf==3.20.3`、`onnx==1.14.1`、`onnxruntime==1.16.0`、`onnxoptimizer==0.3.8`。**这些版本是配套的，别自己乱升。**

---

## 5. 常见报错

| 报错 | 原因 | 解决 |
|---|---|---|
| `Could not find a version that satisfies the requirement rknn-toolkit2` | Python 版本不被支持（你是 3.14） | `python -V` 确认在 conda 的 3.10 环境里 |
| 装完 import 报 `ImportError: libxxx.so` | 缺系统库 | `sudo apt install -y libgl1 libglib2.0-0` |
| `RuntimeError: ... glibc ...` / 各种诡异崩溃 | 你的 Ubuntu 版本太新（26.04），不在官方测试列表 | **备选方案**：在 WSL 里加装一个官方支持的发行版：`wsl --install -d Ubuntu-22.04`（系统自带 Python 就是 3.10，最省心） |
| `build` 阶段报算子不支持 | 模型里有 NPU 不支持的算子 | 这正是第 6 周要解决的**核心问题**，见 `docs/01-总路线图.md` 第 6 周 |
| INT8 量化精度掉太多 | 校准集不具代表性 | 换 100–300 张和实际场景接近的图片做校准 |
| **`ModuleNotFoundError: No module named 'pkg_resources'`** | rknn-toolkit2 **漏声明了 setuptools 依赖**（代码里 `import pkg_resources`，但那个模块是 setuptools 提供的） | `pip install "setuptools<81"`（写 `<81` 是因为 `pkg_resources` 在新版 setuptools 里已被废弃、将来会删） |
| **`AttributeError: module 'onnx' has no attribute 'mapping'`** | `onnx` 版本比工具链要求的**新**（新版删掉了 `onnx.mapping`） | `pip install "onnx==1.14.1"` —— 工具链测试过的就是这一版 |
| **`pip ... dependency conflicts ... protobuf`** | 工具链实际要 `protobuf>=4.21.6,<=4.25.4`，而老文档/PyPI 元数据写的是 3.20.3 | `pip install "protobuf>=4.21.6,<=4.25.4"`。**注意：pip 那句 `ERROR:` 常常只是警告**，要读它给出的具体要求 |
| **`ImportError: ... cannot enable executable stack as shared object requires: Invalid argument`** | `onnxruntime 1.16.0` 的 `.so` 带"可执行栈"标记，**新内核/WSL2 加载器拒绝** | 清掉标记：`sudo apt install -y patchelf && patchelf --clear-execstack <那个 .so>`（或 `execstack -c <so>`）。对功能无影响 |
| **`ValueError: The input(ndarray) shape (1,3,640,640) is wrong, expect 'nhwc' like (1,640,640,3)`** | RKNN 的 `inference()` **默认 `data_format='nhwc'`**，而 ONNX/PyTorch 用的是 NCHW | 喂进去之前转一次：`x = np.transpose(x, (0, 2, 3, 1))`；或显式传 `rknn.inference(inputs=[x], data_format='nchw')` |
| **`E init_runtime: RKNN model that loaded by 'load_rknn' not support inference on the simulator, please set 'target' first!`** | **`load_rknn` 加载的是编译产物，仿真只支持 `load_xxx → build` 的同一个会话** | 想在 PC 上验证，就走完整流程（`load_onnx` → `build` → `inference`）；`.rknn` 文件本身没问题，只是不能在 PC 上跑，要上真机 |

> **RKNN 的两种流程，别混**：
> - **转换 + 仿真**（PC）：`load_onnx` → `build` → `init_runtime()` → `inference()` —— 全在**同一个进程**里
> - **部署**（板子/真机）：`load_rknn` → `init_runtime(target='rk3588')` → `inference()` —— 只吃编译好的 `.rknn`
| **`ImportError: .../torch/lib/libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent`** | conda 装的 torch 和它拿到的 `mkl` 版本不配套（`iJIT_*` 是 Intel VTune 的分析接口，用不到但必须先解析） | 见下面「两个已验证的绕法」 |

### 两个已验证的绕法（`iJIT_NotifyEvent`）

**绕法 A：补一个空壳库（不用下载，30 秒）** —— 前提是有 gcc

```bash
conda activate rknn
cat > /tmp/itt_stub.c << 'EOF'
void iJIT_NotifyEvent(void) {}
void iJIT_NotifyEventW(void) {}
int  iJIT_IsProfilingActive(void) { return 0; }
int  iJIT_GetNewMethodID(void) { return 1; }
int  iJIT_GetNewMethodIDEx(void) { return 1; }
EOF
gcc -shared -fPIC -O2 -o "$CONDA_PREFIX/lib/libittnotify.so" /tmp/itt_stub.c
export LD_PRELOAD="$CONDA_PREFIX/lib/libittnotify.so"
python -c "import torch; print('torch ok', torch.__version__)"
```

做成永久（激活环境时自动生效，只影响这个环境）：

```bash
mkdir -p "$CONDA_PREFIX/etc/conda/activate.d" "$CONDA_PREFIX/etc/conda/deactivate.d"
cat > "$CONDA_PREFIX/etc/conda/activate.d/itt_preload.sh" << 'EOF'
export _OLD_LD_PRELOAD="${LD_PRELOAD:-}"
export LD_PRELOAD="$CONDA_PREFIX/lib/libittnotify.so${LD_PRELOAD:+:$LD_PRELOAD}"
EOF
cat > "$CONDA_PREFIX/etc/conda/deactivate.d/itt_preload.sh" << 'EOF'
export LD_PRELOAD="$_OLD_LD_PRELOAD"
unset _OLD_LD_PRELOAD
EOF
```

**绕法 B：把 conda 的 torch 换成 pip 的 CPU 版**（更干净，但要下几百 MB）

```bash
pip uninstall -y torch torchvision
pip install torch==2.2.0 torchvision==0.17.0 --index-url https://download.pytorch.org/whl/cpu
```

来源：[Anaconda 官方论坛讨论](https://forum.anaconda.com/t/linux-conda-importerror-undefined-symbol-ijit-notifyevent-when-importing-pytorch-in-a-conda-env-fix-without-vtune/107794)（多个用户确认有效）

---

## 6. 环境分层（你现在有三个环境，别混）

| 环境 | Python | 干什么 |
|---|---|---|
| `~/projects/py-basics/.venv` | 3.14 | 学 Python / OpenCV 的练习，**继续用，别动** |
| **conda `rknn`** | **3.10** | **模型转换 + 仿真推理（本文档）** |
| 板子自带 | 3.8 | `rknn_toolkit_lite2`，只管推理 |

**规矩**：`conda activate rknn` 之后才做转换；`source .venv/bin/activate` 之后才做 Python 练习。**两边不要互相装包。**

---

## 7. 装完之后

1. 回到 `docs/01-总路线图.md`，把"环境分层"里的 `rknn` 环境打勾
2. 下一步就是第 5 周：用 YOLO 在电脑上跑通车牌检测（这需要 `torch` + `ultralytics`，正好也在 `rknn` 这个环境里装）
3. 第 6 周：ONNX → RKNN、INT8 量化、精度对比
