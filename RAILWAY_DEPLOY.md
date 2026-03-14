# Railway 部署指南

## 前置准备

- [Railway 账号](https://railway.app)（可用 GitHub 登录）
- 项目已推送到 GitHub

---

## 第一步：创建项目

1. 登录 Railway，点击 **New Project**
2. 选择 **Deploy from GitHub repo**
3. 授权并选择你的仓库
4. Railway 会自动检测到 `railway.toml`，直接继续

---

## 第二步：添加 PostgreSQL 数据库

1. 在项目页面点击 **+ New** → **Database** → **Add PostgreSQL**
2. 等待数据库创建完成（约 30 秒）
3. Railway 会自动将 `DATABASE_URL` 注入到你的服务，**不需要手动复制**

---

## 第三步：配置环境变量

点击你的 Web 服务 → **Variables** 标签页，添加以下变量：

| 变量名 | 值 | 说明 |
|---|---|---|
| `SECRET_KEY` | 随机字符串（见下方生成方法） | Flask Session 密钥，必须设置 |
| `VIKA_API_TOKEN` | 你的维格表 API Token | 如不用维格表同步可留空 |
| `VIKA_DATASHEET_ID` | 你的维格表数据表 ID | 如不用维格表同步可留空 |

> `DATABASE_URL` 由 Railway 数据库服务自动注入，**不要手动填写**。

**生成 SECRET_KEY（在本地终端运行）：**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 第四步：部署

环境变量填好后，点击 **Deploy** 或推送代码会自动触发部署。

Railway 会按 `railway.toml` 中的命令执行：
```
flask db upgrade && gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120
```

即：先自动完成数据库建表，再启动服务。

---

## 第五步：创建管理员账号

服务启动后，点击 Web 服务 → **Settings** → **Deploy** → 找到 **Start Command**，临时改为：

```bash
python create_user.py
```

点击 Redeploy，在 Railway 的日志里按提示输入用户名和密码。

> 更简单的方式：点击服务的 **Shell** 标签（Railway 提供在线终端），直接运行：
> ```bash
> python create_user.py
> ```

完成后把 Start Command 改回原来的内容（或直接删掉，会自动读取 railway.toml）。

---

## 第六步：绑定域名（可选）

1. 点击 Web 服务 → **Settings** → **Networking**
2. 点击 **Generate Domain** 获得免费的 `*.up.railway.app` 域名
3. 如有自定义域名，点击 **Custom Domain** 按提示配置 CNAME

---

## 常见问题

**部署失败，日志显示数据库连接错误**

确认 PostgreSQL 服务和 Web 服务在同一个 Railway 项目里，`DATABASE_URL` 会自动注入。

**登录后立刻掉线（Session 丢失）**

`SECRET_KEY` 未设置或每次重启随机生成。确保在环境变量里固定设置了 `SECRET_KEY`。

**`flask db upgrade` 报错**

检查日志具体错误。常见原因是数据库还未就绪，Railway 通常会自动重试。

**如何重置某个用户密码**

在 Railway 的 Shell 里运行：
```bash
python create_user.py --reset-password 用户名 新密码
```

**如何查看所有用户**

```bash
python create_user.py --list
```

---

## 费用说明

Railway 免费额度：每月 $5 用量（约够跑一个小项目）。PostgreSQL 数据库会持续计费，注意控制用量或升级到付费计划。
