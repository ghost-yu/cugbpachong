import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
import time
import random
import math

# --- 配置 ---
STUDENT_ID = os.environ.get("STUDENT_ID")
PASSWORD = os.environ.get("PASSWORD")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

LOGIN_URL = "https://cas.cugb.edu.cn/login?service=https%3A%2F%2Fportal.cugb.edu.cn%2Fmanage%2Fcommon%2Fcas_login%2F30001%3Fredirect%3Dhttps%253A%252F%252Fportal.cugb.edu.cn"
TARGET_URL = "https://jwglxt.cugb.edu.cn/academic/studentcheckscore/studentCheckresultList.do"

def send_email(subject, content):
    if not EMAIL_USER or not EMAIL_PASS:
        print("未配置邮箱，跳过发送")
        return
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = subject
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

# 生成人类行为轨迹（S型加速减速）
def get_track(distance):
    track = []
    current = 0
    mid = distance * 4 / 5
    t = 0.2
    v = 0
    
    while current < distance:
        if current < mid:
            a = 2  # 加速
        else:
            a = -3 # 减速
        v0 = v
        v = v0 + a * t
        move = v0 * t + 1 / 2 * a * t * t
        current += move
        track.append(round(move))
    return track

def run():
    with sync_playwright() as p:
        # 增加反爬参数
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ]
        )
        context = browser.new_context()
        # 注入 JS 脚本，隐藏 webdriver 特征（关键！）
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = context.new_page()

        try:
            print("1. 访问登录页...")
            page.goto(LOGIN_URL)
            page.wait_for_load_state("networkidle")

            print("2. 填写账号密码...")
            page.fill("#username", STUDENT_ID)
            page.fill("#password", PASSWORD)
            time.sleep(random.uniform(0.5, 1.5))

            print("3. 智能拖动滑块...")
            slider = page.locator(".captcha-move-drag")
            slider_box = slider.bounding_box()
            container = page.locator("#j_digitPicture")
            container_box = container.bounding_box()

            if slider_box and container_box:
                start_x = slider_box["x"] + slider_box["width"] / 2
                start_y = slider_box["y"] + slider_box["height"] / 2
                # 计算需要移动的总距离
                distance = container_box["width"] - slider_box["width"] + random.randint(2, 5) # 稍微多滑一点点

                page.mouse.move(start_x, start_y)
                page.mouse.down()
                
                # 获取模拟轨迹
                tracks = get_track(distance)
                
                # 开始移动
                current_x = start_x
                for step in tracks:
                    current_x += step
                    # 在 Y 轴加入微小抖动
                    current_y = start_y + random.randint(-2, 2)
                    page.mouse.move(current_x, current_y)
                    # 随机停顿，模拟网络波动或人手
                    time.sleep(random.uniform(0.01, 0.03))

                # 模拟滑过头了回退一点点
                page.mouse.move(current_x - 3, start_y)
                time.sleep(0.5)
                page.mouse.up()
                
                print("   滑块动作结束，等待验证...")
                time.sleep(2) 
            
            print("4. 点击登录...")
            page.click("#enterBtn")
            page.wait_for_load_state("networkidle")
            time.sleep(5) # 必须等待跳转

            # 截图保存，方便排查错误（见下一步骤）
            page.screenshot(path="debug_screenshot.png")

            if "login" in page.url:
                print("【失败】依然停留在登录页，截图已保存。")
                # 可以尝试发邮件把报错截图发给自己（需要更复杂的邮件代码），这里先只发文字
                # send_email("脚本报警：登录失败", "GitHub Actions 无法通过滑块验证，请检查 Actions Artifacts 查看截图。")
                return

            print("5. 登录成功！检查成绩...")
            page.goto(TARGET_URL)
            time.sleep(3)
            content = page.content()
            page.screenshot(path="result_screenshot.png")

            if "暂无审查结果" in content:
                print("--- 暂无结果 ---")
            elif "error" in content:
                print("--- 页面加载异常 ---")
            else:
                print("!!! 发现结果 !!!")
                text_info = page.locator("body").inner_text()
                send_email("【好消息】教务系统有变化！", f"检测到页面更新：\n{text_info[:200]}...")

        except Exception as e:
            print(f"运行出错: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
