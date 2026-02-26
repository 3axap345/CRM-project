from flask import Flask
from .config import Config
from .extensions import db, login_manager, migrate
from app.models import User
from app.auth.routes import auth_bp
from app.routes import main_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @login_manager.user_loader
    def load_user(user_id):
        # Исправлено: db.session.get вместо устаревшего query.get
        return db.session.get(User, int(user_id))

    return app
