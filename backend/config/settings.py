"""
Configuración del backend del Asistente Inteligente para la
Detección y Segmentación de Pólipos en Colonoscopias.

Sistema LOCAL/OFFLINE de desarrollo (Fase 1: imágenes).
"""
import os
from pathlib import Path

# backend/ -> sistema/ -> TASIS/
BASE_DIR = Path(__file__).resolve().parent.parent
SISTEMA_DIR = BASE_DIR.parent
TASIS_DIR = SISTEMA_DIR.parent

SECRET_KEY = "desarrollo-local-no-usar-en-produccion"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "corsheaders",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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
    },
]

# Base de datos local (se usará en Fase 2 para el historial de análisis)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL = "static/"
# Frontend React compilado (frontend/dist) servido por el propio Django,
# de modo que toda la aplicación funciona en un solo origen/puerto.
STATICFILES_DIRS = [SISTEMA_DIR / "frontend" / "dist"]

# Archivos subidos y resultados generados
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# CORS: frontend de desarrollo (Vite) y cualquier origen local
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "America/La_Paz"

# ------------------------------------------------------------------
# Modelo de IA
# ------------------------------------------------------------------
# Ruta del checkpoint .pth. Por defecto usa el modelo ACTUAL (modelo3.pth,
# Val Dice 0.9534, época 27). Se puede sobreescribir con la variable de
# entorno MODELO_POLIPOS_PATH.
MODELO_PATH = Path(
    os.environ.get("MODELO_POLIPOS_PATH", TASIS_DIR / "modelo_vit_polipos_bes50.pth")
)
MODELO_IMG_SIZE = 224
MODELO_PATCH_SIZE = 16
MODELO_EMBED_DIM = 768
