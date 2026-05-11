import os
from datetime import timedelta


class Config:
    # База данных
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_VERIFY_SUB = False
    JWT_REFRESH_COOKIE_PATH = "/token-refresh"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Файлы
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {
        "pdf", "doc", "docx",
        "xls", "xlsx",
        "ppt", "pptx",
        "txt",
        "png", "jpg", "jpeg", "gif",
        "zip", "rar"
    }
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB

    # SMTP
    SMTP_HOST = os.getenv("SMTP_HOST", None)
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    MAIL_FROM = os.getenv("MAIL_FROM", "noreply@department.local")