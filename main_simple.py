import os
import time
import random
import smtplib
from email.mime.text import MIMEText

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
        print("✓ 邮件发送成功")
    except Exception as e:
        print(f"✗ 邮件发送失败: {e}")

def simple_drag(driver, slider, distance):
    """
    简化版拖动 - 使用固定距离
    """
    print(f"   快速拖动: {distance}px")
    
    action = ActionChains(driver)
    
    # 移动到滑块
    action.move_to_element(slider).perform()
    time.sleep(0.3)
    
    # 按下
    action.click_and_hold(slider).perform()
    time.sleep(0.2)
    
    # 快速移动到目标位置
    action = ActionChains(driver)
    remaining = distance
    
    while remaining > 0:
        step = min(random.randint(15, 25), remaining)
        y = random.choice([-1, 0, 0, 1])
        action.move_by_offset(step, y).perform()
        remaining -= step
        time.sleep(random.uniform(0.01, 0.02))
        action = ActionChains(driver)
    
    # 小幅回退
    for _ in range(3):
        action.move_by_offset(-random.randint(1, 3), random.choice([-1, 0, 1])).perform()
        time.sleep(0.02)
        action = ActionChains(driver)
    
    time.sleep(0.3)
    action.release().perform()

def try_slider_with_fixed_distances(driver, max_attempts=5):
    """
    使用固定距离尝试（基于经验值）
    """
    # 常见的成功距离（根据经验调整）
    distances = [180, 200, 220, 240, 190, 210, 230, 170]
    
    for attempt in range(max_attempts):
        try:
            print(f"\n━━━ 尝试 {attempt + 1}/{max_attempts} ━━━")
            
            # 等待滑块出现
            slider = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".captcha-move-drag"))
            )
            
            if not slider.is_displayed():
                print("✓ 未检测到滑块")
                return True
            
            # 使用预设距离
            distance = distances[attempt % len(distances)]
            distance += random.randint(-10, 10)  # 添加随机性
            
            print(f"   使用距离: {distance}px")
            
            # 执行拖动
            simple_drag(driver, slider, distance)
            
            # 等待验证结果
            time.sleep(2)
            
            # 检查是否成功
            try:
                slider_check = driver.find_element(By.CSS_SELECTOR, ".captcha-move-drag")
                if not slider_check.is_displayed():
                    print("✓✓✓ 验证成功！")
                    return True
            except:
                print("✓✓✓ 验证成功！")
                return True
            
            print(f"   ✗ 第 {attempt + 1} 次失败")
            time.sleep(random.uniform(1, 2))
            
            # 尝试刷新验证码
            try:
                refresh_btn = driver.find_element(By.CSS_SELECTOR, ".captcha-move-refresh")
                refresh_btn.click()
                time.sleep(1)
            except:
                pass
                
        except Exception as e:
            print(f"   异常: {e}")
            time.sleep(1)
    
    return False

def run():
    print("\n" + "="*60)
    print("🚀 简化版 Undetected ChromeDriver (固定距离策略)")
    print("="*60)
    
    # 配置选项
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    try:
        driver = uc.Chrome(options=options, version_main=None, headless=True)
    except:
        driver = uc.Chrome(options=options, use_subprocess=True)
    
    try:
        print("\n1️⃣  访问登录页...")
        driver.get(LOGIN_URL)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        print("2️⃣  填写账号密码...")
        username_input = driver.find_element(By.ID, "username")
        for char in STUDENT_ID:
            username_input.send_keys(char)
            time.sleep(random.uniform(0.08, 0.15))
        
        time.sleep(0.8)
        
        password_input = driver.find_element(By.ID, "password")
        for char in PASSWORD:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.08, 0.15))
        
        time.sleep(1.2)
        
        print("3️⃣  处理滑块验证（固定距离策略）...")
        success = try_slider_with_fixed_distances(driver, max_attempts=8)  # 增加到8次
        
        if not success:
            print("\n❌ 滑块验证失败")
            driver.save_screenshot("slider_failed.png")
            return
        
        print("\n4️⃣  点击登录...")
        login_btn = driver.find_element(By.ID, "enterBtn")
        time.sleep(0.8)
        login_btn.click()
        
        time.sleep(5)
        
        if "login" in driver.current_url.lower():
            print("❌ 登录失败")
            driver.save_screenshot("login_failed.png")
            return
        
        print("✓✓✓ 登录成功！")
        
        print("\n5️⃣  访问成绩页面...")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        content = driver.page_source
        driver.save_screenshot("result_page.png")
        
        if "暂无审查结果" in content:
            print("📋 暂无成绩结果")
        elif "error" in content.lower():
            print("⚠️  页面异常")
        else:
            body = driver.find_element(By.TAG_NAME, "body").text
            if len(body) > 50:
                print("🎉 发现成绩更新！")
                send_email("【成绩发布】系统更新", f"内容摘要：\n{body[:300]}")
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        driver.save_screenshot("error.png")
        import traceback
        traceback.print_exc()
    finally:
        if os.environ.get('GITHUB_ACTIONS'):
            print("\n运行在GitHub Actions环境")
        else:
            input("\n按回车键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    run()
