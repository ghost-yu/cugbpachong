@echo off
echo ============================================
echo 成绩监控系统 - 本地运行版
echo ============================================
echo.

cd /d G:\2353\cugbpachong

echo [1/4] 检查虚拟环境...
if not exist "g:\2353\.venv\Scripts\python.exe" (
    echo 错误: 虚拟环境不存在
    echo 请先运行: python -m venv g:\2353\.venv
    pause
    exit /b 1
)

echo [2/4] 激活虚拟环境...
call g:\2353\.venv\Scripts\activate.bat

echo [3/4] 安装/更新依赖...
pip install -q undetected-chromedriver requests

echo [4/4] 运行监控程序...
echo.
set STUDENT_ID=1005241118
set PASSWORD=1234Qwer@
set EMAIL_USER=1754932055@qq.com
set EMAIL_PASS=ffzyyrnsztamcghd

python main_undetected.py

echo.
echo ============================================
echo 运行完成
echo ============================================
pause
