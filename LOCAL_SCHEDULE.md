# 本地定时任务方案
# 使用Windows任务计划程序，每30分钟自动运行

# 1. 创建批处理文件 run_monitor.bat
@echo off
cd /d G:\2353\cugbpachong
call .venv\Scripts\activate
set STUDENT_ID=你的学号
set PASSWORD=你的密码
set EMAIL_USER=你的邮箱
set EMAIL_PASS=你的授权码
python main_undetected.py
pause

# 2. 设置Windows任务计划
# - 打开"任务计划程序"
# - 创建基本任务
# - 触发器：每30分钟
# - 操作：启动程序 -> run_monitor.bat
# - 条件：计算机空闲时不运行
