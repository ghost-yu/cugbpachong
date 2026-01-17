import os
import time
import json
import pickle
from pathlib import Path
import smtplib
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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
COOKIE_FILE = "cookies.pkl"

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

def save_cookies(driver, filepath):
    """保存Cookie到文件"""
    with open(filepath, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
    print(f"✓ Cookie已保存到 {filepath}")

def load_cookies(driver, filepath):
    """从文件加载Cookie"""
    if not Path(filepath).exists():
        return False
    try:
        with open(filepath, 'rb') as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            # 移除可能导致问题的字段
            cookie.pop('sameSite', None)
            cookie.pop('httpOnly', None)
            cookie.pop('secure', None)
            driver.add_cookie(cookie)
        print(f"✓ 已加载Cookie: {filepath}")
        return True
    except Exception as e:
        print(f"✗ Cookie加载失败: {e}")
        return False

def manual_login(driver):
    """手动登录模式 - 让用户自己完成滑块验证"""
    print("\n" + "="*60)
    print("🔔 需要手动登录！")
    print("="*60)
    print("请按以下步骤操作：")
    print("1. 在打开的浏览器中输入账号密码")
    print("2. 手动拖动滑块完成验证")
    print("3. 点击登录按钮")
    print("4. 等待登录成功后，回到这里按回车键")
    print("="*60)
    
    driver.get(LOGIN_URL)
    
    # 可选：自动填充账号密码（但不点登录）
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        if STUDENT_ID:
            driver.find_element(By.ID, "username").send_keys(STUDENT_ID)
        if PASSWORD:
            driver.find_element(By.ID, "password").send_keys(PASSWORD)
        print("\n✓ 已自动填写账号密码，请手动完成滑块验证")
    except:
        pass
    
    input("\n>>> 登录完成后按回车继续...")
    
    # 检查是否登录成功
    if "cas.cugb.edu.cn/login" not in driver.current_url:
        print("✓ 登录成功！")
        # 保存Cookie
        save_cookies(driver, COOKIE_FILE)
        return True
    else:
        print("✗ 登录失败，请重试")
        return False

def run_with_cookies():
    """使用Cookie运行（自动化模式）"""
    chrome_options = Options()
    # 这次可以使用无头模式了
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        print("\n🚀 使用Cookie自动登录...")
        
        # 先访问登录页以设置域名
        driver.get("https://cas.cugb.edu.cn/")
        time.sleep(1)
        
        # 加载Cookie
        if not load_cookies(driver, COOKIE_FILE):
            driver.quit()
            return False
        
        # 访问目标页面
        print("📊 正在访问成绩页面...")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        # 检查是否被重定向到登录页
        if "login" in driver.current_url.lower():
            print("✗ Cookie已失效，需要重新登录")
            driver.quit()
            return False
        
        print("✓ 成功访问成绩页面！")
        
        # 检查成绩内容
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
        
        return True
        
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        driver.save_screenshot("error.png")
        return False
    finally:
        driver.quit()

def run_manual_mode():
    """首次运行 - 手动登录获取Cookie"""
    chrome_options = Options()
    # 手动模式必须有头
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        if not manual_login(driver):
            return False
        
        # 登录成功后访问成绩页
        print("\n📊 正在访问成绩页面...")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        content = driver.page_source
        driver.save_screenshot("result_page_initial.png")
        
        if "暂无审查结果" in content:
            print("📋 暂无成绩结果")
        else:
            print("✓ 成功获取页面内容")
        
        return True
        
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        return False
    finally:
        driver.quit()

def main():
    print("\n" + "="*60)
    print("🎓 中国地质大学成绩监控系统 (Cookie版)")
    print("="*60)
    
    # 检查是否有Cookie文件
    if Path(COOKIE_FILE).exists():
        print("✓ 发现已保存的Cookie，尝试自动登录...")
        success = run_with_cookies()
        
        if not success:
            print("\n⚠️  Cookie失效，需要重新手动登录")
            if input("是否重新登录? (y/n): ").lower() == 'y':
                # 删除旧Cookie
                Path(COOKIE_FILE).unlink()
                run_manual_mode()
    else:
        print("⚠️  首次运行，需要手动登录获取Cookie")
        run_manual_mode()
    
    print("\n✅ 程序运行完成")
    print("💡 提示: 下次运行将使用保存的Cookie自动登录")

if __name__ == "__main__":
    main()
