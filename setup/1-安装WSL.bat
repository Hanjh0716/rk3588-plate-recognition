@echo off
chcp 65001 >nul 2>&1
title 步骤1 - 安装 WSL2 和 Ubuntu
setlocal enabledelayedexpansion

REM ============================================================
REM  步骤1: 安装 WSL2 + Ubuntu
REM ============================================================

net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [!] 需要管理员权限，正在请求提权...
    echo      请在弹出窗口中点击 "是"
    echo.
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ================================================================
echo   步骤 1 / 3 : 安装 WSL2 + Ubuntu
echo ================================================================
echo.
echo  [前置检查]
echo.

REM ---------- 检查 Windows 版本 ----------
for /f "tokens=4-5 delims=. " %%i in ('ver') do set "WINVER=%%i.%%j"
echo   Windows 版本: %WINVER%
echo   (WSL2 需要 Windows 10 版本 2004 以上 / Windows 11)

REM ---------- 检查虚拟化 ----------
echo.
echo   正在检查 CPU 虚拟化支持...
systeminfo 2>nul | findstr /C:"Hyper-V" >nul 2>&1
if errorlevel 1 (
    echo   [提示] 未能从 systeminfo 读取虚拟化状态（可能权限不足），跳过此项检查。
) else (
    systeminfo 2>nul | findstr /C:"已启用虚拟化" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo   [警告] systeminfo 里没找到"已启用虚拟化"字样。
        echo          如果安装后 WSL 起不来，需要进 BIOS 打开:
        echo            Intel CPU  ->  Intel VT-x / Virtualization Technology
        echo            AMD   CPU  ->  SVM Mode
    ) else (
        echo   [OK] CPU 虚拟化已启用
    )
)

echo.
echo ================================================================
echo   即将安装:
echo     - 虚拟机平台 / WSL2 组件
echo     - 最新版 Ubuntu
echo.
echo   耗时: 约 5-15 分钟 (取决于网速)
echo   安装完成后必须重启电脑
echo ================================================================
echo.
pause

echo.
echo [1/2] 安装 WSL2 组件 + Ubuntu (一次完成, 不拆开)...
echo.
wsl --install
set "WSL_RC=%errorlevel%"

echo.
if not "%WSL_RC%"=="0" (
    echo   [警告] wsl --install 返回码: %WSL_RC%
    echo          如果上面提示需要重启或权限问题，属于正常现象。
    echo          如果提示"无法识别 wsl 命令"，说明系统太旧。
)
echo [2/2] 检查安装状态...
echo.
wsl --status 2>nul
wsl --list --verbose 2>nul

echo.
echo ================================================================
echo   安装命令已执行
echo ================================================================
echo.
echo  接下来:
echo    1. 【必须】重启电脑
echo.
echo    2. 重启后，从开始菜单打开 "Ubuntu"
echo       (如果没找到，等 1-2 分钟让 Windows 装完)
echo.
echo    3. 第一次打开会让你设置用户名和密码:
echo         Enter new UNIX username:  ^<- 英文小写, 例如 yun
echo         New password:             ^<- 屏幕不显示字符是正常的! 盲打后回车
echo         Retype new password:      ^<- 再输一遍
echo.
echo    4. 看到类似   yun@DESKTOP-XXX:~$   的提示符 = 成功
echo.
echo    5. 然后运行下一个脚本:  2-配置Python环境.bat
echo.
echo ================================================================
echo.
echo  如果卡住了，把上面的输出复制给我。
echo.
endlocal
pause
