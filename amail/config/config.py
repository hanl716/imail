"""
Application Configuration for Amail.

This module loads configuration settings primarily from environment variables.
It uses `python-dotenv` to load variables from a `.env` file located in the
project root directory (one level up from the `amail` package directory,
i.e., next to `run.py`).

Key configurations include:
- Flask application settings (SECRET_KEY).
- IMAP server credentials for email fetching.
- API keys and endpoints for external services like Cerebras.ai.
- Filenames for Google Drive related credentials and tokens (actual paths are
  resolved within the GoogleDriveService).

This module is imported by `amail/app/__init__.py` to configure the Flask app.
Fallback values are provided for some settings for development convenience, but
critical secrets like API keys should always be set in the environment.
"""
import os
from dotenv import load_dotenv

# --- Environment Variable Loading ---
# Construct the path to the .env file.
# Assumes this config.py is in 'amail/config/', so '.env' is two levels up.
# If using `run.py` at project root, `run.py` also loads `.env`, providing robustness.
# This explicit load here ensures config is available even if this module is imported directly
# in a context where `run.py` hasn't run (e.g., some testing scenarios or direct script use).
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # print(f"DEBUG: Loaded .env from: {dotenv_path}") # Uncomment for .env loading debug
else:
    # print(f"DEBUG: .env file not found at: {dotenv_path}. Using system environment variables.") # Uncomment for .env loading debug
    pass
# --- End Environment Variable Loading ---


# === Flask Application Settings ===
# SECRET_KEY: Essential for session management, CSRF protection, and flash messages.
#             Should be a long, random string. CHANGE THIS IN PRODUCTION.
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_dev_secret_key_ CHANGE_ME_IN_PROD_!@#$%")
# For Flask-WTF CSRF protection, often uses the same SECRET_KEY.
WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", SECRET_KEY)


# === IMAP Email Account Configuration ===
# These settings are for connecting to the email server to fetch emails.
# It's highly recommended to use environment variables for sensitive credentials.
# The structure supports multiple accounts in theory, but currently "test_account" is hardcoded in use.
EMAIL_ACCOUNTS = {
    "test_account": {
        # IMAP server address (e.g., "imap.gmail.com", "imap.mail.yahoo.com")
        "imap_server": os.getenv("IMAP_SERVER"),
        # Full email address for login
        "email_address": os.getenv("IMAP_EMAIL_ADDRESS"), # Renamed from EMAIL_ADDRESS for clarity
        # Password for the email account. For Gmail/Outlook, consider using App Passwords.
        "password": os.getenv("IMAP_EMAIL_PASSWORD"),    # Renamed from EMAIL_PASSWORD for clarity
        # Default IMAP folder to fetch emails from (e.g., "INBOX", "Archive")
        "folder": os.getenv("IMAP_FOLDER", "INBOX")
    }
}
# Example of how to add a fallback for local development if .env is not used (not recommended for secrets):
# if not EMAIL_ACCOUNTS["test_account"]["imap_server"] and os.getenv('FLASK_ENV') == 'development':
#     print("WARNING: IMAP environment variables not set. Using placeholder config for development.")
#     EMAIL_ACCOUNTS["test_account"]["imap_server"] = "your_imap_server_placeholder"
#     # ... (add other placeholders)


# === Cerebras.ai API Configuration ===
# API Key and Endpoint for Cerebras.ai services.
# These should be set via environment variables for security.
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY") # No default, should be None if not set.
CEREBRAS_API_ENDPOINT = os.getenv("CEREBRAS_API_ENDPOINT", "YOUR_CEREBRAS_API_ENDPOINT_HERE_PLEASE_UPDATE")
# Example of a hypothetical endpoint: CEREBRAS_API_ENDPOINT = "https://api.cerebras.ai/v1/cs-1/nlp"

# --- User Guidance for Cerebras Configuration (printed at app startup if not set) ---
# To use Cerebras.ai features, set these environment variables (e.g., in your .env file):
#   CEREBRAS_API_KEY="your_actual_api_key_from_cerebras"
#   CEREBRAS_API_ENDPOINT="https_your_cerebras_endpoint/api_path"
# If not set, Cerebras-dependent features will be disabled or use mock data.
# --- End User Guidance ---

# Startup check and print warnings if critical Cerebras configs are missing or use default placeholder.
# This helps developers during setup.
if not CEREBRAS_API_KEY:
    print("WARNING: Environment variable CEREBRAS_API_KEY is not set. "
          "Cerebras.ai integration will be disabled or use mock responses.")
if CEREBRAS_API_ENDPOINT == "YOUR_CEREBRAS_API_ENDPOINT_HERE_PLEASE_UPDATE":
    print("WARNING: Environment variable CEREBRAS_API_ENDPOINT is set to its default placeholder. "
          "Please update it to your actual Cerebras API endpoint for live features.")


# === Google Drive Service Related Filenames ===
# These are filenames, not full paths. The GoogleDriveService resolves their full paths
# within the 'amail/config/' directory.
# GOOGLE_CREDENTIALS_FILENAME: Name of the JSON file downloaded from Google Cloud Console.
GOOGLE_CREDENTIALS_FILENAME = 'google_credentials.json'
# TOKEN_FILENAME: Name of the file where OAuth 2.0 tokens are stored after authorization.
TOKEN_FILENAME = 'token.json'
# DRIVE_FOLDER_ID_FILENAME: Name of the file caching the ID of Amail's dedicated Drive folder.
DRIVE_FOLDER_ID_FILENAME = 'drive_folder_id.txt'

# Note on Google Credentials:
# `google_credentials.json` (or the file specified by GOOGLE_CREDENTIALS_FILENAME)
# MUST be placed in the `amail/config/` directory by the user.
# It is gitignored and should not be committed to the repository.
# A `google_credentials.json.template` is provided as a guide.
