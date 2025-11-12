# Foreign Trade System (Django)

本项目为 Django 应用，已适配本地运行与 Vercel 部署。

## 本地运行
- 进入目录：`cd trade_project`
- 激活环境：`./venv/Scripts/Activate.ps1`
- 数据库迁移：`python manage.py migrate`
- 收集静态：`python manage.py collectstatic --noinput`
- 启动：`python manage.py runserver 0.0.0.0:8000`

## 配置说明
- `trade_project/trade_project/settings.py`
  - `SECRET_KEY` 支持从环境变量读取
  - 支持 `DATABASE_URL`（优先使用外部数据库；默认 `sqlite3`）
  - 使用 `Whitenoise` 提供静态文件

## 部署到 Vercel
- 需要 Node 与 Vercel CLI：`npm i -g vercel`
- 登录：`vercel login`
- 环境变量（Production）：
  - `SECRET_KEY`：随机密钥
  - `DATABASE_URL`：推荐 Postgres 连接串
- 构建与部署：在 `trade_project` 目录运行 `vercel --prod`
- 入口：`server.py`（WSGI），`vercel.json` 已配置 `builds/routes/buildCommand`

## 目录结构（关键）
- `trade_project/manage.py`：Django 管理入口
- `trade_project/trade_project/settings.py`：配置
- `trade_project/trade_project/wsgi.py`：WSGI 入口
- `trade_project/server.py`：Vercel WSGI 入口（exports `app`）
- `orders/`：业务应用、模板与迁移

## 许可证
- 自行根据业务需要添加许可证声明。
