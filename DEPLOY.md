# PDPTool Render 部署指南

部署后公网地址：Render 会自动生成 `https://pdptool-xxx.onrender.com`

---

## 第一步：注册 Render

1. 打开 https://render.com
2. 点 "Get Started" → 用 GitHub 账号登录
3. 授权 Render 访问你的 GitHub

---

## 第二步：创建 Web Service

1. 点右上角 **"New +"** → 选 **"Web Service"**
2. 选择仓库 `ablancetheduke/Software-architecture-design-group-assignment`
3. 填配置：

| 项目 | 值 |
|------|-----|
| Name | `pdptool` |
| Region | 选 Singapore 或 Oregon |
| Build Command | `pip install -r requirements_web.txt` |
| Start Command | `python web_app.py` |
| Instance Type | **Free** |

4. 点 **"Advanced"** → 添加环境变量：

```
DEEPSEEK_API_KEY = sk-你的密钥（在 pdptool_config.json 里找）
```

5. 点底部 **"Create Web Service"**

---

## 第三步：等待部署

Render 会自动：
1. 克隆你的 GitHub 仓库
2. `pip install` 装依赖
3. 启动 FastAPI 服务
4. 给你一个 `https://pdptool-xxx.onrender.com` 的公网地址

看到 **"Your service is live"** 就好了。**任何人打开那个网址就能用。**

---

## 以后更新代码

直接 `git push` 到 GitHub，Render 会自动检测并重新部署，不用手动操作。

---

## 注意

- 免费实例 15 分钟没人访问会休眠，下次打开等 30 秒自动唤醒
- API Key 存在 Render 的环境变量里，不会泄露
- 所有人的数据共享同一个数据库
