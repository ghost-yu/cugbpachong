# 🎯 Cookie持久化方案 - 彻底解决滑块问题

## 核心思路
**手动登录一次** → 保存Cookie → 后续自动使用Cookie访问（无需滑块）

## 使用步骤

### 1. 配置环境变量（可选）
```powershell
# 在PowerShell中设置
$env:STUDENT_ID="你的学号"
$env:PASSWORD="你的密码"
$env:EMAIL_USER="你的QQ邮箱@qq.com"
$env:EMAIL_PASS="QQ邮箱授权码"
```

### 2. 首次运行（手动登录）
```bash
python main_cookie.py
```

**会发生什么：**
1. 🌐 自动打开浏览器
2. 📝 自动填写账号密码（如果配置了环境变量）
3. **🖱️ 你手动拖动滑块完成验证**
4. 🔐 点击登录
5. ⏎ 回到终端按回车键
6. 💾 程序自动保存Cookie到 `cookies.pkl`

### 3. 后续运行（自动模式）
```bash
python main_cookie.py
```

**会发生什么：**
- ✅ 自动加载Cookie
- ✅ 无头模式运行（不打开浏览器）
- ✅ 直接访问成绩页面
- ✅ 检测成绩更新并发邮件

## 优势对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **原版（自动滑块）** | 全自动 | 通过率低，容易被检测 |
| **Cookie版（推荐）** | ✅ 通过率100%<br>✅ GitHub Actions可用<br>✅ 无需图像识别 | 首次需手动登录<br>Cookie过期需重新登录 |

## GitHub Actions 部署

Cookie版可以在GitHub Actions上完美运行！

### 步骤1: 获取Cookie
在本地运行一次：
```bash
python main_cookie.py
# 手动完成登录后，会生成 cookies.pkl 文件
```

### 步骤2: 将Cookie编码为Base64
```python
import base64
with open('cookies.pkl', 'rb') as f:
    encoded = base64.b64encode(f.read()).decode()
    print(encoded)
```

### 步骤3: 添加到GitHub Secrets
- 进入仓库 Settings → Secrets
- 添加 `COOKIES_BASE64`: 粘贴上一步的输出

### 步骤4: 修改Actions配置
创建 `.github/workflows/monitor_cookie.yml`:

```yaml
name: Grade Monitor (Cookie版)

on:
  schedule:
    - cron: '*/30 * * * *'  # 每30分钟
  workflow_dispatch:

jobs:
  check_grade:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install selenium webdriver-manager
      
      - name: Restore cookies
        run: |
          echo "${{ secrets.COOKIES_BASE64 }}" | base64 -d > cookies.pkl
      
      - name: Run Monitor
        env:
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
        run: python main_cookie.py
      
      - name: Upload screenshots
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: screenshots
          path: "*.png"
```

## Cookie有效期

Cookie通常有效期：**7-30天**

**过期后怎么办？**
1. 本地运行 `python main_cookie.py`
2. 重新手动登录
3. 更新GitHub Secret中的 `COOKIES_BASE64`

## 常见问题

**Q: Cookie什么时候会过期？**
A: 
- 学校修改密码
- 长时间未使用（30天+）
- 系统安全策略更新

**Q: 如何知道Cookie过期了？**
A: 程序会输出 `Cookie已失效，需要重新登录`

**Q: 能否永久有效？**
A: 不能。但可以写个自动续期脚本（定期访问刷新Cookie）

## 完整流程图

```
首次运行:
┌─────────────┐
│ 运行脚本     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 打开浏览器   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 手动完成登录 │ ← 你只需在这里操作一次
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 保存Cookie   │
└─────────────┘

后续运行（完全自动）:
┌─────────────┐
│ 加载Cookie   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 无头访问     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 检测成绩     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 发送邮件     │
└─────────────┘
```

## 立即开始

```bash
# 1. 安装依赖（已安装可跳过）
pip install selenium webdriver-manager

# 2. 运行（首次）
python main_cookie.py

# 3. 手动完成登录

# 4. 下次运行（自动）
python main_cookie.py
```

**就是这么简单！** 🎉
