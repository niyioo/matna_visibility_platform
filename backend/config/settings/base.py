from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="unsafe-dev-secret-key-change-in-production")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# Path of the Django admin. Override in production to keep it off the default URL.
ADMIN_URL = config("ADMIN_URL", default="admin/")

# Serve the OpenAPI schema / Swagger UI. Off by default outside DEBUG.
ENABLE_API_DOCS = config("ENABLE_API_DOCS", default=DEBUG, cast=bool)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",

    "apps.accounts",
    "apps.production",
    "apps.inventory",
    "apps.suppliers",
    "apps.analytics",
]

MIDDLEWARE = [
    "common.middleware.HealthCheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="matna_visibility"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=60, cast=int),
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# Throttle counters must be shared by every Gunicorn worker, so production
# overrides this with a database-backed cache (see production.py).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth is a bearer token in the Authorization header, not a cookie, so CORS
# credentials are deliberately NOT allowed.
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173",
    cast=Csv(),
)
# Lets the SPA read the server-chosen filename on report downloads.
CORS_EXPOSE_HEADERS = ["Content-Disposition"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "300/minute",
        "login": "5/minute",          # per username + IP
        "login_ip": "30/minute",      # per IP (plant staff share one public IP)
        "token_refresh": "60/minute",
    },
    # Number of trusted reverse proxies in front of Django. Set to 1 behind the
    # bundled nginx so throttling keys on the real client IP, not nginx's.
    "NUM_PROXIES": config("NUM_PROXIES", default=None, cast=lambda v: None if v in (None, "") else int(v)),
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Matna Visibility Platform API",
    "DESCRIPTION": "Digital Production & Operational Visibility Platform API",
    "VERSION": "1.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
    "SECURITY": [{"BearerAuth": []}],
    "COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_LIFETIME_MINUTES", default=30, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_LIFETIME_DAYS", default=7, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.CustomTokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "apps.accounts.serializers.ActiveUserTokenRefreshSerializer",
}

# The refresh token lives only in this httpOnly cookie, never in JavaScript-readable
# storage. Scoped to the auth endpoints so it is not sent with ordinary API calls.
AUTH_COOKIE = {
    "NAME": "matna_refresh",
    "PATH": "/api/auth/",
    "SAMESITE": "Strict",
    # Browsers treat http://localhost as secure, so this can stay on in development too.
    "SECURE": config("AUTH_COOKIE_SECURE", default=True, cast=bool),
}

LOG_LEVEL = config("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "common": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

# ── Operational KPI thresholds (drive dashboard alerts and health status) ────
OPERATIONS_THRESHOLDS = {
    # Starch yield (%) — cassava-to-starch benchmark ~25–30%.
    "YIELD_TARGET_PERCENT": config("YIELD_TARGET_PERCENT", default=28, cast=float),
    "YIELD_CRITICAL_PERCENT": config("YIELD_CRITICAL_PERCENT", default=22, cast=float),
    # Above this, a yield is physically implausible and most likely a data-entry error.
    "YIELD_MAX_PLAUSIBLE_PERCENT": config("YIELD_MAX_PLAUSIBLE_PERCENT", default=40, cast=float),
    # Daily downtime (minutes).
    "DOWNTIME_WARNING_MINUTES": config("DOWNTIME_WARNING_MINUTES", default=60, cast=int),
    "DOWNTIME_CRITICAL_MINUTES": config("DOWNTIME_CRITICAL_MINUTES", default=180, cast=int),
    # Raw cassava stock cover, in days of average consumption.
    "STOCK_COVER_WARNING_DAYS": config("STOCK_COVER_WARNING_DAYS", default=3, cast=float),
    "STOCK_COVER_CRITICAL_DAYS": config("STOCK_COVER_CRITICAL_DAYS", default=1, cast=float),
    # Days without a production entry before data is considered stale.
    "STALE_DATA_DAYS": config("STALE_DATA_DAYS", default=2, cast=int),
    # Standard deviations from the 30-day mean that count as an anomaly.
    "ANOMALY_SIGMA": config("ANOMALY_SIGMA", default=2.0, cast=float),
}

# ── Analysis windows, input limits and live refresh (served to the SPA via
#    GET /api/analytics/config/ so the UI never hardcodes them) ──────────────
PLATFORM_SETTINGS = {
    # Default trend window when no dates are given, and the dashboard chart window.
    "TREND_WINDOW_DAYS": config("TREND_WINDOW_DAYS", default=30, cast=int),
    # Dashboard "recent performance" window, compared with the window before it.
    "COMPARISON_WINDOW_DAYS": config("COMPARISON_WINDOW_DAYS", default=7, cast=int),
    # Days of recent consumption used to estimate raw-stock cover.
    "STOCK_COVER_BASIS_DAYS": config("STOCK_COVER_BASIS_DAYS", default=14, cast=int),
    # Longest range accepted by analytics and report exports.
    "MAX_RANGE_DAYS": config("MAX_RANGE_DAYS", default=366, cast=int),
    # A production day cannot record more downtime than it has minutes.
    "MAX_DOWNTIME_MINUTES": 24 * 60,
    # How often live pages (dashboard, inventory, analytics) re-fetch.
    "LIVE_REFRESH_SECONDS": config("LIVE_REFRESH_SECONDS", default=60, cast=int),
    # Void / adjustment reasons.
    "REASON_MIN_LENGTH": 5,
    "REASON_MAX_LENGTH": 500,
}
