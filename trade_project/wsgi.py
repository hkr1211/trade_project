"""
WSGI config for trade_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')

# 在 Vercel 环境中创建 /tmp/media 目录
if os.environ.get('VERCEL'):
    media_root = Path('/tmp/media')
    media_root.mkdir(parents=True, exist_ok=True)
    # 创建上传文件所需的子目录
    (media_root / 'drawings' / 'inquiries').mkdir(parents=True, exist_ok=True)
    (media_root / 'drawings' / 'orders').mkdir(parents=True, exist_ok=True)
    (media_root / 'attachments' / 'inquiries').mkdir(parents=True, exist_ok=True)
    (media_root / 'attachments' / 'orders').mkdir(parents=True, exist_ok=True)

application = get_wsgi_application()

app = application
