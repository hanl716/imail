# Amail: AI-Assisted Email Client

## Project Overview

Amail is a modern, AI-assisted email client designed to provide an intelligent and efficient email experience. Its core goals include:
- Offering an IM-like (instant messaging) interface for email conversations.
- Leveraging AI to provide assistance with email categorization, reply suggestions, and other smart features.
- Supporting cross-platform accessibility (eventual goal).
- Integrating with cloud services like Google Drive for enhanced attachment management.
This project is built with Python and Flask, incorporating various AI and utility libraries.

## Features

Currently implemented features include:

*   User Authentication (Login/Register)
*   IMAP Email Integration (fetching and basic display)
*   IM-like Email View (grouped by sender, sorted by recency)
*   AI-Powered Categorization (rule-based: Finance, Work, Support, Complaint, Suggestion, Promotions).
*   AI-Powered Reply Suggestions (rule-based).
*   Complaint/Suggestion Logging (to CSV, with viewer).
*   Google Drive Integration:
    *   Handles OAuth 2.0 authentication with Google Drive.
    *   Automatically creates/uses a dedicated application folder ("AMailAppStorage") in the user's Google Drive.
*   Attachment Handling:
    *   Detects attachments in emails.
    *   Uploads attachments to the dedicated Google Drive folder.
    *   Displays links to these Drive files in the email view.
*   Cerebras.ai Integration (Mocked):
    *   Basic framework for integrating with Cerebras.ai services.
    *   Configuration placeholders for API key and endpoint.
    *   Service calls are currently mocked and log intended actions.
*   Contact Management:
    *   Allows adding contacts from email senders.
    *   Contacts are stored in a JSON file (`amail/data/contacts.json`).
    *   Basic duplicate contact suggestion based on normalized names.
    *   Dedicated "Contacts" page to view all contacts and potential duplicates.

## Setup Instructions

### Prerequisites
*   Python 3.8+
*   pip (Python package installer)
*   Git

### 1. Cloning the Repository
```bash
git clone <repository_url> # Replace <repository_url> with the actual URL
cd amail-project-directory # Or your chosen directory name
```

### 2. Installing Dependencies
It's highly recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
Then install the required packages:
```bash
pip install -r amail/requirements.txt
```
(Note: `requirements.txt` is located inside the `amail` subdirectory. `run.py` is in the project root, one level above `amail/`. `python-dotenv` in `run.py` will look for `.env` in the root.)

### 3. Configuration (Crucial)

Amail requires several configurations to be set up, primarily through environment variables. Create a `.env` file in the project root directory (the same directory as `run.py`).

**`.env` file contents:**

```env
# Flask Configuration
FLASK_APP=amail.app  # Points to the create_app factory in amil/app/__init__.py
FLASK_DEBUG=True     # Set to False in production
SECRET_KEY=your_very_secret_and_long_flask_app_key # Change this to a random string

# IMAP Email Account Configuration (Replace with your actual credentials)
IMAP_SERVER=your_imap_server.com
EMAIL_ADDRESS=your_email_address@example.com
EMAIL_PASSWORD=your_email_app_password_or_actual_password

# Cerebras.ai API (Optional - features will be mocked if not set)
# CEREBRAS_API_KEY=your_actual_cerebras_api_key
# CEREBRAS_API_ENDPOINT=https_your_cerebras_endpoint/api/v1/some_service

# Google Drive API (Required for attachment uploading)
# No direct .env variables for Google Drive paths, but setup is needed.
# See section below.
```

**Google Drive Setup:**
1.  **Google Cloud Console:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project or select an existing one.
    *   Enable the "Google Drive API" for your project.
    *   Create OAuth 2.0 credentials:
        *   Choose "Desktop app" as the application type.
        *   Give it a name (e.g., "Amail Client").
    *   Download the credentials JSON file. It will likely be named `client_secret_xxxxxxxx.json`.
2.  **Place Credentials File:**
    *   Rename the downloaded JSON file to `google_credentials.json`.
    *   Place this file inside the `amail/config/` directory.
3.  **First-time Authorization:**
    *   When you first run the application and access a feature that uses Google Drive (like viewing the dashboard with attachments or running the `/test_drive_setup` route), the application will attempt to authenticate.
    *   It will print a URL to the console where the Flask app is running.
    *   Copy this URL into your web browser.
    *   Authorize the application to access your Google Drive.
    *   After authorization, you might be redirected to a localhost URL, or Google might show you an authorization code to paste back into the console (depending on the exact OAuth flow variant triggered by the library).
    *   Upon successful authorization, a `token.json` file will be created in `amail/config/` storing your OAuth tokens for future use.

### 4. Running the Application
Once dependencies are installed and configuration is set up:
```bash
python run.py
```
The application will typically be available at `http://0.0.0.0:5000/` or `http://127.0.0.1:5000/`. The auth routes are prefixed with `/auth`, e.g., `http://127.0.0.1:5000/auth/login`.

## Directory Structure

*   `run.py`: Script to run the Flask application.
*   `README.md`: This file.
*   `.env` (User-created): Stores environment variables for configuration.
*   `amail/`: Main application package.
    *   `app/`: Core application logic.
        *   `__init__.py`: Application factory (`create_app`).
        *   `routes.py`: Flask routes for different app sections.
        *   `models.py`: User model (currently in-memory).
        *   `forms.py`: Flask-WTF forms for login, registration.
        *   `email_service.py`: Handles IMAP communication and email parsing.
        *   `ai_assistant.py`: Contains AI logic for categorization, suggestions.
        *   `google_drive_service.py`: Manages Google Drive integration.
        *   `cerebras_service.py`: (Mocked) service for Cerebras.ai integration.
        *   `contact_service.py`: Manages contacts and duplicate detection.
    *   `static/`: Static files (CSS, JavaScript, images).
    *   `templates/`: HTML templates (using Jinja2).
    *   `config/`: Configuration files (`config.py`, `google_credentials.json`, `token.json`, etc.).
    *   `data/`: Data storage files (`complaints_suggestions.csv`, `contacts.json`).
    *   `requirements.txt`: Python package dependencies.
    *   `.gitignore`: Specifies intentionally untracked files by Git.

## Future Work/Roadmap (Optional)

*   **Database Integration:** Replace in-memory/JSON/CSV storage with a robust database.
*   **Advanced AI Models:** Implement real Cerebras.ai calls, train custom models.
*   **Full Email Client Features:** Sending emails, search, notifications.
*   **Enhanced Contact Management:** Merging duplicates, manual editing.
*   **UI/UX Improvements.**
*   **Comprehensive Testing.**

## Contributing (Placeholder)
Contributions are welcome. Please open an issue or submit a pull request.

---
*This README provides a snapshot of the Amail project. Refer to the code and comments for more detailed information.*