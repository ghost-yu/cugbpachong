# 本地测试脚本
# 使用前请配置环境变量

# Windows PowerShell
$env:STUDENT_ID = "你的学号"
$env:PASSWORD = "你的密码"
$env:EMAIL_USER = "你的QQ邮箱@qq.com"
$env:EMAIL_PASS = "你的QQ邮箱授权码"

# 安装依赖
pip install selenium webdriver-manager pillow opencv-python numpy requests

# 运行测试（有头模式，可以看到浏览器）
python main_improved.py

# 如果要测试无头模式，修改 main_improved.py 第244行：
# 取消注释：chrome_options.add_argument("--headless=new")
