#coding: utf-8
# Django settings for appconfman project.
try:
    import dev
    DEV = True
except:
    DEV = False

import os.path
USR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
from django.contrib.auth.hashers import make_password, check_password
ROOT_PATH = BASE_DIR

BACKS_LOGIN_URL = '/manager/login'
LOGIN_URL = '/login'
PAGE_LIMIT = 20

# TODO CHANGE 111.230.234.177 to REAL GIT SERVER
GIT_API_SERVER = DEV and 'http://127.0.0.1:18088' or 'http://111.230.234.177:18088'

#session settings
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 86400
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


DEBUG = True
ALLOWED_HOSTS = ['*']


ADMINS = (
    ('anlim', 'anlim@quseit.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'kaizhi2db',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'dbuser',
        'PASSWORD': 'Quseit520',
        'HOST': '127.0.0.1',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '5432',
    }
}
#set db cache
#CACHE_BACKEND = 'db://cache_table'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
        'TIMEOUT': 86400,
        'OPTIONS': {
            'MAX_ENTRIES': 2000
        }
    }
}

"""
#django-redis-cache
#from django.core.cache import cache
#cache.set('key', 'value', timeout='86400')
#cache.get('key')
#redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_POOL = 0
#docs:
CACHES = {
    'default':{
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '%s:%s' % (REDIS_HOST, REDIS_PORT),
        'OPTIONS':{
            'DB': REDIS_POOL, #default 0
        }
    }
}
"""
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE='Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'zh-Hans'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
#MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
#MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = USR_ROOT + '/media/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
  # Put strings here, like "/home/html/static" or "C:/www/django/static".
  # Always use forward slashes, even on Windows.
  # Don't forget to use absolute paths, not relative paths.
    USR_ROOT +'/static/',
)


# Make this unique, and don't share it with anybody.
SECRET_KEY = '#%lx&y2s9trk4k9pz^c0&0x^x!z$5gn*ew6w0yumu1@icewxtf'

# AUTH相关

JWT_AUTH = {
    'PAYLOAD_TO_USER': 'xcx.wechat_user_authentication.payload_to_user',
    'USER_TO_PAYLOAD': 'xcx.wechat_user_authentication.user_to_payload',
}

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.CommonMiddleware',
]
CORS_ORIGIN_ALLOW_ALL = True
"""
CORS_ORIGIN_WHITELIST = (
    'hostname.example.com',
)
"""
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
)

ROOT_URLCONF = 'apps.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'apps.wsgi.application'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # 'django.contrib.admindocs',
    'apps.backs',
    'apps.app',
    'apps.api',
    'apps.xcx',
    'corsheaders',
    'crispy_forms',
    'xadmin',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(ROOT_PATH, 'django.log'),
            'maxBytes': 1024*1024*5, # 5MB
            'backupCount': 0,
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s-%(asctime)s@@%(message)s',
            #'format': '%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(process)d %(message)s',
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s|%(message)s'
        },
    },
    'loggers': {
        'apps.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'apps.models': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps.api.logger':{
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}



PASSWORD_HASHERS = [

    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedSHA1PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
]




STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

GIT_REPO = '/data/www/vhosts/kaizhi-git-server/repos/repo-org'
GIT_REPO_URL = GIT_API_SERVER+'/api/create/new/repo'

GIT_FILE_URL =  GIT_API_SERVER+'/api/create/filestream'
GIT_RENAME_FILE =  GIT_API_SERVER+'/api/rename/file'
GIT_RENAME_REPO =  GIT_API_SERVER+'/api/rename/repo'
GIT_DELETE_REPO =  GIT_API_SERVER+'/api/delete/repo'
GIT_DELETE_FOLDER =  GIT_API_SERVER+'/api/delete/folder'
GIT_DELETE_FILE =  GIT_API_SERVER+'/api/delete/file'
GIT_DELETE_BRANCH =  GIT_API_SERVER+'/api/delete/branch'
GIT_MERGE_BRANCH =  GIT_API_SERVER+'/api/merge/branch'
GIT_DISCUSS_FILE =  GIT_API_SERVER+'/api/modify/discuss/file'
GIT_MODIFY_FILE =  GIT_API_SERVER+'/api/modify/file'
GIT_RECOVER_FILE =  GIT_API_SERVER+'/api/recover/file'
GIT_COPY_FILE =  GIT_API_SERVER+'/api/copy/file'
GIT_COMMIT_FILE =  GIT_API_SERVER+'/api/commit/file'


GIT_CHECKOUT_MASTER = GIT_API_SERVER+'/api/checkout/master'
GIT_DIRPATH = GIT_API_SERVER+'/api/create/new/dirpath'
GIT_DIFF = GIT_API_SERVER+'/api/file/diff'
GIT_BRANCH_DIFF = GIT_API_SERVER+'/api/branch/diff'

GIT_GET_LIST = GIT_API_SERVER+'/api/repo/file/list'
GIT_FILE_CONTENT = GIT_API_SERVER+'/api/repo/file/content'

GIT_DIR_PATH = GIT_API_SERVER+'/api/repo/get/dir'
GIT_BRANCH_URL = GIT_API_SERVER+'/api/create/new/branch'

## TYPE IN GIT DB
GIT_TYPE_DIR = 0
GIT_TYPE_FILE = 1

GIT_ROLE_MASTER = '0'
GIT_ROLE_BRANCH = '1'

## TYPE OF DIFF
GIT_DIFF_FILE = '0'
GIT_DIFF_BRANCH = '1'

##
ERR_FILE_USED = 1001
ERR_FILE_USED = 1001
