"""
Django settings for Veeps API.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
import logging
import os  # pylint: disable=unused-import

import environ
import boto3

ROOT_DIR = environ.Path(__file__) - 2

# Load operating system environment variables and then prepare to use them
env = environ.Env()

# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
]

THIRD_PARTY_APPS = [
    "drf_spectacular",
    "rest_framework",
    "rest_framework.authtoken",
    "authlib",
    "django_extensions",
    "django_filters",
    "drf_api_logger",
    "django_createsuperuserwithpassword",
]

LOCAL_APPS = [
    "apps.users",
    "apps.api",
]

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware",
]

# DEBUG
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DEBUG", default=True)
SECRET_KEY = env.str("SECRET_KEY", default="Please set .env file")

# DOMAINS
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])
DOMAIN = env.str("DOMAIN", default="")

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_PORT = env.int("EMAIL_PORT", default="1025")
EMAIL_HOST = env.str("EMAIL_HOST", default="mailhog")

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [
    ("Martin Anev", "martin.anev@triumphtech.com"),
    ("Steve Butler", "stevebutler@triumphtech.com"),
]

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": env.str("POSTGRES_DB", default="postgresdatabase"),
        "USER": env.str("POSTGRES_USER", default="postgresuser"),
        "PASSWORD": env.str("POSTGRES_PASSWORD", default="Please set .env file"),
        "HOST": env.str("POSTGRES_HOST", default="postgres"),
        "PORT": env.int("POSTGRES_PORT", default=5432),
    },
}

# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = "UTC"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR("staticfiles"))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/staticfiles/"

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [
    str(ROOT_DIR("static")),
]

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(ROOT_DIR("media"))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": STATICFILES_DIRS,
        "OPTIONS": {
            "debug": DEBUG,
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# PASSWORD STORAGE SETTINGS
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

# PASSWORD VALIDATION
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "authlib.backends.EmailBackend",
]

# Custom user app defaults
# Select the correct user model
AUTH_USER_MODEL = "users.User"

# API Auth Key
API_AUTH_KEY = env.str("API_AUTH_KEY", default="PleaseChangeThisKey")

# DJANGO REST FRAMEWORK
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "UPLOADED_FILES_USE_URL": False,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FileUploadParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": env.int("DEFAULT_PAGE_SIZE", default=25),
    "EXCEPTION_HANDLER": "apps.api.exceptions.custom_exception_handler_simple",
}

# Spectacular settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Veeps elemental API",
    "DESCRIPTION": "API to stream AWS elemental SRT/RTMP streams",
    "VERSION": "1.0.9",
    "SERVE_INCLUDE_SCHEMA": False,
}

# AWS Configuration
AWS_ACCOUNT_ID = env.str("AWS_ACCOUNT_ID", default="")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", default="")
AWS_DEFAULT_REGION = env.str("AWS_DEFAULT_REGION", default="us-east-1")
AWS_REGION_NAME = env.str("AWS_REGION_NAME", default=AWS_DEFAULT_REGION)
AWS_SESSION_TOKEN = env.str("AWS_SESSION_TOKEN", default="")
AWS_ACCOUNT_NUMBER = env.str("AWS_ACCOUNT_NUMBER", default="")
AWS_SNS_TOPIC = env.str("AWS_SNS_TOPIC", default="Cloudwatch-hook")

if AWS_ACCOUNT_NUMBER == "":
    try:
        # get AWS_ACCOUNT_NUMBER from boto3 directly
        AWS_ACCOUNT_NUMBER = boto3.client("sts").get_caller_identity().get("Account")
    except Exception as ex:
        logger = logging.getLogger(__name__)
        logger.error(f"Couldn't auto-detect AWS account number {ex}")

# See if we're running locally, or inside AWS
LOCAL_DEV = env.str("LOCAL_DEV", default=True)

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "django": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": True,
        },
    },
}

if not LOCAL_DEV:
    # If we're running in AWS, then we can use watchtower.

    # Create a boto3 log client
    boto3_logs_client = boto3.client("logs", region_name=AWS_REGION_NAME)

    # Setup watchtower
    LOGGING["handlers"]["watchtower"] = {
        "class": "watchtower.CloudWatchLogHandler",
        "boto3_client": boto3_logs_client,
        "log_group_name": env.str("LOG_GROUP_NAME", default="veeps_api_develop"),
        "level": "DEBUG",
    }

    # Add watchtower as a handler
    LOGGING["root"]["handlers"].append("watchtower")
    LOGGING["loggers"]["django"]["handlers"].append("watchtower")

CORS_ALLOW_ALL_ORIGINS = True

DRF_API_LOGGER_DATABASE = True
DRF_LOGGER_QUEUE_MAX_SIZE = 1
DRF_API_LOGGER_EXCLUDE_KEYS = ["password", "token", "access", "refresh"]
# Sensitive data will be replaced with "***FILTERED***".
DRF_API_LOGGER_METHODS = []  # Default to empty list (Log all the requests).
DRF_API_LOGGER_PATH_TYPE = "ABSOLUTE"  # Default to ABSOLUTE if not specified
# Possible values are ABSOLUTE, FULL_PATH or RAW_URI


DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_S3_VOD_INPUT_BUCKET_NAME = env.str("AWS_S3_VOD_INPUT_BUCKET_NAME", default="veeps-vod-input-staging")
AWS_S3_VOD_CLIP_BUCKET_NAME = env.str("AWS_S3_VOD_CLIP_BUCKET_NAME", default="veeps-vod-clip-staging")
AWS_S3_SIGNATURE_VERSION = env.str("AWS_S3_SIGNATURE_VERSION", default="s3v4")
AWS_DEFAULT_ACL = env.str("AWS_DEFAULT_ACL", default=None)
AWS_S3_VERIFY = True
AWS_PRESIGNED_EXPIRY = env.str("AWS_PRESIGNED_EXPIRY", default=3600)
AWS_VOD_S3_TRIGGER_LAMBDA_FUNCTION_NAME = env.str("AWS_VOD_S3_TRIGGER_LAMBDA_FUNCTION_NAME", default="vod-s3-trigger")
