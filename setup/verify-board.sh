#!/bin/bash
# ============================================================
#  RK3588 开发板验机脚本（只读，不改系统配置）
#  适用: Orange Pi 5 Plus（RK3588）等 RK3588/RK3588S 板子
#
#  用法:
#     bash verify-board.sh              只读检查（先跑这个）
#     bash verify-board.sh --disk-test  额外做 512MB 写入测速（在 $HOME 临时写文件）
#
#  建议把输出存下来:
#     bash verify-board.sh | tee ~/verify-report.txt
#
#  出问题时把整段输出发给卖家/我，比说"板子坏了"有用一百倍。
# ============================================================
set -u

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
OK=0; WARN=0; BAD=0
DISK_TEST=0
[ "${1:-}" = "--disk-test" ] && DISK_TEST=1

ok()   { echo -e "  ${GREEN}[OK]${NC}    $1"; OK=$((OK+1)); }
warn() { echo -e "  ${YELLOW}[注意]${NC}  $1"; WARN=$((WARN+1)); }
bad()  { echo -e "  ${RED}[问题]${NC}  $1"; BAD=$((BAD+1)); }
info() { echo "          $1"; }
sec()  { echo; echo -e "${CYAN}===== $1 =====${NC}"; }
has()  { command -v "$1" >/dev/null 2>&1; }

# ---------- root 权限探测（NPU 版本、dmesg 需要 root）----------
CAN_ROOT=0
if [ "$(id -u)" -eq 0 ]; then
    SUDO=""; CAN_ROOT=1
elif sudo -n true >/dev/null 2>&1; then
    SUDO="sudo -n"; CAN_ROOT=1
else
    SUDO=""
fi
root_cat()  { [ "$CAN_ROOT" -eq 1 ] || return 1; $SUDO cat "$1" 2>/dev/null; }
dmesg_all() { if [ "$CAN_ROOT" -eq 1 ]; then $SUDO dmesg 2>/dev/null; else dmesg 2>/dev/null; fi; }

echo "=============================================================="
echo " RK3588 开发板验机报告"
echo " 时间: $(date '+%F %T')"
[ "$CAN_ROOT" -eq 0 ] && echo " 提示: 没有 root/免密 sudo，NPU 版本和 dmesg 检查会被跳过"
echo "=============================================================="

# ---------- 1. 板子身份 ----------
sec "1. 板子身份"
MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || true)
if [ -n "${MODEL:-}" ]; then ok "板子型号: $MODEL"; else warn "读不到 /proc/device-tree/model（可能不是 RK 官方 BSP 镜像）"; fi
info "主机名  : $(hostname)"
info "内核    : $(uname -r)  [$(uname -m)]"
if [ -f /etc/os-release ]; then
    info "系统    : $(. /etc/os-release; echo "${PRETTY_NAME:-未知}")"
fi
info "开机时长: $(uptime -p 2>/dev/null || uptime)"
case "${MODEL:-}" in
    *3588*) ok "确认是 RK3588 系列（NPU 6 TOPS 才对得上）" ;;
    "")     : ;;
    *)      warn "型号里没看到 3588: $MODEL" ;;
esac

# ---------- 2. CPU ----------
sec "2. CPU（RK3588 应为 8 核: 4×A76 + 4×A55）"
CORES=$(nproc 2>/dev/null || echo 0)
if [ "$CORES" -ge 8 ]; then ok "核心数: $CORES"; else bad "核心数只有 $CORES，应该是 8"; fi
has lscpu && lscpu | grep -iE 'model name|architecture' | sed 's/^/          /'
if [ -d /sys/devices/system/cpu/cpufreq ]; then
    for p in /sys/devices/system/cpu/cpufreq/policy*; do
        [ -e "$p/scaling_cur_freq" ] || continue
        cur=$(( $(cat "$p/scaling_cur_freq") / 1000 ))
        mx=$(( $(cat "$p/cpuinfo_max_freq" 2>/dev/null || echo 0) / 1000 ))
        gov=$(cat "$p/scaling_governor" 2>/dev/null || echo '?')
        info "$(basename "$p"): 当前 ${cur} MHz / 最高 ${mx} MHz / 调频器 $gov"
    done
else
    warn "没有 cpufreq 目录，内核可能没开调频"
fi

# ---------- 3. 内存 ----------
sec "3. 内存（8GB 版应显示约 7.6–7.9 GiB）"
if has free; then free -h | sed 's/^/          /'; fi
MEMG=$(awk '/MemTotal/{printf "%.1f", $2/1024/1024}' /proc/meminfo 2>/dev/null || echo 0)
info "MemTotal = ${MEMG} GiB"
if awk -v m="$MEMG" 'BEGIN{exit !(m>=7.0)}'; then
    ok "内存与 8GB 标称相符"
else
    bad "内存只有 ${MEMG} GiB —— 如果你买的是 8GB 版，这就是货不对板"
fi

# ---------- 4. 存储 ----------
sec "4. 存储（eMMC 64GB 对应 mmcblk* 约 57–58 GiB）"
has lsblk && lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,RO | sed 's/^/          /'
FOUND_MMC=0
for d in /sys/block/mmcblk*; do
    [ -e "$d/size" ] || continue
    FOUND_MMC=1
    gib=$(awk '{printf "%.1f", $1*512/1073741824}' "$d/size" 2>/dev/null)
    info "$(basename "$d") 容量 ${gib} GiB"
done
if [ "$FOUND_MMC" -eq 0 ]; then
    warn "没看到 mmcblk* 设备：插了 eMMC 模块就检查是否插到位；系统若装在 NVMe/SPI 上则属正常"
fi
for n in /sys/block/nvme*; do
    [ -e "$n/size" ] || continue
    gib=$(awk '{printf "%.1f", $1*512/1073741824}' "$n/size" 2>/dev/null)
    ok "NVMe SSD: $(basename "$n") 容量 ${gib} GiB（PCIe 3.0 x4，适合放数据集和模型）"
done
if [ -d /sys/class/mmc_host ]; then
    for m in /sys/class/mmc_host/mmc*/mmc*:*/name; do
        [ -e "$m" ] || continue
        info "存储芯片: $(cat "$m" 2>/dev/null)  ($(cat "$(dirname "$m")/type" 2>/dev/null))"
    done
fi
info "根分区  : $(df -h / | awk 'NR==2{print $1"  总 "$2"  已用 "$3"  可用 "$4}')"
MMCERR=$(dmesg_all | grep -icE 'mmc[0-9].*(error|timeout|fail)' || true)
if [ "${MMCERR:-0}" -gt 0 ]; then
    warn "dmesg 里 eMMC/SD 有 ${MMCERR} 条错误/超时（把原文记下来）"
    dmesg_all | grep -iE 'mmc[0-9].*(error|timeout|fail)' | tail -5 | sed 's/^/          /'
else
    ok "dmesg 里没看到 eMMC/SD 报错"
fi

if [ "$DISK_TEST" -eq 1 ]; then
    TMPF="$HOME/.verify-board-test.bin"
    info "写入 512MB 测速（测完自动删除）..."
    DDOUT=$(dd if=/dev/zero of="$TMPF" bs=1M count=512 conv=fdatasync 2>&1 | tail -1)
    rm -f "$TMPF"
    if [ -n "${DDOUT:-}" ]; then
        info "$DDOUT"
        SPEED=$(echo "$DDOUT" | grep -oE '[0-9.]+ [kMG]?B/s' | tail -1)
        ok "写入测速完成: ${SPEED:-见上面输出}（eMMC 一般 100+ MB/s，SD 卡 30–80 MB/s）"
    else
        bad "写入测速失败，存储可能有问题"
    fi
fi

# ---------- 5. 温度与散热 ----------
sec "5. 温度与散热"
MAXT=0
for z in /sys/class/thermal/thermal_zone*; do
    [ -e "$z/temp" ] || continue
    tC=$(awk -v x="$(cat "$z/temp" 2>/dev/null || echo 0)" 'BEGIN{printf "%.1f", x/1000}')
    info "$(basename "$z") [$(cat "$z/type" 2>/dev/null)] = ${tC} °C"
    MAXT=$(awk -v a="$MAXT" -v b="$tC" 'BEGIN{print (b>a)?b:a}')
done
if awk -v t="$MAXT" 'BEGIN{exit !(t>0)}'; then
    if awk -v t="$MAXT" 'BEGIN{exit !(t<65)}'; then
        ok "空闲最高温 ${MAXT} °C（很好）"
    elif awk -v t="$MAXT" 'BEGIN{exit !(t<80)}'; then
        warn "最高温 ${MAXT} °C 偏高，检查风扇是否在转、散热片是否贴合"
    else
        bad "最高温 ${MAXT} °C 过热，会降频，先把散热装好再测"
    fi
else
    warn "没有 thermal_zone，读不到温度"
fi
FAN=0
for c in /sys/class/thermal/cooling_device*; do
    [ -e "$c/type" ] || continue
    info "散热设备 $(basename "$c"): $(cat "$c/type" 2>/dev/null) 状态 $(cat "$c/cur_state" 2>/dev/null)/$(cat "$c/max_state" 2>/dev/null)"
    FAN=1
done
[ -d /sys/class/pwm ] && { info "PWM 通道: $(ls /sys/class/pwm | tr '\n' ' ')"; FAN=1; }
if [ "$FAN" -eq 0 ]; then
    warn "没看到风扇/PWM 设备。风扇要么没插好，要么需要手动开 PWM 控制（官方 Wiki 有「PWM 散热风扇」章节）"
fi

# ---------- 6. NPU ----------
sec "6. NPU（RKNPU，这块板子的核心价值）"
NPUVER=$(root_cat /sys/kernel/debug/rknpu/version || true)
if [ -n "${NPUVER:-}" ]; then
    ok "NPU 驱动: $NPUVER"
elif [ "$CAN_ROOT" -eq 0 ]; then
    warn "读 NPU 版本需要 root：用 sudo 重跑本脚本再确认"
else
    bad "读不到 /sys/kernel/debug/rknpu/version —— 内核没带 RKNPU 驱动，换官方镜像"
fi
NPULOAD=$(root_cat /sys/kernel/debug/rknpu/load || true)
[ -n "${NPULOAD:-}" ] && info "NPU 负载: $NPULOAD"
for f in /sys/class/devfreq/*npu*/cur_freq; do
    [ -e "$f" ] && info "$(basename "$(dirname "$f")") 频率: $(( $(cat "$f") / 1000000 )) MHz"
done
if [ -e /usr/lib/librknnrt.so ] || [ -e /usr/lib/aarch64-linux-gnu/librknnrt.so ]; then
    ok "librknnrt.so 存在（板端推理库已装）"
else
    warn "没找到 librknnrt.so —— 跑 .rknn 模型需要它（装 rknpu2 运行库）"
fi
has rknn_server && ok "rknn_server 存在" || info "没装 rknn_server（只有从 PC 连板推理时才需要）"
dmesg_all | grep -i rknpu | tail -3 | sed 's/^/          /'

# ---------- 7. GPU ----------
sec "7. GPU（Mali-G610）"
for f in /sys/class/devfreq/*gpu*/cur_freq; do
    [ -e "$f" ] && info "$(basename "$(dirname "$f")") 频率: $(( $(cat "$f") / 1000000 )) MHz"
done
dmesg_all | grep -iE 'mali|panfrost' | tail -3 | sed 's/^/          /'
if [ -e /dev/mali0 ]; then ok "/dev/mali0 存在"; else info "/dev/mali0 不存在（Server 版镜像可能没启用 GPU，不影响跑 NPU）"; fi

# ---------- 8. 网络 / WiFi / 蓝牙 ----------
sec "8. 网络 / WiFi / 蓝牙"
has ip && ip -br link | sed 's/^/          /'
WLAN=$(ls -d /sys/class/net/wlan* 2>/dev/null | head -1 || true)
if [ -n "${WLAN:-}" ]; then ok "无线网卡: $(basename "$WLAN")"; else warn "没有 wlan* 设备 —— 5 Plus 的 WiFi 是 M.2 E-Key 模块，先查模块是否插到底、天线是否接上，再看驱动"; fi
if has nmcli; then
    info "nmcli 设备状态:"
    nmcli -t -f DEVICE,TYPE,STATE device 2>/dev/null | sed 's/^/          /'
fi
if has iw; then iw dev 2>/dev/null | grep -E 'Interface|ssid|type' | sed 's/^/          /'; fi
has rfkill && { info "rfkill（有没有被软/硬开关关掉）:"; rfkill list 2>/dev/null | sed 's/^/          /'; }
if has bluetoothctl; then
    BTC=$(bluetoothctl show 2>/dev/null | grep -i '^Controller' | head -1 || true)
    if [ -n "${BTC:-}" ]; then ok "蓝牙: $BTC"; else warn "没看到蓝牙控制器"; fi
fi
has hciconfig && hciconfig -a 2>/dev/null | head -2 | sed 's/^/          /'
ETHS=$(ls -d /sys/class/net/eth* /sys/class/net/en* 2>/dev/null || true)
if [ -n "${ETHS:-}" ]; then
    ETHN=$(echo "$ETHS" | wc -l)
    if [ "$ETHN" -ge 2 ]; then ok "有线网口 ${ETHN} 个（5 Plus 应为 2 个 2.5G）"; else warn "只看到 ${ETHN} 个有线网口，5 Plus 应该有 2 个"; fi
    for e in $ETHS; do
        info "$(basename "$e")  carrier=$(cat "$e/carrier" 2>/dev/null)  (1=插着网线)"
        if has ethtool; then
            SP=$(ethtool "$(basename "$e")" 2>/dev/null | grep -i 'speed' | tr -d ' ' || true)
            [ -n "${SP:-}" ] && info "    $SP"
        fi
    done
else
    warn "没看到有线网口"
fi
if ping -c 2 -W 3 223.5.5.5 >/dev/null 2>&1; then
    ok "外网可达（ping 223.5.5.5）"
else
    warn "外网不通：先确认 WiFi/网线连上，再排查路由/DNS"
fi

# ---------- 9. USB / 显示 / 音频 / 摄像头 ----------
sec "9. USB / 显示 / 音频 / 摄像头"
if has lsusb; then info "USB 设备:"; lsusb | sed 's/^/          /'; else warn "没有 lsusb（sudo apt install -y usbutils）"; fi
for v in /dev/video*; do [ -e "$v" ] && info "摄像头节点: $v"; done
if [ -d /sys/class/drm ]; then
    for c in /sys/class/drm/card*-*; do
        [ -e "$c/status" ] || continue
        info "$(basename "$c"): $(cat "$c/status" 2>/dev/null)"
    done
fi
[ -d /sys/class/sound ] && info "声卡: $(ls /sys/class/sound | tr '\n' ' ')"
has aplay && aplay -l 2>/dev/null | grep -E '^card' | sed 's/^/          /'

# ---------- 10. 内核报错 ----------
sec "10. 内核报错扫描"
ERRS=$(dmesg_all | grep -icE 'error|failed|denied|timeout|panic|oops' || true)
if [ "${ERRS:-0}" -eq 0 ]; then
    ok "dmesg 里没有明显错误"
else
    warn "dmesg 里有 ${ERRS} 条含 error/failed/timeout 的日志（别慌，WiFi/蓝牙探测失败很常见，下面是最新 10 条）"
    dmesg_all | grep -iE 'error|failed|denied|timeout|panic|oops' | tail -10 | sed 's/^/          /'
fi

# ---------- 汇总 ----------
sec "验机汇总"
echo "  [OK] $OK 项    [注意] $WARN 项    [问题] $BAD 项"
echo
if [ "$BAD" -gt 0 ]; then
    echo -e "  ${RED}有硬性问题。把上面 [问题] 那几项的原文复制下来，先联系卖家换货（7 天内最省事）。${NC}"
elif [ "$WARN" -gt 0 ]; then
    echo -e "  ${YELLOW}没有硬性失败，[注意] 项多数能靠散热/配置解决。${NC}"
else
    echo -e "  ${GREEN}全绿。${NC}"
fi
echo
echo "  脚本查不了、必须手动做的三件事:"
echo "    1) 用 NPU 真跑一次模型看 FPS 和温度（rknn_model_zoo 的 yolov8 demo）"
echo "    2) 逐个插一遍 USB 口 / HDMI / 摄像头，看有没有不认的"
echo "    3) 烤机 30 分钟: sudo apt install -y stress-ng && stress-ng --cpu 8 --timeout 1800s"
echo
echo "  留档: bash verify-board.sh | tee ~/verify-report.txt"
echo "  然后记一条到 docs/踩坑记录.md"
exit 0
