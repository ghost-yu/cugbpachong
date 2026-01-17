import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
import time
import random

# --- 配置 ---
STUDENT_ID = os.environ.get("STUDENT_ID")
PASSWORD = os.environ.get("PASSWORD")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# 登录页 (您提供的那个长链接)
LOGIN_URL = "https://cas.cugb.edu.cn/login?service=https%3A%2F%2Fportal.cugb.edu.cn%2Fmanage%2Fcommon%2Fcas_login%2F30001%3Fredirect%3Dhttps%253A%252F%252Fportal.cugb.edu.cn"
# 目标成绩接口
TARGET_URL = "https://jwglxt.cugb.edu.cn/academic/studentcheckscore/studentCheckresultList.do"

def send_email(content):
    if not EMAIL_USER or not EMAIL_PASS:
        print("未配置邮箱，跳过发送")
        return
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = '【教务系统】成绩/审查结果通知'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER
    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")

def run():
    with sync_playwright() as p:
        # 启动浏览器，headless=True 表示无头模式（在服务器运行必须为 True）
        # args 参数是为了尽可能模拟真实浏览器，减少被封概率
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        # 修改 User-Agent 防止被识别为脚本
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("1. 访问登录页...")
            page.goto(LOGIN_URL)
            page.wait_for_load_state("networkidle")

            print("2. 填写账号密码...")
            page.fill("#username", STUDENT_ID)
            page.fill("#password", PASSWORD)
            time.sleep(1) # 稍作停顿，模拟人类

            # --- 核心：处理滑块验证码 ---
            print("3. 尝试拖动滑块...")
            try:
                # 定位滑块和滑轨
                slider = page.locator(".captcha-move-drag")
                slider_box = slider.bounding_box()
                
                # 您的 HTML 里容器 ID 是 j_digitPicture
                container = page.locator("#j_digitPicture")
                container_box = container.bounding_box()

                if slider_box and container_box:
                    # 计算鼠标起始位置（滑块中心）
                    start_x = slider_box["x"] + slider_box["width"] / 2
                    start_y = slider_box["y"] + slider_box["height"] / 2
                    
                    # 计算目标位置（向右拖动到容器边缘）
                    # 拖动距离 = 容器宽度 - 滑块宽度 + 一点余量
                    end_x = start_x + container_box["width"] - slider_box["width"]
                    
                    # 模拟鼠标动作
                    page.mouse.move(start_x, start_y)
                    page.mouse.down()
                    # 分段拖动，模拟人类的不匀速
                    steps = 10
                    for i in range(steps):
                        page.mouse.move(start_x + (end_x - start_x) * (i+1)/steps, start_y + random.randint(-2, 2))
                        time.sleep(random.uniform(0.01, 0.05))
                    
                    page.mouse.up()
                    print("   滑块拖动完成")
                    time.sleep(1) # 等待验证结果
                else:
                    print("   未找到滑块元素，可能无需验证或加载失败")

            except Exception as e:
                print(f"   滑块处理出错: {e}")

            print("4. 点击登录...")
            page.click("#enterBtn")
            
            # 等待跳转，如果成功，URL 应该会变或者出现登录后的元素
            page.wait_for_load_state("networkidle")
            time.sleep(5) # 给予充分的跳转时间

            # 验证是否登录成功 (检查 URL 是否跳转到了 portal 或 jwglxt)
            if "login" in page.url:
                print("登录失败：似乎还停留在登录页，可能是滑块验证未通过。")
                # 可以在这里截图调试：page.screenshot(path="debug.png")
                # 但 GitHub Actions 看不到图片，只能看 Log
                return

            print("5. 访问目标成绩页...")
            # 注意：教务系统通常需要先访问主页拿 Cookie，再访问具体接口
            # 我们先试着直接访问您提供的目标接口
            page.goto(TARGET_URL)
            time.sleep(3)
            
            content = page.content()
            
            # 6. 判断逻辑 (沿用之前的)
            # 如果包含 error_black 或 登录超时，说明没拿数据
            # 如果包含具体的课程名或不包含“暂无”，说明有结果
            print("6. 检查页面内容...")
            
            # 这里简单判断：如果页面里有 "暂无审查结果"
            if "暂无审查结果" in content:
                print("监控中：暂无结果")
            elif "error" in content or "登录" in content:
                print("监控失败：可能 Session 获取失败或未正确登录")
                print(f"页面摘要: {content[:100]}")
            else:
                print("!!! 发现变化 !!!")
                # 提取有用的文本发邮件
                text_content = page.locator("body").inner_text()
                send_email(f"监测到教务系统变化！\n\n页面文字摘要：\n{text_content[:500]}...")

        except Exception as e:
            print(f"运行出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
