import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')

app = get_wsgi_application()
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
