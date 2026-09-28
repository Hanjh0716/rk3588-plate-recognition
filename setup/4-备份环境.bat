@echo off
chcp 65001 >nul 2>&1
title 备份环境配置

echo ================================================================
echo   备份你的 Ubuntu 环境配置
echo ================================================================
echo.
echo  作用: 万一以后配坏了，可以一条命令恢复，不用重装
echo  输出: 本目录下的 ubuntu-backup.tar
echo.
pause

echo.
echo 正在备份 (可能需要几分钟)...
wsl --export Ubuntu "%~dp0ubuntu-backup.tar"

if %errorlevel%==0 (
    echo.
    echo [成功] 备份完成: ubuntu-backup.tar
    echo.
    echo  这个文件会比较大 (1-3 GB)，属于正常。
    echo  恢复方法:  wsl --import Ubuntu D:\WSL\Ubuntu "%~dp0ubuntu-backup.tar"
) else (
    echo.
    echo [失败] 备份未完成，请确认 Ubuntu 已安装且没有正在运行的错误。
)
echo.
pause
