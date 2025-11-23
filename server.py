import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')
if os.environ.get('RUN_MIGRATIONS_ON_START', 'false').lower() == 'true':
    flag_path = '/tmp/django_migrated'
    try:
        if not os.path.exists(flag_path):
            call_command('migrate', run_syncdb=True, interactive=False, verbosity=0)
            with open(flag_path, 'w') as f:
                f.write('ok')
    except Exception:
        try:
            with open(flag_path, 'w') as f:
                f.write('err')
        except Exception:
            pass

# 收集静态文件（生产/无服务器环境可靠执行）
try:
    vercel_detected = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV') or os.environ.get('VERCEL_URL'))
    should_collect = (not getattr(settings, 'DEBUG', False)) or vercel_detected
    if should_collect and not os.environ.get('NO_COLLECTSTATIC'):
        build_id = os.environ.get('APP_BUILD_ID', 'prod')
        static_flag = f"/tmp/django_static_collected_{build_id}"
        admin_base = os.path.join(getattr(settings, 'STATIC_ROOT', '/tmp/staticfiles'), 'admin', 'css', 'base.css')
        need_collect = True
        if os.path.exists(static_flag) and os.path.exists(admin_base):
            need_collect = False
        if need_collect:
            call_command('collectstatic', interactive=False, verbosity=0)
            if not os.path.exists(static_flag):
                with open(static_flag, 'w') as f:
                    f.write('ok')
except Exception:
    pass

app = get_wsgi_application()
