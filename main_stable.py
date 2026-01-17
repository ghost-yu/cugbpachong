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

def stable_drag(driver, slider, distance):
    """
    稳定版拖动 - 使用原生drag_and_drop_by_offset
    """
    print(f"   拖动 {distance}px...")
    
    try:
        # 方法1: 使用原生API（更稳定）
        action = ActionChains(driver)
        action.click_and_hold(slider)
        action.pause(0.3)
        action.move_by_offset(distance, random.randint(-2, 2))
        action.pause(0.2)
        action.release()
        action.perform()
        
    except Exception as e:
        print(f"   拖动异常: {e}")
        # 方法2: 备用方案
        try:
            action = ActionChains(driver)
            action.drag_and_drop_by_offset(slider, distance, 0).perform()
        except:
            pass

def try_slider_simple(driver, max_attempts=5):
    """
    简化版滑块验证
    """
    distances = [180, 200, 220, 240, 190, 210, 230, 250]
    
    for attempt in range(max_attempts):
        try:
            print(f"\n━━━ 尝试 {attempt + 1}/{max_attempts} ━━━")
            
            # 等待滑块
            slider = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".captcha-move-drag"))
            )
            
            if not slider.is_displayed():
                print("✓ 无需滑块验证")
                return True
            
            # 使用预设距离
            distance = distances[attempt % len(distances)] + random.randint(-10, 10)
            
            # 执行拖动
            stable_drag(driver, slider, distance)
            
            # 等待结果
            time.sleep(2.5)
            
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
            time.sleep(2)
            
            # 刷新验证码
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
    print("🚀 稳定版 - Undetected ChromeDriver")
    print("="*60)
    
    options = uc.ChromeOptions()
    
    is_github_actions = os.environ.get('GITHUB_ACTIONS')
    
    if is_github_actions:
        print("🔹 GitHub Actions环境（无头模式）")
        options.add_argument("--headless=new")
    else:
        print("🔹 本地环境（有头模式 - 可以看到浏览器）")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    try:
        driver = uc.Chrome(options=options, version_main=None)
    except:
        driver = uc.Chrome(options=options)
    
    try:
        print("\n1️⃣  访问登录页...")
        driver.get(LOGIN_URL)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        print("2️⃣  填写账号密码...")
        driver.find_element(By.ID, "username").send_keys(STUDENT_ID)
        time.sleep(0.5)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        time.sleep(1)
        
        print("3️⃣  处理滑块验证...")
        success = try_slider_simple(driver, max_attempts=5)
        
        if not success:
            print("\n❌ 滑块验证失败")
            driver.save_screenshot("slider_failed.png")
            return
        
        print("\n4️⃣  点击登录...")
        driver.find_element(By.ID, "enterBtn").click()
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
        
        print("\n✅ 运行完成")
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        driver.save_screenshot("error.png")
        import traceback
        traceback.print_exc()
    finally:
        if not os.environ.get('GITHUB_ACTIONS'):
            input("\n按回车键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    run()
