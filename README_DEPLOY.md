# 中国地质大学成绩监控系统

## 改进内容 ✨

### 1. **滑块验证增强**
- ✅ 添加 OpenCV 图像识别缺口位置
- ✅ 智能重试机制（最多3次）
- ✅ 改进轨迹算法（更拟人化）
- ✅ 动态速度控制
- ✅ 随机抖动和回退

### 2. **新增依赖**
```bash
pip install pillow opencv-python-headless numpy
```

## 快速部署指南

### 步骤 1: 本地测试（推荐）

**安装依赖：**
```bash
cd cugbpachong
pip install selenium webdriver-manager pillow opencv-python numpy
```

**配置环境变量（Windows）：**
```powershell
$env:STUDENT_ID="你的学号"
$env:PASSWORD="你的密码"
$env:EMAIL_USER="你的QQ邮箱"
$env:EMAIL_PASS="QQ邮箱授权码"
```

**运行测试：**
```bash
python main_improved.py
```

### 步骤 2: GitHub Actions 部署

**2.1 创建仓库并推送代码**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

**2.2 配置 Secrets**
进入仓库设置：`Settings → Secrets and variables → Actions → New repository secret`

添加以下4个密钥：
- `STUDENT_ID`: 你的学号
- `PASSWORD`: 你的密码  
- `EMAIL_USER`: QQ邮箱（如 123456@qq.com）
- `EMAIL_PASS`: QQ邮箱授权码（**不是密码！**）

**2.3 获取QQ邮箱授权码**
1. 登录 [QQ邮箱网页版](https://mail.qq.com)
2. 设置 → 账户 → POP3/IMAP/SMTP服务
3. 开启 "IMAP/SMTP服务"
4. 生成授权码（保存好，只显示一次）

**2.4 启用 Actions**
1. 进入仓库 `Actions` 标签
2. 选择 "Grade Monitor" 工作流
3. 点击 `Run workflow` 手动测试

## 重要说明 ⚠️

### 无头模式问题
GitHub Actions 使用无头模式运行，滑块验证可能仍然失败。如果失败：

**解决方案A - Cookie持久化（推荐）：**
手动登录一次并保存Cookie，让脚本复用Session。

**解决方案B - 使用代理/验证码打码服务：**
集成第三方打码平台（如2Captcha）。

**解决方案C - 降低检查频率：**
减少触发频率（如从30分钟改为2小时），降低风控。

### 测试建议
1. **先本地测试** - 确保滑块能通过（有头模式）
2. **查看截图** - 下载Actions的debug-screenshots查看失败原因
3. **查看日志** - Actions运行日志会显示详细错误

## 运行流程

```
启动 → 访问登录页 → 填写账号密码 → 识别缺口位置 
→ 生成拟人轨迹 → 拖动滑块（最多3次重试）
→ 验证成功 → 登录 → 访问成绩页 → 检测更新 → 发邮件
```

## 常见问题

**Q: 滑块一直失败？**
A: 
1. 检查是否使用有头模式测试
2. 查看 `slider_failed.png` 截图
3. 尝试修改 `max_retries` 增加重试次数

**Q: 邮件收不到？**
A:
1. 确认授权码（不是密码）
2. 检查QQ邮箱是否开启SMTP
3. 查看垃圾邮件文件夹

**Q: GitHub Actions 运行失败？**
A:
1. 检查Secrets配置是否正确
2. 下载截图Artifacts查看
3. 查看Actions日志详细错误

## 文件说明

- `main.py` - 原始版本
- `main_improved.py` - 改进版（推荐使用）
- `.github/workflows/monitor.yml` - GitHub Actions配置
- `README.md` - 本文档

## 下一步优化方向

- [ ] Cookie持久化（避免重复登录）
- [ ] 使用Playwright替代Selenium（更难检测）
- [ ] 集成验证码打码服务
- [ ] 添加Telegram/微信推送
- [ ] 数据库存储历史成绩
