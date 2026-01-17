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

# 登录和目标网址
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

# 仿真鼠标滑动算法
def mouse_slide(page, start_x, start_y, end_x, end_y):
    # 1. 移动到滑块起点
    page.mouse.move(start_x, start_y, steps=5)
    time.sleep(0.2)
    page.mouse.down()
    
    # 2. 计算滑动轨迹
    distance = end_x - start_x
    # 增加步数，让动作更慢更自然
    steps = random.randint(30, 45) 
    
    for i in range(steps):
        # 缓动算法：模拟人手先快后慢
        progress = i / steps
        # 使用 easeOutCubic 曲线
        rate = 1 - pow(1 - progress, 3)
        
        move_x = start_x + distance * rate
        # Y轴随机微颤，模拟手抖
        move_y = start_y + random.uniform(-2, 2)
        
        page.mouse.move(move_x, move_y)
        # 随机时间间隔
        time.sleep(random.uniform(0.01, 0.03))
    
    # 3. 到达终点微调
    page.mouse.move(end_x, end_y)
    time.sleep(0.6) # 停顿一下，模拟确认
    page.mouse.up()

def run():
    with sync_playwright() as p:
        # 启动配置
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled", # 关键：禁用自动化特征
                "--disable-infobars",
                "--window-size=1920,1080"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # --- 手动注入隐身 JS (替代 playwight-stealth 库) ---
        context.add_init_script("""
            // 抹除 webdriver 属性，这是最明显的机器人特征
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            // 伪装插件列表
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3]
            });
            // 伪装语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh']
            });
        """)

        page = context.new_page()

        try:
            print("1. 访问登录页...")
            page.goto(LOGIN_URL)
            page.wait_for_load_state("networkidle")
            
            # 等待输入框出现
            try:
                page.wait_for_selector("#username", state="visible", timeout=10000)
            except:
                print("页面加载超时，截图保存")
                page.screenshot(path="load_error.png")
                return
            
            print("2. 填写账号密码...")
            page.fill("#username", STUDENT_ID)
            page.fill("#password", PASSWORD)
            time.sleep(1)

            # 最多重试2次滑块
            for attempt in range(2):
                print(f"3. 处理滑块 (第 {attempt+1} 次)...")
                
                slider = page.locator(".captcha-move-drag")
                container = page.locator("#j_digitPicture")
                
                if not slider.is_visible():
                    print("   滑块未出现，可能不需要验证")
                    break

                slider_box = slider.bounding_box()
                container_box = container.bounding_box()

                if slider_box and container_box:
                    start_x = slider_box["x"] + slider_box["width"] / 2
                    start_y = slider_box["y"] + slider_box["height"] / 2
                    end_x = start_x + container_box["width"] - slider_box["width"]
                    
                    # 执行拟人滑动
                    mouse_slide(page, start_x, start_y, end_x, start_y)
                    
                    time.sleep(2)
                    
                    # 尝试点击登录
                    page.click("#enterBtn")
                    time.sleep(3)
                    
                    if "login" not in page.url:
                        print("   验证成功，跳转中...")
                        break
                    else:
                        print("   验证失败，刷新重试...")
                        if attempt == 0:
                            page.reload()
                            page.wait_for_load_state("networkidle")
                            page.fill("#username", STUDENT_ID)
                            page.fill("#password", PASSWORD)
                            time.sleep(1)

            page.wait_for_load_state("networkidle")
            
            # 最终验证
            if "login" in page.url:
                print("【最终失败】无法通过滑块。")
                page.screenshot(path="final_failed.png") # 失败截图
                return

            print("4. 登录成功！获取成绩...")
            time.sleep(2) # 等待 Cookie 写入
            page.goto(TARGET_URL)
            time.sleep(3)
            
            content = page.content()
            page.screenshot(path="result_page.png") # 成功截图

            if "暂无审查结果" in content:
                print("--- 监控中：暂无结果 ---")
            elif "error" in content:
                print("--- 异常：内容无效 ---")
            else:
                body_text = page.locator("body").inner_text()
                # 简单过滤，防止误报，内容太短通常是报错信息
                if len(body_text) > 50:
                    print("!!! 发现结果 !!!")
                    send_email("【成绩提醒】系统有更新", f"内容摘要：\n{body_text[:300]}...")

        except Exception as e:
            print(f"运行出错: {e}")
            page.screenshot(path="exception.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
