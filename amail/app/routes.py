from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .forms import LoginForm, RegistrationForm
from .models import User
# Removed 'users' import as it's managed within User model
# Removed werkzeug.security import as hashing is in User model
from .email_service import fetch_emails
from .ai_assistant import AIAssistant
from .google_drive_service import GoogleDriveService, CREDENTIALS_PATH as G_CREDENTIALS_PATH # Import service and path
from collections import defaultdict
from email.utils import parsedate_to_datetime
from datetime import timezone
import csv
import os

auth_bp = Blueprint('auth', __name__)
ai_assistant = AIAssistant()
# Potentially initialize GoogleDriveService globally if it's lightweight and settings are fixed,
# or initialize it per request/session if settings can change or for better resource management.
# For a test route, initializing it directly in the route is fine.

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
FEEDBACK_FILE = os.path.join(DATA_DIR, 'complaints_suggestions.csv')
FEEDBACK_FILE_HEADERS = ["type", "sender", "subject", "date", "summary", "source_account"]

def ensure_data_dir_exists():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def log_feedback_to_csv(feedback_data):
    ensure_data_dir_exists()
    file_exists = os.path.isfile(FEEDBACK_FILE)
    try:
        with open(FEEDBACK_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FEEDBACK_FILE_HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(feedback_data)
    except IOError as e:
        current_app.logger.error(f"Error writing to CSV {FEEDBACK_FILE}: {e}")


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Password hashing is done in the User model's __init__ or set_password
        user = User(username=form.username.data, password=form.password.data)
        # Users are added to the in-memory store by the User class constructor
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        flash('Logged in successfully.', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('auth.dashboard'))
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    raw_emails = []
    grouped_emails = defaultdict(list)

    email_accounts_config = current_app.config.get('EMAIL_ACCOUNTS', {})
    if "test_account" in email_accounts_config:
        account_config = email_accounts_config["test_account"]
        if account_config.get("imap_server") and \
           account_config.get("email_address") and \
           account_config.get("password"):
            try:
                # Fetch emails for the "test_account"
                # The account_name is now part of each email dict from fetch_emails
                raw_emails = fetch_emails("test_account")
                if not raw_emails:
                    flash("No emails found or unable to fetch emails for 'test_account'. Check server, credentials, or folder.", "info")
            except Exception as e:
                flash(f"Error fetching emails for 'test_account': {e}", "danger")
                current_app.logger.error(f"Error fetching emails for test_account: {e}", exc_info=True)
        else:
            flash("IMAP server, email address, or password for 'test_account' is not configured. Cannot fetch emails.", "warning")
    else:
        flash("No 'test_account' configured in EMAIL_ACCOUNTS. Cannot fetch emails.", "warning")

    # Process and group emails
    if raw_emails:
        for email_data in raw_emails:
            # Parse date string to datetime object for sorting
            dt = parsedate_to_datetime(email_data['date'])
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None: # Naive datetime
                email_data['datetime_obj'] = dt.replace(tzinfo=timezone.utc) # Assume UTC
            else: # Timezone-aware datetime
                email_data['datetime_obj'] = dt

            # Categorize email using AI Assistant
            email_data['category'] = ai_assistant.categorize_email(email_data)
            # Generate reply suggestions
            email_data['reply_suggestions'] = ai_assistant.generate_reply_suggestions(email_data)

            # Log complaint or suggestion
            if email_data['category'] in ["Complaint", "Suggestion"]:
                feedback_info = ai_assistant.extract_complaint_suggestion_info(email_data)
                log_feedback_to_csv(feedback_info)

            grouped_emails[email_data['from_email']].append(email_data)

        # Sort emails within each group by date (most recent first)
        for sender_email_key in grouped_emails: # Use sender_email_key to avoid clash with sender var later
            grouped_emails[sender_email_key].sort(key=lambda x: x['datetime_obj'], reverse=True)

        # Sort the groups themselves by the date of the most recent email in each group
        # This creates a list of tuples: (sender_email, list_of_emails)
        # sorted_grouped_emails = sorted(
        #     grouped_emails.items(),
        #     key=lambda item: item[1][0]['datetime_obj'] if item[1] else None, # item[1] is the list of emails
        #     reverse=True
        # )
        # Convert back to a dictionary for easier template access, or pass the sorted list
        # For now, defaultdict keeps insertion order for Python 3.7+, if items were added in sorted order.
        # A more robust sort of senders by their most recent email:

        sender_latest_email_date = {
            sender: emails[0]['datetime_obj']
            for sender, emails in grouped_emails.items() if emails
        }

        sorted_senders = sorted(
            sender_latest_email_date.keys(),
            key=lambda sender: sender_latest_email_date[sender],
            reverse=True
        )

        # Reconstruct grouped_emails in the new sorted order of senders
        final_grouped_emails = {sender: grouped_emails[sender] for sender in sorted_senders}

    else: # No raw_emails
        final_grouped_emails = {}

    return render_template('dashboard.html', grouped_emails=final_grouped_emails)


@auth_bp.route('/feedback_log')
@login_required
def feedback_log():
    feedback_items = []
    ensure_data_dir_exists() # Ensure directory exists before trying to read
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    feedback_items.append(row)
        except IOError as e:
            flash(f"Error reading feedback log: {e}", "danger")
            current_app.logger.error(f"Error reading CSV {FEEDBACK_FILE}: {e}")
        except csv.Error as e:
            flash(f"Error parsing feedback log CSV: {e}", "danger")
            current_app.logger.error(f"Error parsing CSV {FEEDBACK_FILE}: {e}")

    # Sort by date, assuming 'date' is in ISO format or string sortable
    # For more robust sorting, parse to datetime objects if necessary
    feedback_items.sort(key=lambda x: x.get('date', ''), reverse=True)

    return render_template('feedback_log.html', feedback_items=feedback_items)


@auth_bp.route('/test_drive_setup')
@login_required # Or remove login_required if it's a purely backend/CLI triggered test for admins
def test_drive_setup():
    # User Instructions for first-time setup
    if not os.path.exists(G_CREDENTIALS_PATH) or os.path.getsize(G_CREDENTIALS_PATH) == 0:
        flash("IMPORTANT: `google_credentials.json` is missing or empty in 'amail/config/'. "
              "Please download your OAuth 2.0 client credentials from Google Cloud Console "
              "and place the file there. Authentication cannot proceed without it.", "danger")
        current_app.logger.error(f"Google credentials file not found or empty at {G_CREDENTIALS_PATH}")
        return "Google Drive setup cannot proceed: `google_credentials.json` missing or empty. Check logs and UI messages.", 500

    flash("Attempting Google Drive setup. If this is the first time, "
          "please monitor the console output of the Flask application. "
          "You might need to open a URL in your browser and authorize the application, "
          "then potentially copy an authorization code back to the console if prompted.", "info")
    current_app.logger.info(
        "Starting Google Drive setup test. User should ensure 'google_credentials.json' is in 'amail/config/'. "
        "If first time, follow printed URL to authorize."
    )

    try:
        drive_service_instance = GoogleDriveService()
        service_client = drive_service_instance.authenticate() # This might involve console interaction

        if service_client:
            flash("Google Drive authentication successful.", "success")
            current_app.logger.info("Google Drive authentication successful.")

            folder_id = drive_service_instance.get_or_create_app_folder(service_client)
            if folder_id:
                flash(f"Successfully obtained/created app folder '{drive_service_instance.APP_FOLDER_NAME}'. Folder ID: {folder_id}", "success")
                current_app.logger.info(f"App folder '{drive_service_instance.APP_FOLDER_NAME}' ID: {folder_id}")
                return f"Google Drive setup successful! App Folder ID: {folder_id}", 200
            else:
                flash("Failed to get or create app folder ID.", "danger")
                current_app.logger.error("Could not get or create app folder ID.")
                return "Google Drive setup failed: Could not get or create app folder ID.", 500
        else:
            flash("Google Drive authentication failed to return a service client.", "danger")
            current_app.logger.error("Google Drive authentication did not return a service client.")
            return "Google Drive setup failed: Authentication did not return a service client.", 500
    except FileNotFoundError as fnf_error:
        # This specific error is caught if credentials.json is missing during the flow.
        flash(str(fnf_error), "danger")
        current_app.logger.critical(str(fnf_error))
        return f"Google Drive setup failed: {str(fnf_error)}", 500
    except Exception as e:
        flash(f"An error occurred during Google Drive setup: {e}", "danger")
        current_app.logger.error(f"Test Drive Setup failed with an error: {e}", exc_info=True)
        return f"Google Drive setup failed with an error: {e}", 500


# This will be needed by Flask-Login
# It should be in __init__.py or a similar central place,
# but models.py is also fine for this simple setup with in-memory users.
# For now, I'll add it to models.py and adjust if Flask-Login complains.
# Actually, better to put it in __init__.py as per instructions.

# @login_manager.user_loader # This decorator needs login_manager instance
# def load_user(user_id):
# return User.get_by_id(int(user_id))
