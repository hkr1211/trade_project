"""
Django settings for trade_project project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-tvc%m0j60@st3kjl2_s-p+!zf4id*wesls3ne%*%q9vjdj#h9b')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'  # 改为 DEBUG

# 允许的主机
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.vercel.app',
    '.supabase.co',
]

# 如果在生产环境，添加实际域名
if not DEBUG:
    ALLOWED_HOSTS.append('*')  # 临时允许所有，部署后改为实际域名

# Application definition
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

# Database Configuration
# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # 生产环境：使用 PostgreSQL（Supabase 或其它托管 PG）
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }

    # 连接保活设置（可保留）
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS'].update({
        'connect_timeout': 10,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5,
    })

elif os.environ.get('VERCEL'):
    # Vercel 环境但没有 DATABASE_URL 时，退回临时 SQLite
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

    
    print(f"Database configured: {DATABASES['default']['ENGINE']}")  # 调试用
    


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'  # 改为中国时区
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

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise 配置
# 使用 CompressedStaticFilesStorage 避免 manifest 问题
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# 媒体文件配置（用户上传的文件）
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
if os.environ.get('VERCEL'):
    MEDIA_ROOT = '/tmp/media'
    try:
        os.makedirs(MEDIA_ROOT, exist_ok=True)
    except Exception:
        pass

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== Session 配置 ====================
# 关键修复：在 Vercel 无服务器环境，使用数据库 session 而不是 signed cookies
# signed cookies 会导致 cookie 过大，特别是有用户数据时
if DATABASE_URL:
    # 生产环境：使用数据库存储 session（Supabase）
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_AGE = 1209600  # 2 weeks
else:
    # 开发环境：使用默认的数据库 session
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ==================== 安全设置 ====================
# CSRF 设置
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://*.supabase.co',
    'https://trade.yj-ql.com',
    'https://*.yj-ql.com'
]

# 代理设置（Vercel 在负载均衡器后面）
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 生产环境的额外安全设置
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Vercel 已经处理了 SSL
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Cookie 安全
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

# ==================== 日志配置（用于调试 Vercel 部署）====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
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
    },
}

if os.environ.get('SUPABASE_SERVICE_KEY') and os.environ.get('SUPABASE_URL'):
    DEFAULT_FILE_STORAGE = 'trade_project.storage_backends.SupabaseStorage'
    MEDIA_URL = "/media/"  # 不重要，真正的 URL 由 storage backend 决定