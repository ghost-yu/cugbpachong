import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
# 必须引入 stealth
from playwright_stealth import stealth_sync
import time
import random

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

# 更加平滑的仿真轨迹算法
def mouse_slide(page, start_x, start_y, end_x, end_y):
    # 1. 鼠标先移动到起点 (模拟人类寻找滑块的过程)
    page.mouse.move(start_x, start_y, steps=10)
    time.sleep(0.2)
    page.mouse.down()
    
    # 2. 计算距离
    distance = end_x - start_x
    steps = random.randint(25, 35) # 步数更多，更细腻
    
    for i in range(steps):
        # 缓动函数：先快后慢
        progress = i / steps
        # easeOutQuad 算法
        move_x = start_x + distance * (1 - (1 - progress) * (1 - progress))
        
        # Y轴微小抖动
        move_y = start_y + random.uniform(-3, 3)
        
        page.mouse.move(move_x, move_y)
        time.sleep(random.uniform(0.01, 0.03))
    
    # 3. 滑到终点后稍微停顿
    page.mouse.move(end_x, end_y)
    time.sleep(0.5)
    page.mouse.up()

def run():
    with sync_playwright() as p:
        # 启动参数优化
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1920,1080"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # --- 关键：开启隐身模式 ---
        page = context.new_page()
        stealth_sync(page) 

        try:
            print("1. 访问登录页...")
            page.goto(LOGIN_URL)
            page.wait_for_load_state("networkidle")
            
            # 确保页面元素加载完毕
            page.wait_for_selector("#username", state="visible")
            
            print("2. 填写账号密码...")
            page.fill("#username", STUDENT_ID)
            page.fill("#password", PASSWORD)
            time.sleep(1)

            # 重试机制：如果第一次没滑成功，再试一次
            for attempt in range(2):
                print(f"3. 处理滑块 (第 {attempt+1} 次尝试)...")
                
                slider = page.locator(".captcha-move-drag")
                container = page.locator("#j_digitPicture")
                
                # 强制等待滑块可见
                if not slider.is_visible():
                    print("   滑块不可见，可能无需验证或页面加载失败")
                    break

                slider_box = slider.bounding_box()
                container_box = container.bounding_box()

                if slider_box and container_box:
                    start_x = slider_box["x"] + slider_box["width"] / 2
                    start_y = slider_box["y"] + slider_box["height"] / 2
                    end_x = start_x + container_box["width"] - slider_box["width"]
                    
                    # 执行滑动
                    mouse_slide(page, start_x, start_y, end_x, start_y)
                    
                    # 等待验证结果
                    time.sleep(2)
                    
                    # 检查是否出现成功标志（通常成功后滑块上的文字会变，或者出现对勾）
                    # 这里通过判断是否还在登录页来侧面验证
                    page.click("#enterBtn")
                    time.sleep(3) # 等待跳转
                    
                    if "login" not in page.url:
                        print("   验证成功，正在跳转...")
                        break
                    else:
                        print("   验证失败，准备重试...")
                        # 刷新页面重置滑块
                        if attempt == 0:
                            page.reload()
                            page.wait_for_load_state("networkidle")
                            page.fill("#username", STUDENT_ID)
                            page.fill("#password", PASSWORD)
                            time.sleep(1)

            # 最终检查
            page.wait_for_load_state("networkidle")
            
            if "login" in page.url:
                print("【最终失败】无法通过滑块验证。")
                page.screenshot(path="final_error.png")
                return

            print("4. 登录成功！获取成绩...")
            # 必须等待 cookie 种下
            time.sleep(3)
            page.goto(TARGET_URL)
            time.sleep(3)
            
            content = page.content()
            page.screenshot(path="result_page.png") # 截图留底

            if "暂无审查结果" in content:
                print("--- 监控中：暂无结果 ---")
            elif "error" in content:
                print("--- 异常：未获取到有效内容 ---")
            else:
                # 只有当包含具体的课程信息时才发邮件
                body_text = page.locator("body").inner_text()
                # 简单过滤，防止误报
                if len(body_text) > 50: 
                    print("!!! 发现新成绩 !!!")
                    send_email("【成绩发布提醒】教务系统更新", f"发现页面变化，内容摘要：\n{body_text[:300]}...")

        except Exception as e:
            print(f"运行出错: {e}")
            page.screenshot(path="exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
