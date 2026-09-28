#!/bin/bash
# ============================================================
#  环境自检脚本
#  由  3-验证环境.bat  自动调用
# ============================================================
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass=0
fail=0

chk_cmd() {
    if command -v "$1" >/dev/null 2>&1; then
        printf "  ${GREEN}[OK]${NC}    %-28s %s\n" "$2" "$(command -v "$1")"
        pass=$((pass+1))
    else
        printf "  ${RED}[缺失]${NC}  %-28s %s\n" "$2" "未安装"
        fail=$((fail+1))
    fi
}

chk_dir() {
    if [ -d "$1" ]; then
        printf "  ${GREEN}[OK]${NC}    %-28s %s\n" "$2" "$1"
        pass=$((pass+1))
    else
        printf "  ${RED}[缺失]${NC}  %-28s %s\n" "$2" "目录不存在"
        fail=$((fail+1))
    fi
}

echo "=============================================================="
echo "  环境自检报告"
echo "=============================================================="
echo
echo "-------- 命令检查 --------"
chk_cmd python3  "Python3"
chk_cmd pip3     "pip3"
chk_cmd git      "git"
chk_cmd gcc      "gcc / 编译工具"
chk_cmd sudo     "sudo"
chk_cmd code     "VS Code 命令行 (可选)"
echo
echo "-------- 目录检查 --------"
chk_dir "$HOME/projects"             "项目目录 ~/projects"
chk_dir "$HOME/projects/py-basics"   "练习目录 py-basics"
chk_dir "$HOME/projects/py-basics/.venv" "虚拟环境 .venv"
chk_dir "$HOME/datasets"             "数据集目录 ~/datasets"
echo
echo "-------- 版本信息 --------"
echo -n "  Python : "; python3 --version 2>&1 | awk '{print $2}'
echo -n "  git    : "; git --version 2>&1 | awk '{print $3}'
echo -n "  系统   : "; . /etc/os-release 2>/dev/null && echo "$PRETTY_NAME"
echo -n "  内存   : "; free -h 2>/dev/null | awk '/^Mem:/{print $2}'
echo -n "  磁盘   : "; df -h "$HOME" 2>/dev/null | awk 'NR==2{print $4" 可用 / "$2" 总计"}'
echo
echo "-------- 库导入测试 --------"
VENV_PY="$HOME/projects/py-basics/.venv/bin/python"
if [ -x "$VENV_PY" ]; then
    if $VENV_PY -c "import numpy" 2>/dev/null; then
        printf "  ${GREEN}[OK]${NC}    numpy   %s\n" "$($VENV_PY -c 'import numpy;print(numpy.__version__)')"
        pass=$((pass+1))
    else
        printf "  ${RED}[缺失]${NC}  numpy 导入失败\n"; fail=$((fail+1))
    fi
    if $VENV_PY -c "import cv2" 2>/dev/null; then
        printf "  ${GREEN}[OK]${NC}    opencv  %s\n" "$($VENV_PY -c 'import cv2;print(cv2.__version__)')"
        pass=$((pass+1))
    else
        printf "  ${RED}[缺失]${NC}  opencv 导入失败\n"; fail=$((fail+1))
    fi
    if $VENV_PY -c "import matplotlib" 2>/dev/null; then
        printf "  ${GREEN}[OK]${NC}    matplotlib %s\n" "$($VENV_PY -c 'import matplotlib;print(matplotlib.__version__)')"
        pass=$((pass+1))
    else
        printf "  ${YELLOW}[跳过]${NC}  matplotlib 未安装 (不影响)\n"
    fi
else
    printf "  ${RED}[缺失]${NC}  虚拟环境不存在，无法测试库\n"
    fail=$((fail+1))
fi
echo
echo "-------- Python 版本要求 --------"
PYMINOR=$(python3 -c 'import sys;print(sys.version_info.minor)')
if [ "$PYMINOR" -ge 10 ]; then
    printf "  ${GREEN}[OK]${NC}    Python 3.%s 满足要求 (需 >= 3.10)\n" "$PYMINOR"
    pass=$((pass+1))
else
    printf "  ${RED}[警告]${NC}  Python 3.%s 偏低，装 PyTorch 可能有问题\n" "$PYMINOR"
    fail=$((fail+1))
fi
echo
echo "=============================================================="
printf "  通过: %d   问题: %d\n" "$pass" "$fail"
if [ "$fail" -eq 0 ]; then
    echo -e "  ${GREEN}环境完全就绪！可以开始学习了。${NC}"
else
    echo -e "  ${YELLOW}存在未通过项，把上面的报告发给 AI 助手处理。${NC}"
fi
echo "=============================================================="
echo
echo "下次开始写代码，先执行:"
echo "    cd ~/projects/py-basics && source .venv/bin/activate"
echo
echo "然后用 VS Code 打开项目:"
echo "    code ~/projects/py-basics"
echo
