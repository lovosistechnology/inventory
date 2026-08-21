from pathlib import Path
import os

from dotenv import load_dotenv


# -----------------------
# BASE DIRECTORY
# -----------------------

BASE_DIR = Path(__file__).resolve().parent.parent


# -----------------------
# LOAD ENVIRONMENT VARIABLES
# -----------------------

load_dotenv()  # For local development using .env


# -----------------------
# SECRET KEY & DEBUG
# -----------------------

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-^wgd3myc9zodm0cj93i^zd+(mko!3na%oem+a!34o&^0#mq^f0"
)

DEBUG = os.environ.get("DEBUG", "False") == "True"


# -----------------------
# ALLOWED HOSTS
# -----------------------

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost,inventory.lovosis.in,145.79.12.143"
).split(",")


# -----------------------
# CSRF TRUSTED ORIGINS
# -----------------------

CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    "https://inventory.lovosis.in,http://inventory.lovosis.in,http://145.79.12.143,localhost,127.0.0.1"
).split(",")


# -----------------------
# INSTALLED APPS
# -----------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "inventory",  # Your app
]


# -----------------------
# MIDDLEWARE
# -----------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# -----------------------
# ROOT URL
# -----------------------

ROOT_URLCONF = "core.urls"


# -----------------------
# TEMPLATES
# -----------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# -----------------------
# WSGI APPLICATION
# -----------------------

WSGI_APPLICATION = "core.wsgi.application"


# -----------------------
# DATABASE CONFIGURATION
# -----------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# -----------------------
# PASSWORD VALIDATION
# -----------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# -----------------------
# INTERNATIONALIZATION
# -----------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# -----------------------
# STATIC FILES
# -----------------------

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# -----------------------
# MEDIA FILES
# -----------------------

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


# -----------------------
# LOGIN / LOGOUT REDIRECTS
# -----------------------

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"


# -----------------------
# SECURITY HEADERS (PRODUCTION)
# -----------------------

if not DEBUG:

    SECURE_SSL_REDIRECT = True

    # Nginx terminates SSL and forwards HTTPS information
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# -----------------------
# DEFAULT AUTO FIELD
# -----------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
