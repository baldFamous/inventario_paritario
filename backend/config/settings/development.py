from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ['*']

# SQLite para desarrollo local rápido
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CORS_ALLOW_ALL_ORIGINS = True
