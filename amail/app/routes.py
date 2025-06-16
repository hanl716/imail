"""
Defines the Flask routes for the Amail application, organized within a Blueprint.

This module handles user authentication (registration, login, logout),
the main email dashboard display, feedback logging, contact management,
and test routes for Google Drive and Cerebras AI integration.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .forms import LoginForm, RegistrationForm # User authentication forms
from .models import User # User model for authentication
from .email_service import fetch_emails # Service for fetching emails via IMAP
from .ai_assistant import AIAssistant # AI helper for categorization, suggestions
from .google_drive_service import GoogleDriveService, CREDENTIALS_PATH as G_CREDENTIALS_PATH # Google Drive integration
from .cerebras_service import CerebrasService # (Mocked) Cerebras AI integration
from .contact_service import ContactService # Contact management service

from collections import defaultdict # For grouping emails
from email.utils import parsedate_to_datetime, unquote # Email utilities
from datetime import timezone # For timezone-aware datetime objects
import csv # For writing to complaints_suggestions.csv
import os # For path operations

# Blueprint for authentication and main application routes
# All routes defined in this blueprint will be prefixed with '/auth' (see app/__init__.py)
auth_bp = Blueprint('auth', __name__)

# Initialize services
# CerebrasService can be initialized here using app.config once the app context is available,
# or passed around. For simplicity with blueprints, often service instances are created
# when needed or made available on `g` or `current_app`.
# Let's initialize it lazily or ensure it's configured in create_app and accessed via current_app.
# For now, AIAssistant will try to get it from current_app if not passed.
# We'll make an instance of CerebrasService and pass it to AIAssistant.
# Note: This global `ai_assistant` instance will not have `cerebras_service` until `create_app` or similar.
# This is a common issue with global object instantiation vs. app context.
# A better pattern is to initialize services within create_app or use Flask extensions.

# Temporary solution: Instantiate CerebrasService here, it will fetch config from current_app when used within a request.
# This assumes CerebrasService constructor is lightweight and primarily stores config paths/values.
# It will attempt to fetch its necessary configurations (API key, endpoint) from current_app.config
# when its methods (like call_cerebras_api) are invoked within a request context.
cerebras_service_instance = CerebrasService()
# The AIAssistant is initialized with this Cerebras service instance.
# AIAssistant can then internally decide whether/how to use Cerebras features.
ai_assistant = AIAssistant(cerebras_service_instance=cerebras_service_instance)

# --- Path Helper Functions for Data Files (to respect testing overrides) ---

def get_data_dir():
    """Returns the appropriate data directory path, respecting test overrides."""
    return current_app.config.get('DATA_DIR_OVERRIDE') or \
           os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

def get_feedback_file_path():
    """Returns the appropriate feedback log file path, respecting test overrides."""
    return current_app.config.get('FEEDBACK_FILE_PATH_OVERRIDE') or \
           os.path.join(get_data_dir(), 'complaints_suggestions.csv')

# Headers for the feedback CSV file - remains constant.
FEEDBACK_FILE_HEADERS = ["type", "sender", "subject", "date", "summary", "source_account"]
# --- End Path Helper Functions ---


# --- File I/O Helper Functions (using path helpers) ---
def ensure_data_dir_exists():
    """Ensures that the data directory exists. Creates it if not."""
    data_dir = get_data_dir()
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            current_app.logger.info(f"Created data directory: {data_dir}")
        except OSError as e:
            current_app.logger.error(f"Error creating data directory {data_dir}: {e}")

def log_feedback_to_csv(feedback_data):
    """
    Logs feedback data (complaints/suggestions) to the feedback CSV file.
    Creates the file and writes headers if it doesn't exist.
    Uses `get_feedback_file_path()` to determine the correct file path.

    Args:
        feedback_data (dict): A dictionary containing the feedback information.
                              Keys should match `FEEDBACK_FILE_HEADERS`.
    """
    ensure_data_dir_exists() # Ensure the correct data directory is there
    feedback_file = get_feedback_file_path()
    file_exists = os.path.isfile(feedback_file)
    try:
        with open(feedback_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FEEDBACK_FILE_HEADERS)
            if not file_exists: # If file doesn't exist or is empty, write header
                writer.writeheader()
            writer.writerow(feedback_data)
    except IOError as e:
        current_app.logger.error(f"Error writing to CSV {feedback_file}: {e}")
# --- End File I/O Helper Functions ---

# --- Authentication Routes ---

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles user registration.
    GET: Displays the registration form.
    POST: Processes registration form submission. If valid, creates a new user
          and redirects to the login page.
    """
    if current_user.is_authenticated: # If user is already logged in, redirect to dashboard
        return redirect(url_for('auth.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit(): # Processes form data on POST request
        # Password hashing is handled within the User model's __init__ or set_password method.
        # User creation also adds the user to the in-memory store (see models.py).
        User(username=form.username.data, password=form.password.data)
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login')) # Redirect to login page after successful registration
    return render_template('register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    GET: Displays the login form.
    POST: Processes login form submission. If valid, logs in the user
          and redirects to the dashboard or the originally requested page.
    """
    if current_user.is_authenticated: # If user is already logged in, redirect to dashboard
        return redirect(url_for('auth.dashboard'))

    form = LoginForm()
    if form.validate_on_submit(): # Processes form data on POST request
        user = User.get_by_username(form.username.data)
        # Check if user exists and password is correct
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect(url_for('auth.login')) # Redirect back to login page on failure

        # Log in the user using Flask-Login's login_user function
        login_user(user, remember=form.remember_me.data)
        flash('Logged in successfully.', 'success')

        # Redirect to the page the user was trying to access before being prompted to log in,
        # or to the dashboard if no specific page was requested.
        next_page = request.args.get('next')
        return redirect(next_page or url_for('auth.dashboard'))
    return render_template('login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required # Ensures only logged-in users can access this route
def logout():
    """
    Handles user logout.
    Logs out the current user and redirects to the login page.
    """
    logout_user() # Logs out the user via Flask-Login
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

# --- Main Application Routes ---

@auth_bp.route('/dashboard')
@login_required # User must be logged in to see the dashboard
def dashboard():
    """
    Displays the main email dashboard.
    Fetches emails, processes them (categorization, suggestions, attachment uploads),
    groups them by sender, and renders the dashboard template.
    """
    raw_emails = [] # Stores emails fetched from the email_service
    grouped_emails = defaultdict(list) # Stores emails grouped by sender for display

    # --- Email Fetching ---
    # Configuration for the primary email account (e.g., "test_account") is retrieved.
    # In a multi-account system, this would iterate over all configured user accounts.

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
        # Initialize GoogleDriveService once if there are emails with attachments to process
        # This avoids re-initializing (and potentially re-authenticating if token is bad) for every email.
        # Actual authentication will only happen if service methods are called and creds are not valid.
        gdrive_service = None
        gdrive_app_folder_id = None

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

            # Log complaint or suggestion to CSV file
            if email_data['category'] in ["Complaint", "Suggestion"]:
                feedback_info = ai_assistant.extract_complaint_suggestion_info(email_data)
                log_feedback_to_csv(feedback_info)

            # --- Attachment Uploading to Google Drive ---
            # This section handles uploading attachments if present and not already processed (conceptual).
            # Note: Robust "already uploaded" detection would require persistent storage of email metadata.
            if email_data.get('attachments'):
                if not gdrive_service: # Initialize GoogleDriveService only if needed
                    try:
                        # Check for google_credentials.json before attempting to initialize service
                        if not os.path.exists(G_CREDENTIALS_PATH) or os.path.getsize(G_CREDENTIALS_PATH) == 0:
                            flash("Google Drive credentials ('google_credentials.json') are missing or empty. Attachments cannot be processed.", "warning")
                            current_app.logger.warning("google_credentials.json missing/empty. Attachment uploads skipped.")
                        else:
                            gdrive_service = GoogleDriveService()
                            # Authenticate and get/create the app folder ID once per request if needed.
                            # This might trigger the OAuth flow on first use or if token is invalid.
                            gdrive_app_folder_id = gdrive_service.get_or_create_app_folder()
                            if not gdrive_app_folder_id:
                                flash("Could not get or create Google Drive app folder. Attachments will not be uploaded.", "danger")
                                current_app.logger.error("Failed to get/create GDrive app folder. Attachment uploads will be skipped for this session.")
                                gdrive_service = None # Disable further GDrive attempts this session if folder fails
                    except Exception as e:
                        flash(f"Error initializing Google Drive service: {e}. Attachments will not be uploaded.", "danger")
                        current_app.logger.error(f"GDrive initialization error: {e}", exc_info=True)
                        gdrive_service = None # Disable further GDrive attempts

                if gdrive_service and gdrive_app_folder_id: # Proceed if service and folder ID are valid
                    for attachment in email_data['attachments']:
                        # Upload if 'payload' exists and 'drive_file_id' is not yet set
                        if not attachment.get('drive_file_id') and attachment.get('payload'):
                            try:
                                current_app.logger.info(f"Uploading attachment: {attachment['filename']} (Size: {attachment['size']}) to Drive.")
                                drive_id = gdrive_service.upload_attachment(
                                    filename=attachment['filename'],
                                    content_type=attachment['content_type'],
                                    file_data_bytes=attachment['payload'],
                                    parent_folder_id=gdrive_app_folder_id
                                )
                                if drive_id:
                                    attachment['drive_file_id'] = drive_id
                                    current_app.logger.info(f"Successfully uploaded {attachment['filename']}, Drive ID: {drive_id}")
                                else: # Upload failed
                                    current_app.logger.error(f"Failed to upload attachment {attachment['filename']} to Drive (no Drive ID returned).")
                                    flash(f"Failed to upload attachment: {attachment['filename']}", "warning")
                                # Remove payload after attempt to free memory, regardless of success for this simplified flow.
                                # In a robust system, you might retry or handle payloads differently.
                                del attachment['payload']
                            except Exception as e: # Catch any exception during upload
                                current_app.logger.error(f"Exception during attachment upload for {attachment['filename']}: {e}", exc_info=True)
                                flash(f"Error uploading attachment {attachment['filename']}: {e}", "danger")
                                if 'payload' in attachment: # Ensure payload is removed even on error
                                    del attachment['payload']
                        elif attachment.get('payload'):
                            # If payload exists but we are not uploading (e.g., drive_file_id already exists or GDrive service failed)
                            # still remove payload to free memory.
                            del attachment['payload']
            # --- End Attachment Uploading ---

            # Add processed email_data to the corresponding sender's list
            grouped_emails[email_data['from_email']].append(email_data)

        # --- Email Sorting ---
        # Sort emails within each sender's group by their datetime object (most recent first)
        for sender_email_key in grouped_emails:
            grouped_emails[sender_email_key].sort(key=lambda x: x['datetime_obj'], reverse=True)

        # Sort the sender groups themselves by the datetime of the most recent email in each group
        sender_latest_email_date = {
            sender: emails[0]['datetime_obj']
            for sender, emails in grouped_emails.items() if emails # Ensure group is not empty
        }
        sorted_senders = sorted(
            sender_latest_email_date.keys(),
            key=lambda sender: sender_latest_email_date[sender],
            reverse=True # Most recent sender group first
        )
        # Reconstruct grouped_emails into a standard dict in the new sorted order of senders
        # This ensures the template iterates through senders in the desired order.
        final_grouped_emails = {sender: grouped_emails[sender] for sender in sorted_senders}
        # --- End Email Sorting ---

    else: # No raw_emails fetched
        final_grouped_emails = {} # Pass an empty dict to the template

    return render_template('dashboard.html', title='Dashboard', grouped_emails=final_grouped_emails)

# --- Feedback and Contact Management Routes ---

@auth_bp.route('/feedback_log')
@login_required
def feedback_log():
    """
    Displays the log of complaints and suggestions from the CSV file.
    """
    feedback_items = []
    ensure_data_dir_exists() # Ensure 'data' directory exists

    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile) # Reads rows as dictionaries
                for row in reader:
                    feedback_items.append(row)
        except IOError as e: # File system error
            flash(f"Error reading feedback log: {e}", "danger")
            current_app.logger.error(f"IOError reading CSV {FEEDBACK_FILE}: {e}")
        except csv.Error as e: # CSV format error
            flash(f"Error parsing feedback log CSV: {e}", "danger")
            current_app.logger.error(f"CSV parsing error for {FEEDBACK_FILE}: {e}")

    # Sort feedback items by date (descending - newest first)
    # Assumes 'date' column exists and is string-sortable (e.g., ISO format).
    feedback_items.sort(key=lambda x: x.get('date', ''), reverse=True)

    return render_template('feedback_log.html', title='Feedback Log', feedback_items=feedback_items)


@auth_bp.route('/contacts')
@login_required
def contacts_page():
    """
    Displays the contacts page, showing all contacts and potential duplicates.
    Uses ContactService, respecting test configuration for file paths.
    """
    contacts_file = current_app.config.get('CONTACTS_FILE_PATH_OVERRIDE') # Get test path if set
    data_dir = current_app.config.get('DATA_DIR_OVERRIDE') # Get test data dir if set
    contact_service = ContactService(contacts_file_path=contacts_file, data_dir_path=data_dir)

    all_contacts = contact_service.contacts # Access loaded contacts

    # Sort contacts by name for consistent display in the "All Contacts" table
    all_contacts.sort(key=lambda c: c.get('name', '').lower())

    duplicate_groups = contact_service.suggest_duplicates() # Get groups of potential duplicates

    return render_template('contacts.html',
                           title='Contacts',
                           contacts=all_contacts,
                           duplicate_groups=duplicate_groups)

@auth_bp.route('/contacts/add_from_email')
@login_required
def add_contact_from_email():
    """
    Adds a contact based on email and name provided in query parameters.
    Typically triggered from a link/button next to an email sender.
    Redirects to the contacts page.
    """
    email = request.args.get('email')
    name = request.args.get('name') # This might be pre-parsed from "Sender Name <email>"

    if not email: # Basic validation
        flash('Email address is required to add a contact.', 'danger')
        return redirect(request.referrer or url_for('auth.dashboard')) # Redirect back or to dashboard

    # If name is not provided or is just the email, attempt to derive a cleaner name.
    if not name or name == email:
        name_part = email.split('@')[0]
        name = name_part.replace('.', ' ').replace('_', ' ').replace('-', ' ').title() if name_part else email

    contacts_file = current_app.config.get('CONTACTS_FILE_PATH_OVERRIDE')
    data_dir = current_app.config.get('DATA_DIR_OVERRIDE')
    contact_service = ContactService(contacts_file_path=contacts_file, data_dir_path=data_dir)

    contact, message = contact_service.add_contact(name=name, email_address=email)

    if contact: # If add_contact returned a contact object (success or update)
        flash(message, 'success')
    else: # If add_contact returned None (e.g., validation error within service)
        flash(message, 'danger')

    # Redirect to the main contacts page to see the newly added/updated contact
    return redirect(url_for('auth.contacts_page'))

# --- Test Routes ---

@auth_bp.route('/test_cerebras')
@login_required
def test_cerebras():
    """
    A test route for Cerebras AI integration.
    Calls the (currently mocked) CerebrasService to analyze sample text.
    Displays the raw JSON response from the service.
    """
    # CerebrasService is initialized globally (blueprint level) and passed to AIAssistant.
    # Its methods use current_app.config for API key/endpoint.

    # Log a warning if Cerebras is not configured, supplementing global/service-level warnings.
    if not current_app.config.get('CEREBRAS_API_KEY') or \
       current_app.config.get('CEREBRAS_API_ENDPOINT') == "YOUR_CEREBRAS_API_ENDPOINT_HERE_PLEASE_UPDATE":
        flash("Cerebras API Key or Endpoint is not configured. Using mock Cerebras response.", "warning")

    sample_text_for_analysis = ("This is a sample email body for testing Cerebras integration. "
                                "It discusses a project meeting and an upcoming invoice for Project Phoenix.")

    # Use the globally instantiated cerebras_service_instance for the test.
    # This instance is the same one potentially used by the AIAssistant.
    # Alternatively, `CerebrasService()` could be called here to create a new instance.
    analysis_result = cerebras_service_instance.analyze_email_text_with_cerebras(sample_text_for_analysis)

    flash(f"Cerebras API call (mocked) attempted. Result: {analysis_result.get('status', 'unknown status')}", "info")

    # Display the full (mocked) JSON response for debugging/testing.
    return f"""<h2>Cerebras Test Result:</h2>
               <p>Note: This currently uses a MOCKED CerebrasService.</p>
               <pre>{current_app.json.dumps(analysis_result, indent=2)}</pre>
               <a href="{url_for('auth.dashboard')}">Back to Dashboard</a>
            """


@auth_bp.route('/test_drive_setup')
@login_required
def test_drive_setup():
    """
    A test route for Google Drive integration setup.
    Initiates authentication and attempts to get/create the app's dedicated folder on Drive.
    Provides user guidance via flashed messages and logging.
    """
    # Check if google_credentials.json exists and is not empty.
    # This file is essential for the OAuth flow.
    if not os.path.exists(G_CREDENTIALS_PATH) or os.path.getsize(G_CREDENTIALS_PATH) == 0:
        error_msg = ("IMPORTANT: `google_credentials.json` is missing or empty in 'amail/config/'. "
                     "Please download your OAuth 2.0 client credentials (Desktop app type) from "
                     "Google Cloud Console and place the file there. Authentication cannot proceed.")
        flash(error_msg, "danger")
        current_app.logger.error(f"Google credentials file not found or empty at {G_CREDENTIALS_PATH}")
        return f"Google Drive setup error: {error_msg}", 500 # Return an error response

    # Initial user guidance for the OAuth flow.
    flash("Attempting Google Drive setup. If this is the first time, "
          "please monitor the console output of this Flask application. "
          "You may need to open a URL in your browser, authorize the application, "
          "and potentially copy an authorization code back to the console if prompted by the Google library.", "info")
    current_app.logger.info(
        "Starting Google Drive setup test. User must ensure 'google_credentials.json' is in 'amail/config/'. "
        "If this is the first authorization, follow any printed URL or browser prompts."
    )

    try:
        drive_service_instance = GoogleDriveService() # Initialize the service
        # The authenticate() method handles token loading, refreshing, or running the full OAuth flow.
        # This call might block and print to console if user interaction is needed for auth.
        service_client = drive_service_instance.authenticate()

        if service_client:
            flash("Google Drive authentication successful. Service client obtained.", "success")
            current_app.logger.info("Google Drive authentication successful.")

            # Attempt to get or create the dedicated application folder.
            folder_id = drive_service_instance.get_or_create_app_folder(service_client)
            if folder_id:
                success_msg = (f"Successfully obtained/created app folder '{drive_service_instance.APP_FOLDER_NAME}' "
                               f"on Google Drive. Folder ID: {folder_id}")
                flash(success_msg, "success")
                current_app.logger.info(f"App folder '{drive_service_instance.APP_FOLDER_NAME}' available with ID: {folder_id}")
                return f"{success_msg}<br><a href='{url_for('auth.dashboard')}'>Back to Dashboard</a>", 200
            else: # Should not happen if get_or_create_app_folder is robust and service_client is valid
                flash("Failed to get or create app folder ID, even after successful authentication.", "danger")
                current_app.logger.error("Could not get or create app folder ID post-authentication.")
                return "Google Drive setup failed: Could not get or create app folder ID.", 500
        else: # Should be caught by exceptions within authenticate() if creds are bad
            flash("Google Drive authentication failed to return a service client. Check logs.", "danger")
            current_app.logger.error("Google Drive authentication did not return a service client.")
            return "Google Drive setup failed: Authentication did not yield a service client.", 500
    except FileNotFoundError as fnf_error: # Specifically for credentials.json missing during the flow
        flash(f"CRITICAL: {str(fnf_error)} - Ensure 'google_credentials.json' is correctly placed.", "danger")
        current_app.logger.critical(f"Google Drive setup failed due to missing credentials file: {str(fnf_error)}")
        return f"Google Drive setup failed: {str(fnf_error)}", 500
    except Exception as e: # Catch-all for other errors during the process
        flash(f"An unexpected error occurred during Google Drive setup: {str(e)}", "danger")
        current_app.logger.error(f"Test Drive Setup failed with an unexpected error: {e}", exc_info=True)
        return f"Google Drive setup failed with an error: {str(e)}", 500

# Note: The @login_manager.user_loader callback is correctly placed in app/__init__.py.
# No need to duplicate it here.
