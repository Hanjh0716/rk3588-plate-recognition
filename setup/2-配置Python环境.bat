@echo off
chcp 65001 >nul 2>&1
title 步骤2 - 配置 Python 环境

echo ================================================================
echo   步骤 2 / 3 : 在 Ubuntu 中配置 Python 环境
echo ================================================================
echo.
echo  前提: 你已经完成步骤1，并且已经重启电脑、设置好 Ubuntu 用户名
echo.
echo  下面的命令会:
echo    - 更新软件源
echo    - 安装 python3 / pip / venv / git
echo    - 安装编译工具 build-essential
echo    - 创建项目目录  ~/projects
echo    - 建立第一个虚拟环境并安装 numpy + opencv
echo.
echo  过程中会要求输入你的 Ubuntu 密码 (sudo 密码)
echo  输入时屏幕不显示字符，这是正常的，盲打后回车即可
echo.
echo ================================================================
echo.
pause

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_WIN=%SCRIPT_DIR%setup-python.sh"

echo [1/2] 把配置脚本复制到 Ubuntu 中...
if exist "\\wsl$\Ubuntu\tmp\" (
    copy /Y "%SCRIPT_WIN%" "\\wsl$\Ubuntu\tmp\setup-python.sh" >nul 2>&1
    if errorlevel 1 goto :trywslpath
    echo   方式A 成功
) else (
    goto :trywslpath
)
goto :runscript

:trywslpath
echo   方式A 不可用，尝试方式B (wslpath)...
for /f "usebackq delims=" %%i in (`wsl -d Ubuntu -- wslpath -a "%SCRIPT_WIN%"`) do set "WSL_SCRIPT=%%i"
wsl -d Ubuntu -- cp "%WSL_SCRIPT%" /tmp/setup-python.sh
if errorlevel 1 (
    echo.
    echo  [!] 两种复制方式都失败了。
    echo.
    echo  请手动执行下面两步 (在普通的 PowerShell 或 CMD 窗口里):
    echo.
    echo     wsl -d Ubuntu -- cp "%SCRIPT_WIN%" /tmp/setup-python.sh
    echo     wsl -d Ubuntu -- bash /tmp/setup-python.sh
    echo.
    pause
    exit /b 1
)
echo   方式B 成功

:runscript
echo.
echo [2/2] 开始执行配置...
echo.
wsl -d Ubuntu -- bash -lc "sed -i 's/\r$//' /tmp/setup-python.sh 2>/dev/null; bash /tmp/setup-python.sh"

echo.
echo ================================================================
echo   步骤2 执行完毕
echo ================================================================
echo.
echo  如果上面看到 "环境就绪" 字样，说明成功了。
echo  如果没有，把报错内容复制到 docs\踩坑记录.md 里，再告诉我。
echo.
echo  下一步: 运行  3-验证环境.bat
echo.
echo ================================================================
pause
