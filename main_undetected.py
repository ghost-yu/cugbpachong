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

def get_slider_distance(driver):
    """
    尝试通过JS获取滑块真实距离
    """
    try:
        # 尝试从页面元素中获取缺口位置
        script = """
        var img = document.querySelector('.captcha-move-img');
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL();
        """
        # 这里只是示例，实际可能需要更复杂的分析
        return None
    except:
        return None

def human_like_drag(driver, slider, distance):
    """
    超级拟人化拖动 - 多阶段随机
    """
    print(f"   开始拖动: 目标距离 {distance}px")
    
    # 1. 鼠标移动到滑块（模拟瞄准）
    action = ActionChains(driver)
    action.move_to_element_with_offset(slider, 
                                      random.randint(-3, 3), 
                                      random.randint(-3, 3)).perform()
    time.sleep(random.uniform(0.3, 0.8))  # 瞄准时间
    
    # 2. 按下
    action = ActionChains(driver)
    action.click_and_hold(slider).perform()
    time.sleep(random.uniform(0.2, 0.4))  # 按压延迟
    
    # 3. 生成超级拟人化轨迹
    tracks = []
    current = 0
    
    # 第一阶段：快速启动（20%距离）
    while current < distance * 0.2:
        move = random.randint(8, 15)
        tracks.append(move)
        current += move
    
    # 第二阶段：中速前进（到80%）
    while current < distance * 0.8:
        move = random.randint(3, 8)
        tracks.append(move)
        current += move
    
    # 第三阶段：减速接近（到95%）
    while current < distance * 0.95:
        move = random.randint(1, 3)
        tracks.append(move)
        current += move
    
    # 第四阶段：精确定位
    remaining = distance - current
    tracks.append(int(remaining))
    
    # 第五阶段：回退修正（模拟过冲）
    for _ in range(random.randint(2, 5)):
        tracks.append(-random.randint(1, 3))
    
    # 第六阶段：最终微调
    for _ in range(random.randint(1, 3)):
        tracks.append(random.randint(1, 2))
    
    # 4. 执行拖动
    action = ActionChains(driver)
    for i, x in enumerate(tracks):
        # Y轴随机抖动（重要！真人不会走直线）
        y = random.choice([-2, -1, -1, 0, 0, 0, 1, 1, 2])
        
        action.move_by_offset(x, y).perform()
        
        # 动态速度：快-慢-快-慢
        if i < len(tracks) * 0.2:
            t = random.uniform(0.003, 0.008)
        elif i < len(tracks) * 0.8:
            t = random.uniform(0.008, 0.015)
        else:
            t = random.uniform(0.015, 0.030)
        
        time.sleep(t)
        action = ActionChains(driver)
    
    # 5. 释放前暂停（模拟确认）
    time.sleep(random.uniform(0.2, 0.5))
    action.release().perform()
    
    print("   拖动完成")

def try_slider_verification(driver, max_attempts=5):
    """
    多次尝试滑块验证
    """
    for attempt in range(max_attempts):
        try:
            print(f"\n━━━ 尝试 {attempt + 1}/{max_attempts} ━━━")
            
            # 等待滑块出现
            slider = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".captcha-move-drag"))
            )
            
            if not slider.is_displayed():
                print("✓ 未检测到滑块，可以登录")
                return True
            
            # 获取容器宽度
            container = driver.find_element(By.ID, "j_digitPicture")
            container_width = container.size['width']
            slider_width = slider.size['width']
            
            # 计算目标距离（多种策略）
            strategies = [
                lambda: int((container_width - slider_width) * random.uniform(0.65, 0.75)),  # 保守
                lambda: int((container_width - slider_width) * random.uniform(0.70, 0.80)),  # 中等
                lambda: int((container_width - slider_width) * random.uniform(0.75, 0.85)),  # 激进
            ]
            
            strategy = strategies[attempt % len(strategies)]
            distance = strategy()
            
            # 添加随机偏移
            distance += random.randint(-8, 8)
            distance = max(10, min(distance, container_width - slider_width - 10))
            
            print(f"   策略: {'保守' if attempt % 3 == 0 else '中等' if attempt % 3 == 1 else '激进'}")
            print(f"   容器: {container_width}px, 滑块: {slider_width}px")
            
            # 执行拖动
            human_like_drag(driver, slider, distance)
            
            # 等待验证结果
            time.sleep(2.5)
            
            # 检查是否成功（滑块消失或验证通过标识出现）
            try:
                slider_check = driver.find_element(By.CSS_SELECTOR, ".captcha-move-drag")
                if not slider_check.is_displayed():
                    print("✓✓✓ 滑块验证成功！")
                    return True
            except:
                print("✓✓✓ 滑块验证成功！")
                return True
            
            # 检查错误提示
            try:
                error = driver.find_element(By.CSS_SELECTOR, ".captcha-move-error")
                if error.is_displayed():
                    print(f"   ✗ 验证失败: {error.text}")
            except:
                pass
            
            print(f"   ✗ 第 {attempt + 1} 次尝试失败，等待重试...")
            time.sleep(random.uniform(1.5, 3.0))
            
            # 尝试刷新滑块
            try:
                refresh_btn = driver.find_element(By.CSS_SELECTOR, ".captcha-move-refresh")
                refresh_btn.click()
                time.sleep(1)
            except:
                pass
                
        except Exception as e:
            print(f"   异常: {e}")
            time.sleep(2)
    
    return False

def run():
    print("\n" + "="*60)
    print("🚀 使用 Undetected ChromeDriver (绕过检测版)")
    print("="*60)
    
    # 配置选项
    options = uc.ChromeOptions()
    
    # GitHub Actions需要无头模式
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # 创建 undetected driver（自动绕过检测）
    try:
        driver = uc.Chrome(options=options, version_main=None, headless=True)
    except Exception as e:
        print(f"⚠️  创建driver失败: {e}")
        print("尝试使用备用方式...")
        driver = uc.Chrome(options=options, use_subprocess=True)
    
    try:
        print("\n1️⃣  访问登录页...")
        driver.get(LOGIN_URL)
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        print("2️⃣  填写账号密码...")
        # 模拟真人输入（带延迟）
        username_input = driver.find_element(By.ID, "username")
        for char in STUDENT_ID:
            username_input.send_keys(char)
            time.sleep(random.uniform(0.08, 0.15))
        
        time.sleep(random.uniform(0.5, 1.0))
        
        password_input = driver.find_element(By.ID, "password")
        for char in PASSWORD:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.08, 0.15))
        
        time.sleep(random.uniform(0.8, 1.5))
        
        print("3️⃣  处理滑块验证...")
        success = try_slider_verification(driver, max_attempts=5)
        
        if not success:
            print("\n❌ 滑块验证失败次数过多")
            driver.save_screenshot("slider_failed.png")
            return
        
        print("\n4️⃣  点击登录...")
        login_btn = driver.find_element(By.ID, "enterBtn")
        time.sleep(random.uniform(0.5, 1.0))
        login_btn.click()
        
        time.sleep(5)
        
        # 检查是否登录成功
        if "login" in driver.current_url.lower():
            print("❌ 登录失败，仍在登录页")
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
        # GitHub Actions环境不需要手动输入
        if os.environ.get('GITHUB_ACTIONS'):
            print("\n运行在GitHub Actions环境")
        else:
            input("\n按回车键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    run()
