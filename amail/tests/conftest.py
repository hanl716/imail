import pytest
import os
import tempfile # For creating temporary data files for tests

# Adjust the import path if your create_app is elsewhere or project structure is different.
# This assumes create_app is in amail/app/__init__.py
from amail.app import create_app
# from amail.app.models import users, user_id_to_username, next_user_id # For resetting user store

# If ContactService uses a default file path, we might need to control it during tests.
# One way is to set an environment variable that ContactService checks,
# or pass the path directly if the service allows.
# For now, the test_client fixture will set a specific path in app.config.

@pytest.fixture(scope='module')
def test_app_instance():
    """
    Creates a Flask app instance configured for testing.
    This fixture has a 'module' scope, meaning one app instance is created per test module.
    """
    # Create a temporary directory for test data files (like contacts.json)
    # This ensures tests don't interfere with actual data or each other if run in parallel (though pytest usually serializes).
    # However, for simplicity here, we'll configure a fixed path that tests should clean up.
    # A more robust way is to use pytest's tmp_path fixture per test function if needed.

    # For testing, we override some configurations:
    # - TESTING=True: Enables Flask's testing mode (e.g., disables error catching during request handling
    #   so you get better error reports).
    # - WTF_CSRF_ENABLED=False: Disables CSRF protection for forms in tests, simplifying POST requests.
    # - SECRET_KEY: A fixed key for testing.
    # - Mock external service configs to prevent real API calls.

    # Define a temporary directory for test-specific data files
    # This is a simple approach. For more complex scenarios, pytest's `tmp_path_factory`
    # or per-test `tmp_path` might be better.
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data_temp')
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)

    test_contacts_file = os.path.join(test_data_dir, 'test_contacts.json')
    test_feedback_log_file = os.path.join(test_data_dir, 'test_feedback_log.csv')
    # For Google Drive service, provide paths to non-existent/mock files to prevent real ops
    # if the service attempts to load them by default (it shouldn't if properly mocked or if auth is bypassed).
    mock_google_creds = os.path.join(test_data_dir, 'mock_google_credentials.json')
    mock_google_token = os.path.join(test_data_dir, 'mock_token.json')
    mock_drive_folder_id = os.path.join(test_data_dir, 'mock_drive_folder_id.txt')

    # Create empty mock files so service initializers don't fail if they expect file existence
    # (though ideally, they handle non-existence gracefully).
    open(mock_google_creds, 'a').close()
    open(mock_google_token, 'a').close()
    open(mock_drive_folder_id, 'a').close()


    flask_app = create_app({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False, # Disable CSRF for simpler form testing
        'SECRET_KEY': 'test_secret_key_for_pytest_session',
        # Mock email account configuration
        'EMAIL_ACCOUNTS': {
            "test_account": {
                "imap_server": "mock.imap.server.com", # Non-existent server
                "email_address": "testuser@example.com",
                "password": "testpassword",
                "folder": "INBOX"
            }
        },
        # Override paths for services that write/read files
        # These are custom config keys that services should be adapted to use if they don't already.
        # Or, services should accept paths in their constructors for testing.
        # For GoogleDriveService, these are based on its constants:
        'GOOGLE_CREDENTIALS_PATH_OVERRIDE': mock_google_creds,
        'GOOGLE_TOKEN_PATH_OVERRIDE': mock_google_token,
        'GOOGLE_FOLDER_ID_PATH_OVERRIDE': mock_drive_folder_id,

        # Mock Cerebras configuration
        'CEREBRAS_API_KEY': 'mock_cerebras_api_key_for_testing',
        'CEREBRAS_API_ENDPOINT': 'https://mock.cerebras.api/test_endpoint',

        # Override data file paths for ContactService and Feedback logging
        # These keys need to be understood and used by the respective services/routes during testing.
        'CONTACTS_FILE_PATH_OVERRIDE': test_contacts_file,
        'FEEDBACK_FILE_PATH_OVERRIDE': test_feedback_log_file,
        'DATA_DIR_OVERRIDE': test_data_dir, # If services construct paths from a base data dir
    })

    # Ensure test data files are clean before module tests if they are module-scoped
    if os.path.exists(test_contacts_file):
        os.remove(test_contacts_file)
    if os.path.exists(test_feedback_log_file):
        os.remove(test_feedback_log_file)

    yield flask_app # Provide the app instance for the test module

    # Teardown: Clean up test data files and directory after all tests in the module run
    # This is important for module-scoped fixtures.
    # For function-scoped, cleanup would happen after each test.
    if os.path.exists(test_contacts_file):
        os.remove(test_contacts_file)
    if os.path.exists(test_feedback_log_file):
        os.remove(test_feedback_log_file)
    if os.path.exists(mock_google_creds): os.remove(mock_google_creds)
    if os.path.exists(mock_google_token): os.remove(mock_google_token)
    if os.path.exists(mock_drive_folder_id): os.remove(mock_drive_folder_id)

    # Attempt to remove the test_data_dir if empty
    try:
        if os.path.exists(test_data_dir) and not os.listdir(test_data_dir): # Check if empty
            os.rmdir(test_data_dir)
    except OSError:
        pass # Ignore if it fails (e.g., not empty, permissions)


@pytest.fixture(scope='function') # Changed to function scope for client to ensure clean state for each test
def test_client(test_app_instance):
    """
    Creates a test client for the Flask application.
    This fixture has 'function' scope, meaning a new test client (and app context)
    is created for each test function. This helps ensure test isolation.
    """
    # Reset in-memory user store before each test that uses this client
    # This is crucial for auth tests to avoid interference.
    # Requires access to the User model's storage.
    from amail.app.models import users as global_users_dict, \
                                 user_id_to_username as global_user_id_dict, \
                                 next_user_id as global_next_user_id_module_var

    # This direct manipulation is a bit of a hack. Better if User model had a reset method.
    global_users_dict.clear()
    global_user_id_dict.clear()
    # Resetting global 'next_user_id' if it's a direct global int.
    # If it's part of a class, that class would need a reset method.
    # For this example, assuming it's `models.next_user_id`
    # To reset module-level variable, we need to re-assign it in its module.
    import amail.app.models as user_models_module
    user_models_module.next_user_id = 1


    # Clean up test data files before each test (function scope)
    # This provides better isolation than module-level cleanup if tests modify these files.
    # These paths are now taken from the app config set by `test_app_instance` fixture.
    contacts_file = test_app_instance.config.get('CONTACTS_FILE_PATH_OVERRIDE')
    feedback_file = test_app_instance.config.get('FEEDBACK_FILE_PATH_OVERRIDE')

    if contacts_file and os.path.exists(contacts_file):
        os.remove(contacts_file)
    if feedback_file and os.path.exists(feedback_file):
        os.remove(feedback_file)


    with test_app_instance.test_client() as testing_client:
        with test_app_instance.app_context(): # Push an application context
            # yield the client to the test function
            yield testing_client

    # Post-test cleanup (function scope) can also go here if needed,
    # though the file cleanup above is more for pre-test state.
    # The app context is automatically popped when the 'with' block exits.
    # The user store reset above ensures each test starts fresh regarding users.
    # print("DEBUG: Test client and app context torn down.")

# Note: To use the overridden file paths (e.g., CONTACTS_FILE_PATH_OVERRIDE) in services:
# 1. Services should accept the path in their __init__ constructor.
#    The route would then instantiate the service with `current_app.config.get('CONTACTS_FILE_PATH_OVERRIDE')`.
# 2. Or, services directly check `current_app.config.get('CONTACTS_FILE_PATH_OVERRIDE', DEFAULT_PATH)`.
#
# The GoogleDriveService constants (CREDENTIALS_PATH, TOKEN_PATH, FOLDER_ID_PATH) are global in its module.
# To override them for tests without changing the service code:
#   - Use monkeypatching (pytest fixture `monkeypatch`) to change these global variables within the test scope.
#   - Example (in a test or fixture):
#     monkeypatch.setattr('amail.app.google_drive_service.CREDENTIALS_PATH', current_app.config['GOOGLE_CREDENTIALS_PATH_OVERRIDE'])
# This is important because GoogleDriveService reads these paths at its module level.
# The current `test_app_instance` fixture creates mock files for these, and the service uses them.
# However, if the GoogleDriveService was refactored to take paths from app.config, it would be cleaner.
# For now, the existing GoogleDriveService will use its defined constants, which point to amil/config/...
# The mock files created in test_app_instance are at amil/tests/test_data_temp/...
# This means the current GoogleDriveService will NOT use the mock files from conftest for its default paths.
# This needs to be addressed for proper mocking of GoogleDriveService file interactions.
#
# Quick fix for GoogleDriveService paths for testing:
# We will use monkeypatching in specific test modules or fixtures where GoogleDriveService is tested/used.
# The current conftest sets up mock files but GoogleDriveService isn't using them yet.
# The test_client config for GOOGLE_*_PATH_OVERRIDE are placeholders for this idea.
# The actual GoogleDriveService needs to be adapted or monkeypatched.
# For now, tests involving GoogleDriveService might attempt real auth if not carefully mocked.
# The `/test_drive_setup` route itself checks G_CREDENTIALS_PATH (imported from GoogleDriveService).
# So, for that route test, monkeypatching `amail.app.google_drive_service.CREDENTIALS_PATH` is key.
# And also `TOKEN_PATH` and `FOLDER_ID_PATH`.

# Similarly for ContactService and Feedback log, they are hardcoded to use their DATA_DIR.
# The `test_client` fixture sets `CONTACTS_FILE_PATH_OVERRIDE` etc. in app.config.
# The services/routes need to be adapted to *use* these config values.
# Example: `ContactService(contacts_file_path=current_app.config.get('CONTACTS_FILE_PATH_OVERRIDE'))`
# Or `ContactService` constructor itself checks `current_app.config`.

# For now, I will adapt ContactService and the feedback log path in routes.py
# to check for these _OVERRIDE config settings when running in a testing environment.
# This is simpler than monkeypatching for these specific cases for now.
# This adaptation will be done in the respective service/route files as part of the testing setup.
# (This is a meta-comment on how to make the app more testable with these fixtures)
# The conftest.py is now more robust in setting up a test environment.
# The next step is to write tests that leverage this, and adapt services if they
# don't respect the test configurations.
# The code for ContactService and log_feedback_to_csv in routes.py already uses
# module-level constants for file paths. These will need adjustment or monkeypatching for tests.

# The `test_app_instance` fixture now creates the mock files in `amail/tests/test_data_temp`.
# The services need to be made aware of these paths during tests.
# The most straightforward way is to modify services to accept paths in constructor or read from app.config.
# I will assume this modification will be done as part of writing the tests for those services.
# For now, the fixture sets up the *potential* for these overrides.
# `test_contacts_file` and `test_feedback_log_file` are cleaned up by `test_app_instance`.
# This is okay for module scope, but for function scope, `test_client` should handle it.
# Adjusted `test_client` to also clean these files for better isolation per test.
# And `test_app_instance` to do it once for the module.
# The `CONTACTS_FILE_PATH_OVERRIDE` etc. in app.config is the key.
# Services/routes must be updated to use these config values.
# E.g., in ContactService:
# path = current_app.config.get('CONTACTS_FILE_PATH_OVERRIDE') or DEFAULT_CONTACTS_PATH
# Or pass it in constructor.
# This is a common challenge in making Flask apps testable.
# For this subtask, I will assume the test files will handle instantiation of services
# with test-specific paths if needed, or that services are adapted.
# The `ai_assistant` and `auth` tests can proceed more easily as they are less path-dependent.`amail/tests/conftest.py` has been created with a `test_app_instance` (module scope) and `test_client` (function scope) fixture.
The `test_client` fixture also includes logic to reset the in-memory user store and clean up test data files for better test isolation.
The fixture sets up various mock configurations in `app.config` for testing. Services and routes will need to be written or adapted to respect these `_OVERRIDE` paths when `TESTING` is true.

**Step 2: Authentication Tests (`amail/tests/test_auth.py`)**
I'll create this file and add some basic authentication tests.
