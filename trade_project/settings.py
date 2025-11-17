"""
Django settings for trade_project project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== 基础安全设置 ====================
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-tvc%m0j60@st3kjl2_s-p+!zf4id*wesls3ne%*%q9vjdj#h9b')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# 允许的主机
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.vercel.app',
    '.supabase.co',
    '.yj-ql.com',
]

# 如果在生产环境，添加所有主机（部署后应改为实际域名）
if not DEBUG:
    ALLOWED_HOSTS.append('*')

# ==================== 应用配置 ====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'trade_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'trade_project.wsgi.application'

# ==================== 数据库配置 ====================
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # 生产环境：使用 PostgreSQL（Supabase 或其它托管 PG）
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

    # 如果URL中包含sslmode参数，则使用它，否则不强制SSL
    # 这样可以兼容不同的数据库环境
    if 'sslmode' not in DATABASE_URL.lower():
        DATABASES['default'].setdefault('OPTIONS', {})
        # 连接保活设置
        DATABASES['default']['OPTIONS'].update({
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        })
elif os.environ.get('VERCEL'):
    # Vercel 环境但没有 DATABASE_URL 时，使用临时 SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/db.sqlite3',
        }
    }
else:
    # 本地开发，使用 SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==================== 密码验证 ====================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================== 国际化 ====================
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('zh-hans', '中文'),
    ('en', 'English'),
    ('ja', '日本語'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ==================== 静态文件配置 ====================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise 配置
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==================== 媒体文件配置 ====================
MEDIA_URL = '/media/'

# 根据环境选择媒体文件存储位置
if os.environ.get('VERCEL'):
    # Vercel环境：使用临时目录
    MEDIA_ROOT = '/tmp/media'
    try:
        os.makedirs(MEDIA_ROOT, exist_ok=True)
    except Exception:
        pass
else:
    # 本地开发：使用项目目录
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 如果配置了Supabase，使用Supabase存储
if os.environ.get('SUPABASE_SERVICE_KEY') and os.environ.get('SUPABASE_URL'):
    STORAGES = {
        'default': {
            'BACKEND': 'trade_project.storage_backends.SupabaseStorage'
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        }
    }

# ==================== Session 配置 ====================
# 统一使用数据库存储session
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# 生产环境：启用安全cookie
if not DEBUG:
    SESSION_COOKIE_SECURE = True

# ==================== CSRF 配置 ====================
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://*.supabase.co',
    'https://trade.yj-ql.com',
    'https://*.yj-ql.com',
]

# 代理设置（Vercel 在负载均衡器后面）
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ==================== 生产环境安全设置 ====================
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Vercel 已经处理了 SSL
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

# ==================== 日志配置 ====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'orders': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ==================== 其他设置 ====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
