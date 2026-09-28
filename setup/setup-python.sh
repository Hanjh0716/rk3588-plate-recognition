#!/bin/bash
# ============================================================
#  在 Ubuntu (WSL) 中配置 Python 开发环境
#  由  2-配置Python环境.bat  自动调用
# ============================================================
set -u

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
info() { echo -e "${YELLOW}[..]${NC} $1"; }
err()  { echo -e "${RED}[错误]${NC} $1"; }

echo "=============================================================="
echo " 开始在 Ubuntu 中配置 Python 开发环境"
echo "=============================================================="
echo

# ---------- 1. 更新软件源 ----------
info "更新软件源 (需要你的 Ubuntu 密码)..."
if sudo apt-get update -qq; then ok "软件源更新完成"; else err "软件源更新失败，检查网络"; exit 1; fi
echo

# ---------- 2. 安装基础包 ----------
info "安装 python3 / pip / venv / git / 编译工具 ..."
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv python3-dev \
    git curl wget build-essential \
  && ok "基础包安装完成" \
  || { err "基础包安装失败"; exit 1; }
echo

# ---------- 3. 检查 Python 版本 ----------
PYVER=$(python3 --version 2>&1 | awk '{print $2}')
ok "Python 版本: $PYVER"
PYMAJ=$(echo "$PYVER" | cut -d. -f1)
PYMIN=$(echo "$PYVER" | cut -d. -f2)
if [ "$PYMAJ" -lt 3 ] || { [ "$PYMAJ" -eq 3 ] && [ "$PYMIN" -lt 10 ]; }; then
    err "Python 版本过低 (需要 >= 3.10)，后续装 PyTorch 会有问题"
    err "解决办法: 告诉我，我帮你配置 deadsnakes PPA 装新版"
else
    ok "Python 版本满足要求 (>= 3.10)，PyTorch / OpenCV 都没问题"
    echo "   提示: 以后装 RKNN-Toolkit2 时，它可能不支持最新版 Python。"
    echo "         到时候先看官方 GitHub 的 README 确认支持的版本，用 conda 或 PPA 单独装一个即可。"
    echo "         现在这个版本用来学 Python 和跑 PyTorch 完全够用。"
fi
echo

# ---------- 4. 创建项目目录 ----------
info "创建项目目录 ~/projects ..."
mkdir -p ~/projects ~/datasets
ok "已创建: ~/projects  (代码放这里) 和 ~/datasets (数据集放这里)"
echo "   注意: 代码一定要放在 WSL 内部，不要放 /mnt/d/ ，跨盘读写很慢"
echo

# ---------- 5. 建立虚拟环境 ----------
info "建立第一个虚拟环境 ~/projects/py-basics/.venv ..."
VENV_DIR=~/projects/py-basics
mkdir -p "$VENV_DIR"
if [ ! -d "$VENV_DIR/.venv" ]; then
    python3 -m venv "$VENV_DIR/.venv" && ok "虚拟环境创建完成" || { err "venv 创建失败"; exit 1; }
else
    ok "虚拟环境已存在，跳过"
fi
echo

# ---------- 6. 安装第一批库 ----------
info "在虚拟环境中安装 numpy + opencv (国内镜像加速)..."
PIP_CONF=~/.pip/pip.conf
mkdir -p ~/.pip
if [ ! -f "$PIP_CONF" ]; then
    printf '[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple\n' > "$PIP_CONF"
    ok "已配置清华 PyPI 镜像 (以后 pip 会快很多)"
fi

"$VENV_DIR/.venv/bin/pip" install -q --upgrade pip
"$VENV_DIR/.venv/bin/pip" install -q numpy opencv-python matplotlib
ok "numpy / opencv-python / matplotlib 安装完成"
echo

# ---------- 7. 把练习文件复制进 WSL ----------
if [ -d /mnt/d/FreeRTOS\ Worksapce/嵌入式AI-车牌识别/practice ]; then
    info "复制练习文件到 ~/projects/practice ..."
    mkdir -p ~/projects/practice
    cp -r /mnt/d/FreeRTOS\ Worksapce/嵌入式AI-车牌识别/practice/* ~/projects/practice/ 2>/dev/null
    find ~/projects/practice -name "*.py" -exec sed -i 's/\r$//' {} \; 2>/dev/null
    ok "练习文件已复制 (已修正换行符)"
else
    info "未找到练习文件目录，跳过 (不影响环境)"
fi
echo

# ---------- 8. 运行验证 ----------
echo "=============================================================="
echo " 环境就绪，正在自检..."
echo "=============================================================="
cd ~/projects/py-basics
"$VENV_DIR/.venv/bin/python" - <<'PYEOF'
import sys
print("  Python 路径 :", sys.executable)
print("  Python 版本 :", sys.version.split()[0])
try:
    import numpy as np
    print("  NumPy 版本  :", np.__version__)
except Exception as e:
    print("  [错误] NumPy 导入失败:", e)
try:
    import cv2
    print("  OpenCV 版本 :", cv2.__version__)
except Exception as e:
    print("  [错误] OpenCV 导入失败:", e)
PYEOF
echo
echo -e "${GREEN}=============================================================="
echo -e " 环境就绪！"
echo -e "==============================================================${NC}"
echo
echo " 以后每次开始写代码，先在终端敲:"
echo
echo "     cd ~/projects/py-basics && source .venv/bin/activate"
echo
echo " 看到命令行前面出现 (.venv) 就说明虚拟环境已激活。"
echo
