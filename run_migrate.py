# run_migrate.py
import os
import django
from django.core.management import call_command

# 告诉 Django 用哪个 settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trade_project.settings")

django.setup()

def app(environ, start_response):
    """
    一个简单的 WSGI 应用，访问一次就执行 migrate。
    Vercel 的 Python Runtime 只要看到模块里有 app 变量，就会当作 WSGI 处理。
    """
    try:
        # 只允许 GET，防止乱用
        method = environ.get("REQUEST_METHOD", "GET")
        if method != "GET":
            status = "405 Method Not Allowed"
            body = b"Only GET is allowed.\n"
        else:
            # 执行数据库迁移
            call_command("migrate", interactive=False)
            status = "200 OK"
            body = b"Migrations ran successfully.\n"
    except Exception as e:
        status = "500 Internal Server Error"
        body = f"Error while running migrate: {e}\n".encode("utf-8")

    headers = [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]
    start_response(status, headers)
    return [body]
