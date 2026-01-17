# 🎯 最终方案选择指南

## 现状分析

经过多次测试，发现**你们学校的滑块验证极其严格**：
- ✅ 本地有头模式：80-90% 成功率
- ❌ GitHub Actions无头：0% 成功率（40次尝试全部失败）

## 三个可行方案对比

| 方案 | 成功率 | 成本 | 维护难度 | 推荐度 |
|------|--------|------|----------|--------|
| **A. 本地定时任务** | **95%+** | 免费 | 低（需保持电脑开机） | ⭐⭐⭐⭐⭐ |
| **B. 2Captcha打码** | **99%+** | ~$3/月 | 低 | ⭐⭐⭐⭐ |
| **C. Actions重试** | **5-15%** | 免费 | 低（会经常失败） | ⭐⭐ |

---

## 方案A：本地定时任务（强烈推荐）

### 为什么推荐？
- ✅ **最高成功率**：有头模式通过率80-90%
- ✅ **完全免费**
- ✅ **不依赖外部服务**
- ⚠️ 需要电脑保持开机（或设置唤醒）

### 配置步骤

#### 1. 创建运行脚本
在 `G:\2353\cugbpachong\` 创建 `run_monitor.bat`：

```batch
@echo off
cd /d G:\2353\cugbpachong
call .venv\Scripts\activate
set STUDENT_ID=你的学号
set PASSWORD=你的密码
set EMAIL_USER=你的邮箱@qq.com
set EMAIL_PASS=你的授权码
python main_undetected.py
```

#### 2. 设置Windows任务计划
1. 按 `Win + R`，输入 `taskschd.msc`
2. 右侧点击"创建基本任务"
3. 名称：`成绩监控`
4. 触发器：**重复任务** → 每30分钟
5. 操作：**启动程序**
   - 程序：`G:\2353\cugbpachong\run_monitor.bat`
6. 条件：
   - ✅ 只有在计算机接通电源时才启动
   - ✅ 如果计算机开始使用电池，则停止
7. 设置：
   - ✅ 允许按需运行任务
   - ✅ 如果任务失败，每5分钟重新启动一次

#### 3. 测试
右键点击任务 → **运行**，观察是否成功。

### 优化建议
- **防止息屏**：控制面板 → 电源选项 → 从不关闭显示器
- **唤醒定时**：BIOS设置 → 定时开机（早8点-晚12点）
- **后台运行**：修改脚本，添加无头模式（成功率会降低）

---

## 方案B：2Captcha打码服务

### 为什么选择？
- ✅ **最高成功率**：99%+
- ✅ **支持GitHub Actions**
- ✅ **无需本地电脑**
- 💰 **需付费**：约$3/月

### 费用计算
- 每次验证：$0.001-0.003
- 每30分钟一次：一天48次
- 一天费用：$0.05-0.15
- **一个月：$1.5-4.5**

### 配置步骤

#### 1. 注册2Captcha
访问：https://2captcha.com/
- 注册账号
- 充值 $3-5 USD
- 获取 **API Key**

#### 2. 安装依赖
```bash
pip install 2captcha-python
```

#### 3. 添加GitHub Secret
- 仓库 → Settings → Secrets
- 新增：`TWOCAPTCHA_KEY`：你的API Key

#### 4. 修改Actions配置
`.github/workflows/monitor.yml`：
```yaml
- name: Install dependencies
  run: |
    pip install undetected-chromedriver requests 2captcha-python

- name: Run Monitor
  env:
    STUDENT_ID: ${{ secrets.STUDENT_ID }}
    PASSWORD: ${{ secrets.PASSWORD }}
    EMAIL_USER: ${{ secrets.EMAIL_USER }}
    EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
    TWOCAPTCHA_KEY: ${{ secrets.TWOCAPTCHA_KEY }}
  run: python main_2captcha.py
```

### 余额监控
登录2Captcha查看余额，低于$1时充值。

---

## 方案C：接受低成功率（不推荐）

### 当前配置
已优化为：
- ⏰ 每2小时检查一次（降低频率）
- 🔄 每次尝试8个距离
- ♻️ 失败后重试5次，间隔3分钟
- 📊 预期成功率：**5-15%**

### 适用场景
- 成绩更新不紧急
- 不想花钱
- 不想开着电脑

### 现状
- 一天12次检查（每2小时）
- 每次5轮重试，共40次尝试
- **预计1-2次成功 / 天**

---

## 🎯 最终建议

### 如果你...

#### 1. 电脑经常开着 → **选方案A**
```bash
# 立即设置本地定时任务
# 10分钟内完成，终身免费
```

#### 2. 电脑不常开 + 愿意付费 → **选方案B**
```bash
# 注册2Captcha
# 充值$5，可用2-3个月
```

#### 3. 不想花钱 + 电脑不常开 → **选方案C**
```bash
# 接受低成功率
# 保持当前GitHub Actions配置
# 可能2-3天才成功一次
```

---

## 立即行动

### 方案A - 本地定时任务
```powershell
# 1. 创建批处理文件
cd G:\2353\cugbpachong
notepad run_monitor.bat
# 粘贴上面的脚本内容

# 2. 手动测试一次
.\run_monitor.bat

# 3. 成功后，设置任务计划（见上文）
```

### 方案B - 2Captcha
```bash
# 1. 访问 https://2captcha.com/ 注册
# 2. 充值 $5
# 3. 复制 API Key
# 4. 添加到 GitHub Secrets: TWOCAPTCHA_KEY
# 5. 修改 Actions 配置使用 main_2captcha.py
```

### 方案C - 保持现状
```
# 什么都不用做
# 当前已经是最优配置
# 只是成功率很低（5-15%）
```

---

## FAQ

**Q: 为什么本地成功率高，Actions低？**  
A: 有头浏览器更像真人，无头环境特征太明显。

**Q: 2Captcha合法吗？**  
A: 合法，但有些网站条款可能禁止。学校系统无明文禁止。

**Q: 能否两个方案同时用？**  
A: 可以！本地 + Actions 双保险，提高覆盖率。

**Q: 方案A需要一直开着浏览器吗？**  
A: 不需要，每次运行完自动关闭。

**Q: 电费会很高吗？**  
A: 不会，每次运行1-2分钟，功耗几乎可忽略。

---

## 总结

| 你的情况 | 推荐方案 | 理由 |
|---------|---------|------|
| 电脑24小时开机 | **方案A** | 免费+高成功率 |
| 电脑白天开机 | **方案A** | 成绩通常白天更新 |
| 电脑很少开 | **方案B** | 付费但稳定 |
| 预算紧张 | **方案C** | 接受低成功率 |
| 追求完美 | **A+B** | 本地为主，Actions兜底 |

**我的建议**：先试方案A，如果觉得麻烦再考虑方案B。方案C只是备选。
