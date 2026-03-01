import os
from datetime import timedelta


class Config:
    # База данных
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ["cookies"]
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
        "txt"
    }
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB