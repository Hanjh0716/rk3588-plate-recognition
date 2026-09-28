@echo off
chcp 65001 >nul 2>&1
title 步骤3 - 验证环境

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_WIN=%SCRIPT_DIR%verify.sh"

echo ================================================================
echo   步骤 3 / 3 : 验证环境是否安装成功
echo ================================================================
echo.

if exist "\\wsl$\Ubuntu\tmp\" (
    copy /Y "%SCRIPT_WIN%" "\\wsl$\Ubuntu\tmp\verify.sh" >nul 2>&1
    if errorlevel 1 goto :trywslpath
    goto :runcheck
)

:trywslpath
for /f "usebackq delims=" %%i in (`wsl -d Ubuntu -- wslpath -a "%SCRIPT_WIN%"`) do set "WSL_SCRIPT=%%i"
wsl -d Ubuntu -- cp "%WSL_SCRIPT%" /tmp/verify.sh
if errorlevel 1 (
    echo  [!] 脚本复制失败，请手动执行:
    echo      wsl -d Ubuntu -- cp "%SCRIPT_WIN%" /tmp/verify.sh
    echo      wsl -d Ubuntu -- bash /tmp/verify.sh
    echo.
    pause
    exit /b 1
)

:runcheck
wsl -d Ubuntu -- bash -lc "sed -i 's/\r$//' /tmp/verify.sh 2>/dev/null; bash /tmp/verify.sh"

echo.
echo ================================================================
echo  如果报告里有 [缺失]，把内容复制给我。
echo.
echo  全部就绪后，开始学习:
echo    1. 看  docs\02-Linux速查表.md          (第1周)
echo    2. 跟着 practice\02-python\ 的14天计划写代码
echo    3. 每天在 docs\踩坑记录.md 里记一条
echo ================================================================
pause
