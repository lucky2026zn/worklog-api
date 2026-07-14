# 工时记录系统 — 完整部署与使用手册

> 更新日期：2026-07-13
> 项目结构：`worklog-api/`（后端 Flask API）+ `worklog-weapp/`（微信小程序）

---

## 目录

1. [项目介绍](#一项目介绍)
2. [本地开发环境](#二本地开发环境)
3. [常见错误与修复](#三常见错误与修复)
4. [功能修改记录](#四功能修改记录)
5. [部署到 Zeabur](#五部署到-zeabur)
6. [微信小程序配置](#六微信小程序配置)
7. [发布体验版](#七发布体验版)
8. [日常修改流程](#八日常修改流程)
9. [关键地址汇总](#九关键地址汇总)
10. [常见问题 FAQ](#十常见问题-faq)

---

## 一、项目介绍

工时记录系统，包含两部分：

| 模块 | 技术栈 | 用途 |
|---|---|---|
| `worklog-api` | Python Flask + SQLite/PostgreSQL | 提供 API 接口 |
| `worklog-weapp` | 微信小程序 | 前端界面 |

---

## 二、本地开发环境

### 2.1 启动后端

```bash
# 进入后端目录
cd C:\Users\nazha\Documents\New project_文件整理\worklog-api

# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

启动后 API 地址：`http://127.0.0.1:5000/api`

### 2.2 启动小程序

用微信开发者工具打开 `worklog-weapp` 文件夹，编译运行。

### 2.3 本地 API 地址配置

`worklog-weapp\app.js` 第 5 行：

```javascript
apiBaseUrl: "http://localhost:5000/api"   // 本地开发时
apiBaseUrl: "https://你的域名/api"          // 部署后
```

---

## 三、常见错误与修复

### 3.1 WXSS 文件编译错误

**错误信息：**
```
[ WXSS 文件编译错误] ./pages/admin/admin.wxss(1:1): unexpected `�` at pos 1
```

**原因：** 文件是 UTF-8 with BOM 格式，微信小程序 WXSS 编译器不认 BOM。

**解决：** 用 VS Code 打开，底部状态栏把编码改为 **UTF-8 without BOM**，重新编译。

### 3.2 _append.js 上传报错

**错误信息：**
```
Error: file: pages/admin/_append.js unknown: Missing semicolon. (1:21)
```

**原因：** `_append.js` 是多余的碎片文件，不是合法的独立 JS 文件。

**解决：** 直接删除该文件：
```bash
Remove-Item -Path "worklog-weapp\pages\admin\_append.js" -Force
```

### 3.3 LF / CRLF 警告（不影响运行）

**警告信息：**
```
warning: LF will be replaced by CRLF the next time Git touches it
```

**原因：** Windows 和 Linux 换行符不同，Git 自动转换。

**解决：** 忽略即可，不影响程序运行。

### 3.4 Git 用户配置

**错误信息：**
```
fatal: unable to auto-detect email address
```

**解决：**
```bash
git config --global user.email "你的邮箱@example.com"
git config --global user.name "你的名字"
```

### 3.5 GitHub push 连接被重置

**错误信息：**
```
fatal: unable to access 'https://...': Recv failure: Connection was reset
```

**原因：** 国内网络访问 GitHub 不稳定。

**解决方法一：SSH（推荐）**
```bash
# 生成密钥
ssh-keygen -t ed25519 -C "你的邮箱@example.com"

# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 复制输出内容，添加到 GitHub：
# 浏览器打开 https://github.com/settings/keys → New SSH key → 粘贴 → Add

# 改远程地址
git remote set-url origin git@github.com:你的用户名/你的仓库.git
git push -u origin main
```

**解决方法二：代理**
```bash
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
git push -u origin main
# 推送完后关闭
git config --global --unset http.proxy
git config --global --unset https.proxy
```

---

## 四、功能修改记录

### 4.1 进度改为文字输入（原进度%→进度说明）

**需求：** 每个任务的进度不仅是百分比，可以是"入组3例"、"访视2例"等文字。

**后端修改：**

| 文件 | 修改内容 |
|---|---|
| `worklog-api/models.py` | `TimeEntryDetail.progress` 字段类型 `Float` → `String(200)` |
| `worklog-api/api/time_entries.py` | 提交接口接受文本格式 progress，兼容旧数字数据 |
| `worklog-api/api/exports.py` | Excel 导出表头"进度(%)"→"进度说明" |

**前端修改：**

| 文件 | 修改内容 |
|---|---|
| `time-entry.wxml` | 列头"进度%"→"进度说明"；`type="digit"`→`type="text"`；placeholder 改为"如入组3例" |
| `time-entry.js` | `onProgressInput` 取消 parseFloat，存原始字符串 |
| `time-entry.wxss` | 进度列宽度 `flex: 1.5`→`2.5` |
| `daily-report.wxml` | `{{item.progress}}%` → `{{item.progress}}` |

### 4.2 工时支持小数（0.5h）

**需求：** 工时(h) 支持输入 0.5、1.25 等小数。

**原因分析：** `type="digit"` 在小程序某些版本不允许输入小数点；且受控输入（`value` + `setData`）会导致光标跳动。

**修改：**

| 文件 | 修改前 | 修改后 |
|---|---|---|
| `time-entry.wxml` 工时输入框 | `type="digit"` | `type="text"` |
| `time-entry.js` 初始化 | `hours: 0` | `hours: ""` |
| `time-entry.js` `onHoursInput` | `parseFloat(...)` 直接存数字 | 存 `e.detail.value` 原始字符串 |
| `time-entry.js` `calcTotal` | `t.hours` 直接累加 | `parseFloat(t.hours)` 再累加 |
| `time-entry.js` `submitEntry` | `t.hours > 0` 筛选 | `parseFloat(t.hours) > 0` 筛选 |

### 4.3 后台管理输入框太窄

**需求：** 新增人员、项目、部门的输入框太小看不清楚。

**修改：** 增强 `admin.wxss` 样式

| 属性 | 旧值 | 新值 |
|---|---|---|
| 内边距 | `20rpx 24rpx` | `24rpx 28rpx` |
| 字号 | `28rpx` | `30rpx` |
| 边框颜色 | `#E8E8E8` | `#D9D9D9` |
| 背景色 | `#FAFAFA` | `#FFFFFF` |
| 聚焦效果 | 无 | 蓝色边框 + 浅蓝光晕 |

---

## 五、部署到 Zeabur

### 5.1 推送代码到 GitHub

```bash
# 1. 进入后端目录
cd C:\Users\nazha\Documents\New project_文件整理\worklog-api

# 2. 初始化 Git
git init
git add -A
git commit -m "init: worklog-api"

# 3. 如果分支名不是 main
git branch -M main

# 4. 连接到 GitHub（先新建空仓库）
git remote add origin git@github.com:你的用户名/worklog-api.git

# 5. 推送
git push -u origin main
```

### 5.2 添加 SSH Key 到 GitHub（如果没配置过）

```bash
# 查看公钥
cat ~/.ssh/id_ed25519.pub
# 若没有，先生成：
ssh-keygen -t ed25519 -C "你的邮箱@example.com"
```

复制输出的内容 → 浏览器打开 `https://github.com/settings/keys` → **New SSH key** → 粘贴 → **Add SSH key**

### 5.3 创建 GitHub 仓库

1. 浏览器打开 [github.com](https://github.com)，登录
2. 点右上角 **+** → **New repository**
3. 仓库名：`worklog-api`（Public）
4. 点 **Create repository**

### 5.4 Zeabur 部署

1. 浏览器打开 [zeabur.com](https://zeabur.com)，GitHub 登录
2. **创建项目** → **从 GitHub 导入**
3. 如果找不到仓库，先安装 Zeabur GitHub App：
   - 浏览器打开 `https://github.com/apps/zeabur/installations/new`
   - 选择仓库 `worklog-api`，点 **Install**
4. 回到 Zeabur，选 `worklog-api` 导入部署
5. 部署完成获得域名

### 5.5 设置环境变量

Zeabur → 项目 → **Variable** → **Add Variable**：

| Key | Value | 说明 |
|---|---|---|
| `SECRET_KEY` | `my-secret-key-20260713`（可随便填） | 安全密钥 |
| `DEBUG` | `false` | 关闭调试模式 |

### 5.6 后端代码修改后更新

```bash
cd C:\Users\nazha\Documents\New project_文件整理\worklog-api
git add -A
git commit -m "修改说明"
git push
```
Zeabur 会自动检测 GitHub 更新并重新部署。

---

## 六、微信小程序配置

### 6.1 修改 API 地址

`worklog-weapp\app.js` 第 5 行改为：
```javascript
apiBaseUrl: "https://你的域名/api"
```

例如：
```javascript
apiBaseUrl: "https://worklog-api.preview.aliyun-zeabur.cn/api"
```

### 6.2 微信白名单（必须配置）

1. 浏览器打开 [mp.weixin.qq.com](https://mp.weixin.qq.com) → 登录
2. **开发管理** → **开发设置** → **服务器域名**
3. 点 **修改** → **request合法域名** → 添加：
   ```
   https://你的域名
   ```
   例如：`https://worklog-api.preview.aliyun-zeabur.cn`
4. 点保存

### 6.3 开发工具设置

| 设置项 | 操作 |
|---|---|
| 详情 → 本地设置 → 不校验合法域名 | 本地开发时可勾选，上线前取消 |
| 基础库版本 | 建议与灰度的 3.16.2 一致 |

---

## 七、发布体验版

### 7.1 上传小程序

1. 打开微信开发者工具
2. 点顶部菜单 **上传** 按钮
3. 版本号：`1.0.0`、`1.0.1`、`1.0.2` ... 每次+1
4. 备注填写本次修改内容

### 7.2 设为体验版

1. 浏览器打开 [mp.weixin.qq.com](https://mp.weixin.qq.com) → **版本管理**
2. **开发版本** 列表找到刚上传的版本
3. 点 **选为体验版**

### 7.3 添加测试成员

1. mp.weixin.qq.com → **版本管理** → **体验版管理**
2. 添加测试成员的微信号
3. 保存后分享体验版二维码

**注意：** 体验版不需要提交审核，测试成员扫码即可使用。

---

## 八、日常修改流程

### 前端改动（.wxml / .js / .wxss）

```
本地改 → 开发者工具验证 → 点"上传"(版本+1) → 测试成员扫码
```

### 后端改动（.py 文件）

```
本地改 → git add → git commit → git push → Zeabur 自动部署 → 测试成员刷新
```

---

## 九、关键地址汇总

| 项目 | 地址 |
|---|---|
| GitHub 仓库 | `https://github.com/lucky2026zn/worklog-api` |
| 后端 API | `https://worklog-api.preview.aliyun-zeabur.cn/api` |
| 微信小程序后台 | `https://mp.weixin.qq.com` |
| Zeabur | `https://dash.zeabur.com` |
| Zeabur GitHub App 安装 | `https://github.com/apps/zeabur/installations/new` |
| GitHub SSH Key 设置 | `https://github.com/settings/keys` |

---

## 十、常见问题 FAQ

### Q1：Zeabur 网络不稳定会影响小程序吗？

会。小程序是"空壳子"，所有数据都靠后端 API。Zeabur 挂了小程序也用不了。

测试阶段 Zeabur 够用，正式用建议换腾讯云/阿里云（需 ICP 备案）。

### Q2：国内服务器需要 ICP 备案吗？

需要。Zeabur 国内节点需要备案才能绑定自定义域名。
Zeabur 海外节点不需要备案（免费套餐足矣）。

### Q3：没有信用卡怎么部署？

- **Railway**：需要 Visa/Mastercard 验证（不扣费）
- **Zeabur**：支持支付宝/微信支付
- **PythonAnywhere**：免费套餐，无需信用卡

### Q4：体验版和正式版有什么区别？

| | 体验版 | 正式版 |
|---|---|---|
| 需要审核 | ❌ 不需要 | ✅ 需要提交审核 |
| 谁可以用 | 指定的测试成员 | 所有微信用户 |
| 搜索可见 | ❌ 不可搜索 | ✅ 可被搜索到 |
| 适合阶段 | 开发测试 | 正式上线 |

### Q5：上传时提示 "Missing semicolon" 怎么办？

找到报错的 `.js` 文件（如 `_append.js`），删除即可。

### Q6：WXSS 文件编译错误 "unexpected character" 怎么办？

文件编码问题。用 VS Code 打开 → 底部状态栏 → 编码改为 **UTF-8 without BOM**。

### Q7：小程序提示"网络异常"？

可能原因：
- 后端没启动或挂了
- `app.js` 里的 `apiBaseUrl` 写错了（注意是 `https://` 不是 `http://`）
- 微信白名单没配或地址写错了

### Q8：Git push 提示 "Connection was reset" 怎么办？

国内访问 GitHub 不稳定，改用 SSH 方式：
```bash
git remote set-url origin git@github.com:你的用户名/仓库名.git
git push -u origin main
```

### Q9：怎么在文件夹里打开命令行？

打开 `worklog-api` 文件夹 → 在空白处按住 **Shift** + 鼠标右键 → **在此处打开 PowerShell 窗口**

或用 VS Code 打开文件夹 → 按 **Ctrl + `**（键盘左上角 Esc 下面那个键）

### Q10：如何打开 VS Code 终端？

VS Code → **文件** → **打开文件夹** → 选目标目录 → 按 **Ctrl + `**