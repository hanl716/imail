"""
Tests for services that interact with external APIs or systems.
These tests will primarily focus on instantiation and basic non-network functionality,
or use mocking for network calls.
"""
import pytest
from flask import current_app
from unittest.mock import patch, MagicMock

from amail.app.email_service import fetch_emails, parse_sender, decode_subject, get_email_body
from amail.app.google_drive_service import GoogleDriveService
from amail.app.cerebras_service import CerebrasService

# --- EmailService Tests (Parsing Logic) ---

def test_decode_subject_simple():
    assert decode_subject("Hello World") == "Hello World"

def test_decode_subject_encoded():
    # Example of a simple base64 encoded subject (UTF-8)
    # "=?UTF-8?B?SGVsbG8gV29ybGQ=?=" -> "Hello World"
    encoded_subject = "=?UTF-8?B?SGVsbG8gV29ybGQ=?="
    assert decode_subject(encoded_subject) == "Hello World"

    # Example with ISO-8859-1
    # "=?ISO-8859-1?Q?Pr=FCfung_f=FCr_Umlaute?=" -> "Prüfung für Umlaute"
    encoded_subject_iso = "=?ISO-8859-1?Q?Pr=FCfung_f=FCr_Umlaute?="
    assert decode_subject(encoded_subject_iso) == "Prüfung für Umlaute"


def test_parse_sender_simple_email():
    assert parse_sender("user@example.com") == "user@example.com"

def test_parse_sender_with_name():
    assert parse_sender("John Doe <john.doe@example.com>") == "john.doe@example.com"

def test_parse_sender_empty():
    assert parse_sender(None) == "Unknown Sender"
    assert parse_sender("") == "Unknown Sender"

# More comprehensive tests for get_email_body and fetch_emails (full parsing)
# would require sample raw email content (bytes).
# For fetch_emails, mocking `imaplib` would be necessary for true unit tests.
# Here's a placeholder for a very basic fetch_emails test structure using mocks.

@patch('amail.app.email_service.imaplib.IMAP4_SSL')
def test_fetch_emails_mocked_imap_basic(mock_imap_ssl, test_client): # test_client for app_context
    """
    Basic test for fetch_emails, ensuring it tries to connect and handles
    a mocked successful, but empty, response from IMAP.
    """
    # Configure the mock IMAP server instance
    mock_server_instance = MagicMock()
    mock_imap_ssl.return_value = mock_server_instance # Constructor returns our mock

    # Mock login, select, search, fetch, close, logout to simulate a successful flow with no emails
    mock_server_instance.login.return_value = ("OK", [b"Login successful"])
    mock_server_instance.select.return_value = ("OK", [b"1"]) # Mock 1 message in folder for select
    mock_server_instance.search.return_value = ("OK", [b""]) # No UIDs found
    mock_server_instance.fetch.return_value = ("OK", [])
    mock_server_instance.close.return_value = ("OK", [])
    mock_server_instance.logout.return_value = ("OK", [])

    # `test_client` fixture provides app context, so `current_app.config` is available
    # The EMAIL_ACCOUNTS config is taken from conftest.py's test_app_instance
    emails = fetch_emails("test_account", limit=5)

    assert emails == [] # Expect no emails from the mocked empty search
    mock_imap_ssl.assert_called_once_with("mock.imap.server.com") # Check server address from config
    mock_server_instance.login.assert_called_once_with("testuser@example.com", "testpassword")
    mock_server_instance.select.assert_called_once_with('"INBOX"')
    mock_server_instance.search.assert_called_once_with(None, "ALL")
    # fetch should not be called if search returns no UIDs
    mock_server_instance.fetch.assert_not_called()
    mock_server_instance.logout.assert_called_once()


# --- GoogleDriveService Tests ---
def test_google_drive_service_instantiation(test_client):
    """
    Test that GoogleDriveService can be instantiated.
    Does not test authentication or API calls, which require mocking or real credentials.
    Relies on paths being overridden by conftest.py for a test environment.
    """
    # The test_client fixture sets up app.config with _OVERRIDE paths.
    # GoogleDriveService needs to be adapted to use these if current_app.config has them.
    # For now, let's assume GoogleDriveService is adapted or we monkeypatch its path constants.

    # To properly test this, we'd monkeypatch the path constants in google_drive_service module
    # before instantiation if the service doesn't read them from app.config.
    # For example, using pytest's monkeypatch fixture:
    # monkeypatch.setattr('amail.app.google_drive_service.CREDENTIALS_PATH', current_app.config['GOOGLE_CREDENTIALS_PATH_OVERRIDE'])
    # monkeypatch.setattr('amail.app.google_drive_service.TOKEN_PATH', current_app.config['GOOGLE_TOKEN_PATH_OVERRIDE'])
    # monkeypatch.setattr('amail.app.google_drive_service.FOLDER_ID_PATH', current_app.config['GOOGLE_FOLDER_ID_PATH_OVERRIDE'])

    # The GoogleDriveService __init__ tries to load folder_id from FOLDER_ID_PATH.
    # The mock file is created by conftest.py.
    try:
        service = GoogleDriveService()
        assert service is not None
        # Check if it tried to load the (mock) folder ID.
        # If FOLDER_ID_PATH was a non-empty mock file, service.app_folder_id might be set.
        # If it was empty (like created by touch), app_folder_id would be None or empty.
        # This depends on the content of the mock file if it was pre-populated by conftest.
        # The conftest creates it empty, so app_folder_id should be None or empty.
        assert not service.app_folder_id
    except Exception as e:
        pytest.fail(f"GoogleDriveService instantiation failed: {e}")

# --- CerebrasService Tests ---
def test_cerebras_service_instantiation_and_mock_call(test_client):
    """
    Test CerebrasService instantiation and that its mock call works.
    Uses API key/endpoint from test_client's app config.
    """
    # CerebrasService __init__ reads from current_app.config if no args are passed.
    service = CerebrasService()
    assert service is not None
    assert service.api_key == "mock_cerebras_api_key_for_testing" # From conftest.py
    assert service.api_endpoint == "https://mock.cerebras.api/test_endpoint"

    response = service.call_cerebras_api("test_task", {"data": "sample"})
    assert response is not None
    assert response['status'] == 'success_mocked_call'
    assert response['task_type_received'] == 'test_task'
    assert "MOCKED result" in response['result']

def test_cerebras_service_no_config_mock_call(test_client):
    """Test mock call when Cerebras API key/endpoint are not configured (or set to placeholder)."""
    # Temporarily override app config for this test to simulate missing keys
    original_key = current_app.config.get('CEREBRAS_API_KEY')
    original_endpoint = current_app.config.get('CEREBRAS_API_ENDPOINT')

    current_app.config['CEREBRAS_API_KEY'] = None
    current_app.config['CEREBRAS_API_ENDPOINT'] = "YOUR_CEREBRAS_API_ENDPOINT_HERE_PLEASE_UPDATE"

    service = CerebrasService() # Re-initialize with overridden "missing" config
    response = service.call_cerebras_api("another_task", {"input": "test"})

    assert response['status'] == 'mock_success_no_config'
    assert "no API config" in response['result']

    # Restore original config to not affect other tests
    current_app.config['CEREBRAS_API_KEY'] = original_key
    current_app.config['CEREBRAS_API_ENDPOINT'] = original_endpoint
