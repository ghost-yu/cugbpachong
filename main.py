import os
import time
import random
import math
import smtplib
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

class ActionMove:
    """
    复刻 Java 版 ActionMove 的核心逻辑
    """
    @staticmethod
    def get_track(distance):
        """
        生成拟人化轨迹：
        1. 0-20%: 加速
        2. 20-80%: 匀速 (波动)
        3. 80-100%: 减速 (包含回退)
        """
        track = []
        current = 0
        mid = distance * 4 / 5  # 减速阈值 (80%)
        t = 0.2 # 计算时间间隔
        v = 0   # 初始速度
        
        while current < distance:
            if current < distance / 5:
                # 开始阶段：加速
                a = random.randint(2, 5)
            elif current < mid:
                # 中间阶段：匀速 (加速度偶尔波动)
                a = random.randint(-1, 2) 
            else:
                # 结束阶段：减速
                a = -random.randint(3, 5)
            
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            
            # 加入轨迹
            track.append(round(move))
            
        # 修正终点误差
        # 如果跑过头了或者没跑到，最后修正一下
        # 模拟“回滑”：在最后阶段加入几个负值
        if sum(track) > distance:
            for _ in range(abs(int(sum(track) - distance))):
                track.append(-1)
        elif sum(track) < distance:
            for _ in range(int(distance - sum(track))):
                track.append(1)
                
        return track

    @staticmethod
    def move_slider(driver, slider_element, container_width):
        """
        执行滑块拖动
        """
        # 1. 瞄准：计算距离 (这里假设滑块宽度约40px，简单计算缺口位置)
        # 真实场景应该用 OpenCV 识别缺口，但无头模式下我们先尝试盲滑到 70%-80% 处
        # 或者根据页面特征动态获取。这里先设定一个常见距离范围。
        slider_width = slider_element.size['width']
        # 随机目标距离：通常在容器宽度的 50% 到 90% 之间
        # 您的 HTML 中容器通常是 300px 左右
        target_distance = int((container_width - slider_width) * random.uniform(0.6, 0.85))
        
        print(f"   目标距离: {target_distance}px")
        
        tracks = ActionMove.get_track(target_distance)
        
        action = ActionChains(driver)
        
        # 2. 初始瞄准与按压 (随机偏移 + 延迟)
        action.click_and_hold(slider_element).perform()
        time.sleep(random.randint(80, 180) / 1000) # 80-180ms 延迟
        
        # 3. 执行移动
        for track in tracks:
            # X轴移动
            x_offset = track
            # Y轴微小抖动 (模拟手抖)
            y_offset = random.choice([0, 0, 0, 1, -1, 0]) 
            
            action.move_by_offset(xoffset=x_offset, yoffset=y_offset).perform()
            
            # 智能速度控制：根据阶段调整 sleep
            # 回滑或减速阶段慢一点
            if track < 0:
                time.sleep(random.randint(20, 30) / 1000)
            else:
                time.sleep(random.randint(5, 15) / 1000)
                
            # 重置 Action 避免累积误差 (Selenium 特性)
            action = ActionChains(driver)

        # 4. 结束延迟与释放
        time.sleep(random.randint(200, 500) / 1000)
        action.release().perform()

def run():
    # 设置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # 新版无头模式，更难被检测
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # 关键：禁用自动化扩展和标志
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # 伪装 User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # CDP 命令：进一步移除 webdriver 特征
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })

    try:
        print("1. 访问登录页...")
        driver.get(LOGIN_URL)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        
        print("2. 填写账号密码...")
        driver.find_element(By.ID, "username").send_keys(STUDENT_ID)
        time.sleep(0.5)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        time.sleep(1)

        print("3. 处理滑块 (ActionMove)...")
        # 定位滑块和容器
        slider = driver.find_element(By.CSS_SELECTOR, ".captcha-move-drag")
        container = driver.find_element(By.ID, "j_digitPicture")
        
        if slider.is_displayed():
            container_width = container.size['width']
            # 调用复刻的核心逻辑
            ActionMove.move_slider(driver, slider, container_width)
            
            time.sleep(2)
            
            # 点击登录
            print("4. 点击登录...")
            driver.find_element(By.ID, "enterBtn").click()
            time.sleep(5)
            
            if "login" in driver.current_url:
                print("【失败】依然在登录页，尝试保存截图...")
                driver.save_screenshot("selenium_failed.png")
                return
        else:
            print("   未发现滑块，直接登录...")
            driver.find_element(By.ID, "enterBtn").click()

        print("5. 获取成绩...")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        content = driver.page_source
        driver.save_screenshot("result_page.png")

        if "暂无审查结果" in content:
            print("--- 暂无结果 ---")
        elif "error" in content:
            print("--- 异常 ---")
        else:
            body = driver.find_element(By.TAG_NAME, "body").text
            if len(body) > 50:
                print("!!! 发现结果 !!!")
                send_email("【成绩发布】系统更新", f"内容摘要：\n{body[:300]}")

    except Exception as e:
        print(f"运行出错: {e}")
        driver.save_screenshot("exception.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
