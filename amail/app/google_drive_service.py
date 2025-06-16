import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import current_app # For logging

# Define paths - relative to the 'app' directory where this service might be imported
# Or better, make them absolute paths from the project root if possible
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Goes up to 'amail'
CONFIG_DIR = os.path.join(APP_ROOT, 'config')
CREDENTIALS_PATH = os.path.join(CONFIG_DIR, 'google_credentials.json')
TOKEN_PATH = os.path.join(CONFIG_DIR, 'token.json')
FOLDER_ID_PATH = os.path.join(CONFIG_DIR, 'drive_folder_id.txt')

class GoogleDriveService:
    # Using drive.file scope to allow creating files/folders in app's own space or specific folders it creates.
    # If you need to search all of Drive, or manage other files, 'https://www.googleapis.com/auth/drive' might be needed.
    # 'drive.metadata.readonly' could be useful for just searching/listing.
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    APP_FOLDER_NAME = "AMailAppStorage"

    def __init__(self):
        self.creds = None
        self.service = None
        self.app_folder_id = None
        self._load_app_folder_id()

    def _load_app_folder_id(self):
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
        try:
            with open(FOLDER_ID_PATH, 'w') as f:
                f.write(folder_id)
            self.app_folder_id = folder_id
            if current_app:
                current_app.logger.info(f"Saved App Folder ID: {folder_id}")
            else:
                print(f"Saved App Folder ID: {folder_id}")
        except IOError as e:
            if current_app:
                current_app.logger.error(f"Error saving folder ID file: {e}")
            else:
                 print(f"Error saving folder ID file: {e}")


    def authenticate(self):
        """Handles OAuth 2.0 authentication and returns the Drive API service client."""
        if os.path.exists(TOKEN_PATH):
            try:
                self.creds = Credentials.from_authorized_user_file(TOKEN_PATH, self.SCOPES)
            except ValueError as e: # Handle cases where token.json might be malformed
                if current_app:
                    current_app.logger.warning(f"Error loading token.json: {e}. Will attempt re-authentication.")
                else:
                    print(f"Error loading token.json: {e}. Will attempt re-authentication.")
                self.creds = None # Ensure creds is None to trigger re-auth
            except Exception as e: # Catch any other potential error from from_authorized_user_file
                if current_app:
                    current_app.logger.error(f"Unexpected error loading token.json: {e}. Will attempt re-authentication.")
                else:
                    print(f"Unexpected error loading token.json: {e}. Will attempt re-authentication.")
                self.creds = None


        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    if current_app:
                        current_app.logger.error(f"Failed to refresh token: {e}. Initiating full auth flow.")
                    else:
                        print(f"Failed to refresh token: {e}. Initiating full auth flow.")
                    self._run_auth_flow()
            else:
                self._run_auth_flow()

            # Save the credentials for the next run
            if self.creds:
                try:
                    with open(TOKEN_PATH, 'w') as token_file:
                        token_file.write(self.creds.to_json())
                    if current_app:
                         current_app.logger.info("Token saved successfully.")
                    else:
                        print("Token saved successfully.")
                except IOError as e:
                    if current_app:
                        current_app.logger.error(f"Error saving token: {e}")
                    else:
                        print(f"Error saving token: {e}")


        if not self.creds:
             msg = "Failed to obtain Google Drive credentials after authentication flow."
             if current_app: current_app.logger.error(msg)
             else: print(msg)
             raise Exception(msg) # Or handle more gracefully

        try:
            self.service = build('drive', 'v3', credentials=self.creds)
            if current_app: current_app.logger.info("Google Drive API service built successfully.")
            else: print("Google Drive API service built successfully.")
            return self.service
        except Exception as e:
            if current_app: current_app.logger.error(f"Failed to build Google Drive service: {e}")
            else: print(f"Failed to build Google Drive service: {e}")
            raise

    def _run_auth_flow(self):
        """Runs the OAuth 2.0 authorization flow."""
        if not os.path.exists(CREDENTIALS_PATH):
            msg = (f"Google credentials file not found at {CREDENTIALS_PATH}. "
                   "Please download it from Google Cloud Console and place it correctly. "
                   "If running for the first time, expect to follow a URL to authorize.")
            if current_app: current_app.logger.error(msg)
            else: print(msg)
            # Depending on setup, might want to raise an error or exit if creds file is mandatory
            return # or raise FileNotFoundError(msg)

        try:
            # Log user guidance message
            auth_message = ("Attempting Google Drive authentication. "
                            "If this is the first time or token is invalid, "
                            "a web browser may open or a URL will be printed here. "
                            "Please follow the instructions to authorize access.")
            if current_app: current_app.logger.info(auth_message)
            else: print(auth_message)

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, self.SCOPES)
            # The port and host for the local server can be specified if needed, e.g., flow.run_local_server(port=0)
            # For environments where a browser cannot be opened automatically,
            # run_console() might be more appropriate if it forces code pasting.
            # However, run_local_server is generally preferred if a local browser redirect is possible.
            self.creds = flow.run_local_server(port=0)
            # self.creds = flow.run_console() # Alternative for strictly no-browser environments

        except FileNotFoundError:
            msg = (f"CRITICAL: {CREDENTIALS_PATH} not found. "
                   "Cannot proceed with Google Drive authentication. "
                   "Download your OAuth 2.0 credentials from Google Cloud Console.")
            if current_app: current_app.logger.critical(msg)
            else: print(msg)
            # This is a critical failure, so re-raise or handle appropriately
            raise
        except Exception as e:
            msg = f"Error during OAuth flow: {e}"
            if current_app: current_app.logger.error(msg)
            else: print(msg)
            self.creds = None # Ensure creds is None if flow failed

    def get_or_create_app_folder(self, service=None):
        """
        Searches for the app folder by name. If not found, creates it.
        Returns the folder ID.
        Caches the folder ID in a local file to avoid repeated searches.
        """
        if not service:
            if not self.service:
                self.authenticate() # Ensure service is built
            service = self.service

        if not service: # Still no service after trying to authenticate
            raise Exception("Google Drive service not available.")

        # Check if we already have a cached folder ID that's valid
        if self.app_folder_id:
            try:
                service.files().get(fileId=self.app_folder_id, fields="id").execute()
                if current_app: current_app.logger.info(f"App folder ID {self.app_folder_id} is valid.")
                else: print(f"App folder ID {self.app_folder_id} is valid.")
                return self.app_folder_id
            except HttpError as e:
                if e.resp.status == 404:
                    if current_app: current_app.logger.warning(f"Cached App folder ID {self.app_folder_id} not found on Drive. Will create a new one.")
                    else: print(f"Cached App folder ID {self.app_folder_id} not found on Drive. Will create a new one.")
                    self.app_folder_id = None # Clear invalid cached ID
                    self._save_app_folder_id('') # Clear from file too
                else:
                    if current_app: current_app.logger.error(f"Error checking cached folder ID: {e}")
                    else: print(f"Error checking cached folder ID: {e}")
                    raise

        try:
            # Search for the folder
            query = f"mimeType='application/vnd.google-apps.folder' and name='{self.APP_FOLDER_NAME}' and trashed=false"
            response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = response.get('files', [])

            if files:
                folder_id = files[0]['id']
                if current_app: current_app.logger.info(f"Found app folder '{self.APP_FOLDER_NAME}' with ID: {folder_id}")
                else: print(f"Found app folder '{self.APP_FOLDER_NAME}' with ID: {folder_id}")
                self._save_app_folder_id(folder_id)
                return folder_id
            else:
                # Create the folder
                if current_app: current_app.logger.info(f"App folder '{self.APP_FOLDER_NAME}' not found. Creating...")
                else: print(f"App folder '{self.APP_FOLDER_NAME}' not found. Creating...")
                file_metadata = {
                    'name': self.APP_FOLDER_NAME,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = service.files().create(body=file_metadata, fields='id').execute()
                folder_id = folder.get('id')
                if current_app: current_app.logger.info(f"Created app folder '{self.APP_FOLDER_NAME}' with ID: {folder_id}")
                else: print(f"Created app folder '{self.APP_FOLDER_NAME}' with ID: {folder_id}")
                self._save_app_folder_id(folder_id)
                return folder_id
        except HttpError as error:
            if current_app: current_app.logger.error(f'An error occurred during folder check/creation: {error}')
            else: print(f'An error occurred during folder check/creation: {error}')
            raise
        except Exception as e: # Catch any other unexpected errors
            if current_app: current_app.logger.error(f'An unexpected error: {e}')
            else: print(f'An unexpected error: {e}')
            raise


if __name__ == '__main__':
    # This is a basic test sequence.
    # IMPORTANT: For this to run, 'amail/config/google_credentials.json' MUST exist and be correctly populated
    # by the user from their Google Cloud Console.
    print("Starting Google Drive Service Test...")
    print(f"Expecting credentials at: {CREDENTIALS_PATH}")
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
