"""
WSGI config for trade_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')

application = get_wsgi_application()

# WhiteNoise 配置：确保在 Vercel 上正确处理静态文件
# 这会将 WhiteNoise 包装在 Django 应用周围，处理所有对静态文件的请求
application = WhiteNoise(
    application,
    root=os.path.join(os.path.dirname(__file__), '..', 'staticfiles'),
    max_age=31536000,  # 1 year
    mimetypes={
        '.css': 'text/css; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.json': 'application/json',
        '.svg': 'image/svg+xml',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
    }
)

app = application
