import os
import time
import random
import math
import smtplib
from email.mime.text import MIMEText
from io import BytesIO
from PIL import Image
import numpy as np
import cv2

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
    改进版滑块处理：增加图像识别和智能重试
    """
    @staticmethod
    def detect_gap(image_bytes):
        """
        使用OpenCV检测缺口位置
        """
        try:
            # 将字节流转为图像
            image = Image.open(BytesIO(image_bytes))
            img_array = np.array(image)
            
            # 转灰度
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # 边缘检测
            edges = cv2.Canny(gray, 100, 200)
            
            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 查找最大的凹陷区域（缺口）
            max_area = 0
            gap_x = 0
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                # 缺口通常在中间区域且面积适中
                if 50 < x < 250 and 500 < area < 3000 and area > max_area:
                    max_area = area
                    gap_x = x
            
            print(f"   检测到缺口位置: {gap_x}px")
            return gap_x if gap_x > 0 else None
        except Exception as e:
            print(f"   缺口检测失败: {e}")
            return None
    
    @staticmethod
    def get_track(distance):
        """
        生成拟人化轨迹（改进版）
        """
        track = []
        current = 0
        mid = distance * 4 / 5
        t = 0.2
        v = 0
        
        while current < distance:
            if current < distance / 5:
                a = random.randint(2, 5)
            elif current < mid:
                a = random.randint(-1, 2) 
            else:
                a = -random.randint(3, 5)
            
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        
        # 修正误差
        total = sum(track)
        if total > distance:
            overshoot = int(total - distance)
            for _ in range(overshoot):
                track.append(-1)
        elif total < distance:
            shortage = int(distance - total)
            for _ in range(shortage):
                track.append(1)
        
        # 添加回退模拟手抖
        for _ in range(random.randint(2, 4)):
            track.append(-random.randint(1, 2))
                
        return track

    @staticmethod
    def move_slider(driver, slider_element, container_element, max_retries=3):
        """
        执行滑块拖动（带重试和图像识别）
        """
        for attempt in range(max_retries):
            try:
                print(f"   尝试第 {attempt + 1}/{max_retries} 次...")
                
                # 1. 尝试识别缺口位置
                gap_position = None
                try:
                    captcha_img = driver.find_element(By.CSS_SELECTOR, ".captcha-move-img img")
                    img_bytes = captcha_img.screenshot_as_png
                    gap_position = ActionMove.detect_gap(img_bytes)
                except Exception as e:
                    print(f"   图像识别失败: {e}")
                
                # 2. 计算滑动距离
                container_width = container_element.size['width']
                slider_width = slider_element.size['width']
                
                if gap_position:
                    target_distance = int(gap_position - slider_width / 2)
                else:
                    # 降级方案：随机距离
                    target_distance = int((container_width - slider_width) * random.uniform(0.6, 0.85))
                
                # 添加随机偏移
                target_distance += random.randint(-5, 5)
                target_distance = max(0, min(target_distance, container_width - slider_width))
                
                print(f"   目标距离: {target_distance}px")
                
                # 3. 生成轨迹
                tracks = ActionMove.get_track(target_distance)
                
                # 4. 执行拖动
                action = ActionChains(driver)
                
                # 移动到滑块并悬停
                action.move_to_element(slider_element).perform()
                time.sleep(random.uniform(0.3, 0.6))
                
                # 按下
                action.click_and_hold(slider_element).perform()
                time.sleep(random.uniform(0.15, 0.25))
                
                # 按轨迹移动
                for i, track in enumerate(tracks):
                    x_offset = track
                    y_offset = random.choice([0, 0, 0, 1, -1, 2, -2, 0, 0])
                    
                    action.move_by_offset(xoffset=x_offset, yoffset=y_offset).perform()
                    
                    # 动态速度
                    if i < len(tracks) * 0.3:
                        sleep_time = random.uniform(0.005, 0.01)
                    elif i < len(tracks) * 0.8:
                        sleep_time = random.uniform(0.01, 0.02)
                    else:
                        sleep_time = random.uniform(0.02, 0.04)
                    
                    time.sleep(sleep_time)
                    action = ActionChains(driver)
                
                # 释放前停顿
                time.sleep(random.uniform(0.3, 0.6))
                action.release().perform()
                
                # 5. 等待验证结果
                time.sleep(2)
                
                # 检查是否还有滑块
                try:
                    slider_check = driver.find_element(By.CSS_SELECTOR, ".captcha-move-drag")
                    if not slider_check.is_displayed():
                        print("   ✓ 滑块验证成功！")
                        return True
                except:
                    print("   ✓ 滑块验证成功！")
                    return True
                
                print(f"   ✗ 第 {attempt + 1} 次尝试失败")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 2))
                    
            except Exception as e:
                print(f"   滑块操作异常: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return False

def run():
    # 设置 Chrome 选项
    chrome_options = Options()
    # 先尝试有头模式（更容易通过验证）
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # 移除 webdriver 特征
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

        print("3. 处理滑块验证...")
        try:
            slider = driver.find_element(By.CSS_SELECTOR, ".captcha-move-drag")
            container = driver.find_element(By.ID, "j_digitPicture")
            
            if slider.is_displayed():
                # 使用改进的滑块处理（最多重试3次）
                success = ActionMove.move_slider(driver, slider, container, max_retries=3)
                
                if not success:
                    print("【失败】滑块验证失败，保存截图...")
                    driver.save_screenshot("slider_failed.png")
                    return
                
                # 等待验证完成
                time.sleep(2)
                
                # 点击登录
                print("4. 点击登录...")
                driver.find_element(By.ID, "enterBtn").click()
                time.sleep(5)
            else:
                print("   未发现滑块，直接登录...")
                driver.find_element(By.ID, "enterBtn").click()
                time.sleep(5)
        except Exception as e:
            print(f"   滑块处理异常: {e}")
            driver.save_screenshot("slider_error.png")
            return
        
        # 检查是否登录成功
        if "login" in driver.current_url.lower():
            print("【失败】依然在登录页...")
            driver.save_screenshot("login_failed.png")
            return

        print("5. 登录成功，获取成绩...")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        content = driver.page_source
        driver.save_screenshot("result_page.png")

        if "暂无审查结果" in content:
            print("--- 暂无结果 ---")
        elif "error" in content.lower():
            print("--- 页面异常 ---")
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
