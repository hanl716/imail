from amail.app import create_app
import os

# Load environment variables from .env file if it exists in the project root
# This is especially useful if not using `flask run` which handles .flaskenv/.env automatically
from dotenv import load_dotenv

# Construct the path to the .env file expected to be in the same directory as run.py
# (which should be the project root, one level above the 'amail' package directory)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # print(f"Loaded environment variables from: {dotenv_path}") # For debugging
else:
    # print(f".env file not found at: {dotenv_path}. Relying on system environment variables.") # For debugging
    pass


# Check if FLASK_APP is set, if not, set it to 'amail' (the package name)
# This helps when `flask` CLI commands are used directly sometimes,
# though create_app() directly uses the 'amail' package.
if os.environ.get('FLASK_APP') is None:
    os.environ['FLASK_APP'] = 'amail' # Or more specifically 'amail.app:create_app' if structure demands

app = create_app()

if __name__ == '__main__':
    # Ensure FLASK_DEBUG from .env is correctly interpreted as boolean for app.run()
    # os.environ.get returns string; 'True', 'true', '1' are common true values.
    flask_debug_str = os.environ.get('FLASK_DEBUG', 'False').lower()
    debug_mode = flask_debug_str in ['true', '1', 't']

    # Get port from environment or default to 5000
    port = int(os.environ.get('FLASK_PORT', 5000))

    # Host '0.0.0.0' makes the server accessible externally if needed (e.g., in a Docker container)
    # For local development, '127.0.0.1' is also common.
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')

    app.run(debug=debug_mode, host=host, port=port)
