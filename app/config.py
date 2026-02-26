import os


class Config:
    # Исправлено: SECRET_KEY берётся из переменной окружения
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    # Исправлено: URI тоже можно переопределить через ENV
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///crm.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
