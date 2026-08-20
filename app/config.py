import os


class Config:
    # Исправлено: SECRET_KEY берётся из переменной окружения
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    # Исправлено: URI тоже можно переопределить через ENV
    database_url = os.environ.get("DATABASE_URL", "sqlite:///crm.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
