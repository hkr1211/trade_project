import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')

app = get_wsgi_application()
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
    # 只要不是 DEBUG 或检测到 Vercel 环境变量，就尝试收集静态
    vercel_detected = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV') or os.environ.get('VERCEL_URL'))
    should_collect = (not getattr(settings, 'DEBUG', False)) or vercel_detected
    if should_collect and not os.environ.get('NO_COLLECTSTATIC'):
        build_id = os.environ.get('APP_BUILD_ID', 'prod')
        static_flag = f"/tmp/django_static_collected_{build_id}"
        if not os.path.exists(static_flag):
            # 执行一次收集
            call_command('collectstatic', interactive=False, verbosity=0)
            with open(static_flag, 'w') as f:
                f.write('ok')
except Exception:
    # 若收集失败，不影响应用启动；但可能导致生产缺少静态资源
    pass
