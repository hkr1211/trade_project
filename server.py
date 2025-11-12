import os
from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')

app = get_wsgi_application()
try:
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
        db_name = str(settings.DATABASES['default']['NAME'])
        if db_name.startswith('/tmp'):
            call_command('migrate', run_syncdb=True, interactive=False, verbosity=0)
except Exception:
    pass
