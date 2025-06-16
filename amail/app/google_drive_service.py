"""
Manages interactions with Google Drive API.

This service handles OAuth 2.0 authentication, creation/retrieval of a dedicated
application folder in Google Drive, and uploading files (e.g., email attachments)
to this folder. It requires `google_credentials.json` (OAuth client secrets)
and stores obtained OAuth tokens in `token.json`. The ID of the application's
Drive folder is cached in `drive_folder_id.txt`.
These files are expected to be in the `amail/config/` directory.
"""
import os
import io # For io.BytesIO, used with MediaIoBaseUpload
import json # For reading/writing token.json (though Google library handles this mostly)
from google.auth.transport.requests import Request # For token refresh
from google.oauth2.credentials import Credentials # For handling OAuth credentials
from google_auth_oauthlib.flow import InstalledAppFlow # For OAuth 2.0 authorization code flow
from googleapiclient.discovery import build # To build the Drive API service client
from googleapiclient.errors import HttpError # For handling Google API errors
from googleapiclient.http import MediaIoBaseUpload # For resumable file uploads
from flask import current_app # For logging within a Flask application context

# --- Path Definitions ---
# APP_ROOT determines the root directory of the 'amail' package.
# This is used to construct absolute paths to configuration files, ensuring they are found
# regardless of where the script is run from (within the app context).
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Resolves to 'amail/'
CONFIG_DIR = os.path.join(APP_ROOT, 'config') # Path to 'amail/config/'

# Full paths to credential and token files.
# `google_credentials.json`: User must download this from Google Cloud Console.
# `token.json`: Stores OAuth tokens obtained after successful authorization.
# `drive_folder_id.txt`: Caches the ID of the app's dedicated folder on Google Drive.
CREDENTIALS_PATH = os.path.join(CONFIG_DIR, 'google_credentials.json')
TOKEN_PATH = os.path.join(CONFIG_DIR, 'token.json')
FOLDER_ID_PATH = os.path.join(CONFIG_DIR, 'drive_folder_id.txt')
# --- End Path Definitions ---

class GoogleDriveService:
    """
    Service class for interacting with Google Drive.
    Handles authentication, app folder management, and file uploads.
    """
    # SCOPES define the level of access requested to Google Drive.
    # 'drive.file': Per-file access to files created or opened by the app.
    #               Allows creation of new files/folders. Does not grant access to all files on Drive.
    # Other scopes like 'drive.metadata.readonly' or 'drive' (full access) can be used if needed.
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    # Name of the dedicated folder Amail will use in the user's Google Drive.
    APP_FOLDER_NAME = "AMailAppStorage"

    def __init__(self):
        """
        Initializes the GoogleDriveService.
        Sets up internal state for credentials, API service client, and app folder ID.
        Attempts to load a cached app folder ID from file.
        """
        self.creds = None  # Stores Google OAuth credentials
        self.service = None # Stores the built Google Drive API service client
        self.app_folder_id = None # Stores the ID of the app's dedicated folder on Drive
        self._load_app_folder_id() # Load cached folder ID on initialization

    def _load_app_folder_id(self):
        """
        Loads the app folder ID from a local cache file (`drive_folder_id.txt`).
        This avoids querying Drive API for the folder ID on every app start if already known.
        """
        if os.path.exists(FOLDER_ID_PATH):
            try:
                with open(FOLDER_ID_PATH, 'r') as f:
                    self.app_folder_id = f.read().strip()
                if self.app_folder_id:
                    if current_app:
                        current_app.logger.info(f"Loaded App Folder ID: {self.app_folder_id}")
                    else:
                        print(f"Loaded App Folder ID: {self.app_folder_id}")
            except IOError as e:
                if current_app:
                    current_app.logger.error(f"Error reading folder ID file: {e}")
                else:
                    print(f"Error reading folder ID file: {e}")

    def _save_app_folder_id(self, folder_id):
        """
        Saves the given app folder ID to the local cache file (`drive_folder_id.txt`).

        Args:
            folder_id (str): The Google Drive folder ID to save.
        """
        # Ensure the config directory exists (it should, but good to be safe)
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR) # Create 'amail/config/' if it's missing
            except OSError as e:
                log_func = current_app.logger.error if current_app else print
                log_func(f"Critical error: Could not create config directory {CONFIG_DIR}: {e}")
                return # Cannot save folder_id if config dir cannot be made

        try:
            with open(FOLDER_ID_PATH, 'w') as f:
                f.write(folder_id if folder_id else '') # Write empty string if folder_id is None/empty
            self.app_folder_id = folder_id # Update instance variable
            log_func = current_app.logger.info if current_app else print
            log_func(f"Saved App Folder ID: '{folder_id}' to {FOLDER_ID_PATH}")
        except IOError as e:
            log_func = current_app.logger.error if current_app else print
            log_func(f"Error saving app folder ID to {FOLDER_ID_PATH}: {e}")

    def authenticate(self):
        """
        Handles the OAuth 2.0 authentication flow for Google Drive.
        It tries to load existing tokens, refreshes them if expired, or runs the
        full authorization code flow if no valid tokens are found.
        The user needs `google_credentials.json` in `amail/config/` for the flow.

        Returns:
            googleapiclient.discovery.Resource: The authenticated Google Drive API service client.

        Raises:
            Exception: If authentication fails or the service cannot be built.
        """
        log_info = current_app.logger.info if current_app else print
        log_warning = current_app.logger.warning if current_app else print
        log_error = current_app.logger.error if current_app else print

        # Attempt to load credentials from the token file (token.json)
        if os.path.exists(TOKEN_PATH) and os.path.getsize(TOKEN_PATH) > 0:
            try:
                self.creds = Credentials.from_authorized_user_file(TOKEN_PATH, self.SCOPES)
                log_info("Loaded credentials from token.json.")
            except ValueError as e: # Handles malformed token.json
                log_warning(f"Error loading token.json: {e}. Will attempt re-authentication.")
                self.creds = None
            except Exception as e: # Catch other potential errors
                log_error(f"Unexpected error loading token.json: {e}. Will attempt re-authentication.")
                self.creds = None

        # If credentials are not loaded, or invalid/expired, then authenticate.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                log_info("Credentials expired. Attempting to refresh token...")
                try:
                    self.creds.refresh(Request())
                    log_info("Token refreshed successfully.")
                except Exception as e: # Refresh token might be revoked or other issues
                    log_error(f"Failed to refresh token: {e}. Initiating full authentication flow.")
                    self._run_auth_flow() # Fallback to full flow if refresh fails
            else: # No valid credentials or no refresh token, run full auth flow
                log_info("No valid credentials found or refresh token missing. Initiating full authentication flow.")
                self._run_auth_flow()

            # Save the (newly obtained or refreshed) credentials for the next run
            if self.creds:
                try:
                    with open(TOKEN_PATH, 'w') as token_file:
                        token_file.write(self.creds.to_json())
                    log_info(f"Credentials saved to {TOKEN_PATH}.")
                except IOError as e:
                    log_error(f"Error saving credentials token to {TOKEN_PATH}: {e}")

        if not self.creds: # If still no credentials after all attempts
             msg = "Failed to obtain Google Drive credentials after authentication flow."
             log_error(msg)
             raise Exception(msg)

        # Build and return the Google Drive API service client
        try:
            self.service = build('drive', 'v3', credentials=self.creds)
            log_info("Google Drive API service client built successfully.")
            return self.service
        except Exception as e: # Catch errors during service build
            log_error(f"Failed to build Google Drive service client: {e}", exc_info=True)
            raise Exception(f"Failed to build Google Drive service: {e}")


    def _run_auth_flow(self):
        """
        Runs the OAuth 2.0 installed application authorization flow.
        This typically involves the user opening a URL in a browser to authorize
        the application. `google_credentials.json` must be present.
        Updates `self.creds` with the obtained credentials.

        Raises:
            FileNotFoundError: If `google_credentials.json` is not found.
            Exception: If any other error occurs during the flow.
        """
        log_info = current_app.logger.info if current_app else print
        log_error = current_app.logger.error if current_app else print
        log_critical = current_app.logger.critical if current_app else print

        if not os.path.exists(CREDENTIALS_PATH) or os.path.getsize(CREDENTIALS_PATH) == 0:
            # This is a critical setup error.
            msg = (f"CRITICAL: Google OAuth credentials file ('{os.path.basename(CREDENTIALS_PATH)}') "
                   f"not found or empty in '{CONFIG_DIR}'. "
                   "Please download it from Google Cloud Console (OAuth 2.0 Desktop client) "
                   "and place it correctly to enable Google Drive features.")
            log_critical(msg)
            raise FileNotFoundError(msg) # Fail fast if credentials are not there

        try:
            auth_guidance_msg = ("Attempting Google Drive OAuth flow. "
                                 "If this is the first authorization for this application, "
                                 "a web browser may open, or a URL will be printed to the console. "
                                 "Please follow the instructions in your browser to authorize access. "
                                 "The flow might involve a local redirect or copying an auth code.")
            log_info(auth_guidance_msg)

            # Create an InstalledAppFlow instance from the client secrets file and defined SCOPES.
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, self.SCOPES)

            # Run the local server flow. This will typically open a browser window for user authorization.
            # `port=0` allows the system to pick an available port.
            # For environments without a browser or display, flow.run_console() might be an alternative,
            # which usually involves copying/pasting an auth code.
            self.creds = flow.run_local_server(port=0)
            log_info("OAuth flow completed. Credentials obtained.")
        except FileNotFoundError: # Should be caught by the check above, but as a safeguard
            msg = f"CRITICAL: {CREDENTIALS_PATH} not found during OAuth flow."
            log_critical(msg)
            raise
        except Exception as e: # Catch any other error during the OAuth flow
            msg = f"An error occurred during Google Drive OAuth authorization flow: {e}"
            log_error(msg, exc_info=True)
            self.creds = None # Ensure creds is None if flow failed
            raise Exception(msg) # Re-raise to indicate failure of authentication

    def get_or_create_app_folder(self, service=None):
        """
        Searches for the app folder by name. If not found, creates it.
        Returns the folder ID.
        Caches the folder ID in `drive_folder_id.txt` to avoid repeated API calls.

        Args:
            service (googleapiclient.discovery.Resource, optional):
                The authenticated Google Drive API service client. If None,
                it will attempt to use `self.service` or authenticate.

        Returns:
            str: The ID of the app's dedicated folder on Google Drive.

        Raises:
            Exception: If the service is not available or folder cannot be found/created.
        """
        current_service = service or self.service
        if not current_service: # If no service provided and self.service is not set
            current_service = self.authenticate() # Try to authenticate and get the service

        if not current_service: # Still no service after trying
            raise Exception("Google Drive service client is not available for folder operations.")

        log_info = current_app.logger.info if current_app else print
        log_warning = current_app.logger.warning if current_app else print
        log_error = current_app.logger.error if current_app else print

        # Check if a valid cached folder ID already exists
        if self.app_folder_id:
            try:
                # Verify the cached folder ID is still valid by trying to get it
                current_service.files().get(fileId=self.app_folder_id, fields="id").execute()
                log_info(f"Using cached and validated App Folder ID: {self.app_folder_id}")
                return self.app_folder_id
            except HttpError as e:
                if e.resp.status == 404: # Folder not found (e.g., deleted by user)
                    log_warning(f"Cached App folder ID '{self.app_folder_id}' not found on Drive. Will search/create anew.")
                    self.app_folder_id = None # Clear invalid cached ID
                    self._save_app_folder_id('') # Also clear it from the cache file
                else: # Other HTTP error
                    log_error(f"Error validating cached folder ID '{self.app_folder_id}': {e}", exc_info=True)
                    raise # Re-raise other errors as they might be critical

        # If no valid cached ID, search for the folder on Drive
        try:
            query = f"mimeType='application/vnd.google-apps.folder' and name='{self.APP_FOLDER_NAME}' and trashed=false"
            response = current_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            found_files = response.get('files', [])

            if found_files: # Folder found
                folder_id = found_files[0]['id']
                log_info(f"Found existing app folder '{self.APP_FOLDER_NAME}' with ID: {folder_id}")
                self._save_app_folder_id(folder_id) # Cache the found ID
                return folder_id
            else: # Folder not found, so create it
                log_info(f"App folder '{self.APP_FOLDER_NAME}' not found on Drive. Creating new folder...")
                folder_metadata = {
                    'name': self.APP_FOLDER_NAME,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                # Create the folder and get its ID
                created_folder = current_service.files().create(body=folder_metadata, fields='id').execute()
                folder_id = created_folder.get('id')
                log_info(f"Created new app folder '{self.APP_FOLDER_NAME}' with ID: {folder_id}")
                self._save_app_folder_id(folder_id) # Cache the new ID
                return folder_id
        except HttpError as error: # Handle errors during search or creation
            log_error(f"An API error occurred during app folder check/creation: {error}", exc_info=True)
            raise # Re-raise to signal failure
        except Exception as e: # Catch any other unexpected errors
            log_error(f"An unexpected error occurred during app folder check/creation: {e}", exc_info=True)
            raise


    def upload_attachment(self, filename, content_type, file_data_bytes, parent_folder_id):
        """
        Uploads attachment data (bytes) to a specified parent folder in Google Drive.

        Args:
            filename (str): The desired filename for the attachment on Google Drive.
            content_type (str): The MIME type of the attachment (e.g., 'application/pdf').
            file_data_bytes (bytes): The raw binary data of the attachment.
            parent_folder_id (str): The Google Drive ID of the folder where the attachment
                                    should be uploaded (typically the app's dedicated folder).

        Returns:
            str: The Google Drive `fileId` of the uploaded attachment, or `None` if upload fails.

        Raises:
            Exception: If the Google Drive service is not available or `parent_folder_id` is missing.
        """
        if not self.service: # Ensure service client is available (authenticate if needed)
            self.authenticate()

        if not self.service: # Still no service after trying
            raise Exception("Google Drive service is not available for uploading attachments.")

        if not parent_folder_id: # Parent folder ID is crucial
             # This could try to get self.app_folder_id or self.get_or_create_app_folder() as a fallback,
             # but for this method, let's require it to be explicit for clarity of where it's uploading.
             # The caller (e.g., dashboard route) is responsible for providing this.
             raise ValueError("parent_folder_id must be provided for uploading to Google Drive.")

        log_info = current_app.logger.info if current_app else print
        log_error = current_app.logger.error if current_app else print

        # Metadata for the new file on Google Drive
        file_metadata = {
            'name': filename,
            'mimeType': content_type,
            'parents': [parent_folder_id] # Specify the parent folder
        }

        # Wrap the file data bytes in an io.BytesIO object for the media uploader
        media_body = io.BytesIO(file_data_bytes)

        # Create a MediaIoBaseUpload object for resumable uploads
        uploader = MediaIoBaseUpload(media_body, mimetype=content_type, resumable=True)

        try:
            # Create (upload) the file
            drive_file = self.service.files().create(
                body=file_metadata,      # File metadata
                media_body=uploader,     # File content
                fields='id'              # Fields to include in the API response (we only need the ID)
            ).execute()

            drive_file_id = drive_file.get('id')
            log_info(f"Successfully uploaded attachment '{filename}' to Google Drive. File ID: {drive_file_id}")
            return drive_file_id
        except HttpError as error: # Handle API errors during upload
            log_error(f"An HTTP error occurred uploading '{filename}' to Drive: {error}", exc_info=True)
            return None
        except Exception as e: # Catch any other unexpected errors
            log_error(f"An unexpected error occurred uploading '{filename}' to Drive: {e}", exc_info=True)
            return None


if __name__ == '__main__':
    # This block allows direct execution of this file for testing purposes (e.g., `python -m amail.app.google_drive_service`).
    # It attempts to authenticate and create/get the app folder.
    # Note: For this to run successfully standalone, `google_credentials.json` must be correctly
    # placed in the `amail/config/` directory. Flask `current_app` context won't be available,
    # so logging will fall back to `print`.
    print("Starting Google Drive Service Test (direct script execution)...")
    print(f"Credentials file expected at: {CREDENTIALS_PATH}")
    print(f"Token will be stored/read from: {TOKEN_PATH}")
    print(f"App Folder ID will be stored/read from: {FOLDER_ID_PATH}")

    if not os.path.exists(CREDENTIALS_PATH) or os.path.getsize(CREDENTIALS_PATH) == 0:
        print("\n" + "="*60)
        print("IMPORTANT: `google_credentials.json` is missing or empty.")
        print("Please download your OAuth 2.0 client ID credentials from")
        print("Google Cloud Console (for a 'Desktop app') and place the")
        print(f"file at: {CREDENTIALS_PATH}")
        print("Without this file, authentication cannot proceed.")
        print("="*60 + "\n")
    else:
        print("`google_credentials.json` found. Proceeding with test...")
        try:
            drive_service = GoogleDriveService()
            service_client = drive_service.authenticate()
            if service_client:
                print("Authentication successful. Drive API service client obtained.")
                folder_id = drive_service.get_or_create_app_folder(service_client)
                if folder_id:
                    print(f"Successfully obtained/created app folder '{GoogleDriveService.APP_FOLDER_NAME}'. ID: {folder_id}")
                    print("Test PASSED!")
                else:
                    print("Test FAILED: Could not get or create app folder ID.")
            else:
                print("Test FAILED: Authentication did not return a service client.")
        except Exception as e:
            print(f"Test FAILED with an error: {e}")
            import traceback
            traceback.print_exc()

    print("\nGoogle Drive Service Test Finished.")
