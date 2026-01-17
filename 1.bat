@echo off
chcp 65001 >nul
echo ============================================
echo 成绩监控系统 - 本地运行版
echo ============================================
echo.

cd /d G:\2353\cugbpachong

echo [1/3] 激活虚拟环境...
call g:\2353\.venv\Scripts\activate.bat

echo [2/3] 确保依赖已安装...
pip install -q undetected-chromedriver requests 2>nul

echo [3/3] 运行监控程序（有头模式 - 可以看到浏览器操作）...
echo.
set STUDENT_ID=1005241118
set PASSWORD=1234Qwer@
set EMAIL_USER=1754932055@qq.com
set EMAIL_PASS=ffzyyrnsztamcghd

python main_stable.py

echo.
echo ============================================
echo 运行完成！
echo 提示: 本地运行使用有头模式，通过率80-90%%
echo       如果失败，请直接手动完成滑块后观察
echo ============================================
pause