import os
import time
import random
import smtplib
from email.mime.text import MIMEText
from twocaptcha import TwoCaptcha

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 配置 ---
STUDENT_ID = os.environ.get("STUDENT_ID")
PASSWORD = os.environ.get("PASSWORD")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
TWOCAPTCHA_KEY = os.environ.get("TWOCAPTCHA_KEY")  # 新增：2Captcha API Key

LOGIN_URL = "https://cas.cugb.edu.cn/login?service=https%3A%2F%2Fportal.cugb.edu.cn%2Fmanage%2Fcommon%2Fcas_login%2F30001%3Fredirect%3Dhttps%253A%252F%252Fportal.cugb.edu.cn"
TARGET_URL = "https://jwglxt.cugb.edu.cn/academic/studentcheckscore/studentCheckresultList.do"

def send_email(subject, content):
    if not EMAIL_USER or not EMAIL_PASS:
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

def solve_slider_with_2captcha(driver):
    """
    使用2Captcha解决滑块验证
    """
    if not TWOCAPTCHA_KEY:
        print("❌ 未配置2Captcha API Key")
        return False
    
    try:
        print("🤖 使用2Captcha打码服务...")
        solver = TwoCaptcha(TWOCAPTCHA_KEY)
        
        # 获取滑块图片
        captcha_img = driver.find_element(By.CSS_SELECTOR, ".captcha-move-img img")
        img_src = captcha_img.get_attribute("src")
        
        # 调用2Captcha API（滑块类型）
        result = solver.coordinates(
            img_src,
            lang='zh'
        )
        
        distance = result['code'].split(':')[0]  # 获取X坐标
        
        print(f"✓ 2Captcha返回距离: {distance}px")
        
        # 使用返回的距离拖动
        slider = driver.find_element(By.CSS_SELECTOR, ".captcha-move-drag")
        from selenium.webdriver.common.action_chains import ActionChains
        
        action = ActionChains(driver)
        action.click_and_hold(slider).perform()
        time.sleep(0.2)
        action.move_by_offset(int(distance), 0).perform()
        time.sleep(0.3)
        action.release().perform()
        
        time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"❌ 2Captcha解决失败: {e}")
        return False

def run():
    print("\n" + "="*60)
    print("🚀 2Captcha打码服务版本")
    print("="*60)
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
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
        driver.find_element(By.ID, "username").send_keys(STUDENT_ID)
        time.sleep(0.5)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        time.sleep(1)
        
        print("3️⃣  使用2Captcha解决滑块...")
        success = solve_slider_with_2captcha(driver)
        
        if not success:
            print("❌ 打码失败")
            return
        
        print("\n4️⃣  点击登录...")
        driver.find_element(By.ID, "enterBtn").click()
        time.sleep(5)
        
        if "login" in driver.current_url.lower():
            print("❌ 登录失败")
            return
        
        print("✓✓✓ 登录成功！")
        
        print("\n5️⃣  访问成绩页面...")
        driver.get(TARGET_URL)
        time.sleep(3)
        
        content = driver.page_source
        
        if "暂无审查结果" in content:
            print("📋 暂无成绩结果")
        else:
            body = driver.find_element(By.TAG_NAME, "body").text
            if len(body) > 50:
                print("🎉 发现成绩更新！")
                send_email("【成绩发布】系统更新", f"内容摘要：\n{body[:300]}")
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    run()

# 使用方法：
# 1. 安装：pip install 2captcha-python
# 2. 注册2Captcha账号：https://2captcha.com/
# 3. 充值（约$1-3）
# 4. 获取API Key
# 5. 添加到GitHub Secrets: TWOCAPTCHA_KEY
# 
# 费用：约 $0.001-0.003 / 次
# 一天48次 = $0.05-0.15
# 一个月 = $1.5-4.5
