import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
import time

# 从 GitHub Secrets 获取配置
STUDENT_ID = os.environ.get("STUDENT_ID")
PASSWORD = os.environ.get("PASSWORD")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# 目标成绩接口 (从您提供的 HTML 分析出来的)
TARGET_URL = "https://jwglxt.cugb.edu.cn/academic/studentcheckscore/studentCheckresultList.do"

def send_email(content):
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = '【重要】教务系统成绩/审查结果更新提醒'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER  # 发给自己

    try:
        # 这里以 QQ 邮箱为例，如果是 Gmail 用 smtp.gmail.com
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")

def run():
    with sync_playwright() as p:
        # 启动无头浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("1. 开始访问登录页...")
        page.goto("https://jwglxt.cugb.edu.cn")

        # --- 这里的选择器可能需要根据实际页面调整 ---
        # 尝试等待输入框出现
        try:
            # 常见的教务系统输入框选择器，如果不奏效，请按 F12 查看实际 ID
            page.wait_for_selector("input[name='j_username']", timeout=10000)
            
            print("2. 输入账号密码...")
            page.fill("input[name='j_username']", STUDENT_ID)
            page.fill("input[name='j_password']", PASSWORD)
            
            # 点击登录按钮 (假设是一个 type=submit 的按钮或者 id=loginButton)
            # 如果点击没反应，可能需要换成 page.click("#loginButton")
            page.click("input[type='submit']") 
            
            # 等待登录完成（等待 URL 变化或页面特定元素出现）
            page.wait_for_load_state("networkidle")
            
        except Exception as e:
            print(f"登录过程出错 (可能是选择器不对): {e}")
            browser.close()
            return

        print("3. 登录成功，访问目标接口...")
        # 直接访问那个 ajax 请求的地址，或者通过界面点击进入
        # 这里尝试直接访问那个审查结果的页面
        page.goto(TARGET_URL)
        
        # 等待内容加载
        time.sleep(5) 
        content = page.content()

        # 4. 判断逻辑
        # 您提供的 HTML 里说：如果没有结果，会有 "暂无审查结果" 或者 "error_top" 等类名
        # 我们这里反向判断：如果页面里包含了具体的课程名，或者不包含“暂无”，就报警
        
        print("4. 检查页面内容...")
        # 简单粗暴逻辑：如果页面长度大于某个值，或者不包含“暂无”二字
        if "暂无审查结果" not in content and "error_black" not in content:
            # 这里需要根据实际没有成绩时的页面微调
            # 比如，如果出现了 "通过" 或者 "分数" 字样
            print("!!! 发现变化，可能出成绩了 !!!")
            send_email(f"教务系统可能有新成绩/结果发布。\n\n当前页面包含信息摘要：\n{content[:200]}...")
        else:
            print("监控中：暂无新结果。")

        browser.close()

if __name__ == "__main__":
    run()
