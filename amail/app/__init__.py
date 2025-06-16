from flask import Flask
from flask_login import LoginManager
from .models import User
from amail.config import config as app_config # Import the config module

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    # Load configurations from config.py
    app.config['SECRET_KEY'] = app_config.SECRET_KEY
    app.config['EMAIL_ACCOUNTS'] = app_config.EMAIL_ACCOUNTS
    # For Flask-WTF CSRF protection (can also be set directly or from os.environ)
    app.config['WTF_CSRF_SECRET_KEY'] = app_config.SECRET_KEY


    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # The route for login
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        # User IDs are stored as integers in our simple model
        return User.get_by_id(int(user_id))

    from .routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth') # Added /auth prefix for clarity

    # You might have other blueprints or direct routes here
    # For example, a main blueprint for the app's core functionality
    # from .main import main_bp
    # app.register_blueprint(main_bp)

    return app
