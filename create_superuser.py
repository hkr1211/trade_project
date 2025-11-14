# create_superuser.py
import os
import django
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trade_project.settings")
django.setup()

def app(environ, start_response):
    try:
        # 创建或获取用户
        from django.contrib.auth.models import User

        username = "jerry"
        email = "jerry.houyong@gmail.com"
        password = "hy720901"

        # 已存在则直接更新密码
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.email = email
            user.is_superuser = True
            user.is_staff = True
            user.save()
            msg = f"Superuser '{username}' already existed. Password updated."
        else:
            # 创建超级用户（非交互式）
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            msg = f"Superuser '{username}' created successfully."

        status = "200 OK"
        body = (msg + "\n").encode("utf-8")

    except Exception as e:
        status = "500 Internal Server Error"
        body = f"Error: {e}\n".encode("utf-8")

    headers = [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ]
    start_response(status, headers)
    return [body]
