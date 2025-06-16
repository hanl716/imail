"""
Main application package initializer for Amail.

This file sets up the Flask application factory (`create_app`), initializes extensions like Flask-Login,
loads configuration, and registers blueprints.
"""
from flask import Flask
from flask_login import LoginManager
from .models import User # User model for authentication
from amail.config import config as app_config # Application configuration module

# Initialize Flask-Login manager
login_manager = LoginManager()
# 'auth.login' is the route name for the login page, using the 'auth' blueprint.
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info' # Flash message category for login required messages

def create_app():
    """
    Application factory function to create and configure the Flask app.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configurations from amil/config/config.py
    # SECRET_KEY is crucial for session security and CSRF protection.
    app.config['SECRET_KEY'] = app_config.SECRET_KEY
    # EMAIL_ACCOUNTS holds IMAP server details for fetching emails.
    app.config['EMAIL_ACCOUNTS'] = app_config.EMAIL_ACCOUNTS
    # WTF_CSRF_SECRET_KEY is specifically for Flask-WTF form protection.
    # It can be the same as SECRET_KEY or a different one.
    app.config['WTF_CSRF_SECRET_KEY'] = app_config.SECRET_KEY

    # Cerebras.ai API Configuration (loaded from environment or config.py defaults)
    app.config['CEREBRAS_API_KEY'] = app_config.CEREBRAS_API_KEY
    app.config['CEREBRAS_API_ENDPOINT'] = app_config.CEREBRAS_API_ENDPOINT

    # Log a warning during app startup if Cerebras.ai is not fully configured.
    # This helps in diagnosing issues if AI features seem to be missing.
    if not app.config.get('CEREBRAS_API_KEY') or \
       app.config.get('CEREBRAS_API_ENDPOINT') == "YOUR_CEREBRAS_API_ENDPOINT_HERE_PLEASE_UPDATE":
        # Use app.logger if available (after app context), or print for early config issues.
        # app.logger might not be fully configured here yet.
        print("WARNING: CEREBRAS_API_KEY or CEREBRAS_API_ENDPOINT is not configured. "
              "Cerebras.ai dependent features may be disabled or use mock data.")
    else:
        # Consider app.logger.info for successful configuration messages if desired.
        print("INFO: Cerebras.ai API Key and Endpoint are configured.")

    # Initialize Flask-Login with the app
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login user loader callback.
        Loads a user given their ID.

        Args:
            user_id (str): The ID of the user to load (usually from the session).

        Returns:
            User: The User object, or None if the user_id is not found.
        """
        # User IDs are stored as integers in our simple in-memory model
        return User.get_by_id(int(user_id))

    # Import and register blueprints
    # Blueprints help in organizing routes and views.
    from .routes import auth_bp  # Authentication routes (login, register, etc.)
    app.register_blueprint(auth_bp, url_prefix='/auth') # Prefix all auth routes with /auth

    # Example for other potential blueprints:
    # from .main_routes import main_bp # For core app routes like dashboard (if not in auth_bp)
    # app.register_blueprint(main_bp)
    #
    # from .api_routes import api_bp # For REST API endpoints
    # app.register_blueprint(api_bp, url_prefix='/api')

    return app
