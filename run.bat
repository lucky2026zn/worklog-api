@echo off
chcp 65001 >nul
title 工时记录系统 API

cd /d "C:\Users\nazha\Documents\New project_文件整理\worklog-api"

echo ============================================
echo   工时记录系统 API v1.0
echo ============================================
echo.

REM ---- 检测 Python ----
set PYTHON_CMD=
where python 2>nul >nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
) else (
    if exist "C:\Users\nazha\AppData\Local\Programs\Python\Python313\python.exe" (
        set PYTHON_CMD="C:\Users\nazha\AppData\Local\Programs\Python\Python313\python.exe"
    ) else (
        echo [失败] 找不到 Python！
        echo 请检查 Python 是否安装，或编辑 run.bat 修改路径
        pause
        exit /b
    )
)

echo 使用 Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM ---- 安装依赖 ----
echo [1/3] 安装依赖...
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [失败] 依赖安装出错，请手动运行：
    echo   %PYTHON_CMD% -m pip install flask flask-sqlalchemy flask-cors openpyxl
    pause
    exit /b
)
echo [完成] 依赖就绪
echo.

REM ---- 启动服务器 ----
echo [2/3] 启动服务器...
echo.
echo ============================================
echo   服务器地址: http://127.0.0.1:5000
echo.
echo   微信开发者工具中 app.js 设置:
echo     apiBaseUrl: "http://127.0.0.1:5000/api"
echo.
echo   真机测试: 换成电脑 IP（运行 ipconfig 查看）
echo.
echo   按 Ctrl+C 停止服务器
echo ============================================
echo.

%PYTHON_CMD% app.py

echo.
echo [失败] 服务器异常退出
pause