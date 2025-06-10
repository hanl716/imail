import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting db_session fixture

# client fixture is automatically available due to conftest.py

# Helper function to get auth token (can be moved to conftest.py if used by many test files)
def get_auth_token(client: TestClient, email: str, password: str) -> str:
    # Ensure user is registered (ignore error if already exists, for idempotency in tests)
    client.post("/api/v1/auth/users/", json={"email": email, "password": password})

    response = client.post(
        "/api/v1/auth/token/",
        data={"username": email, "password": password}
    )
    response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
    return response.json()["access_token"]

@pytest.fixture(scope="module") # Token can be reused for all tests in this module
def auth_headers(client: TestClient):
    # Use a unique email for this module to avoid conflicts if tests run in parallel (though function scope fixtures are isolated)
    token = get_auth_token(client, email="user.for.accounts@example.com", password="testpassword")
    return {"Authorization": f"Bearer {token}"}


def test_link_email_account_success(client: TestClient, auth_headers: dict, db_session: Session):
    account_data = {
        "email_address": "test.linked.acc1@example.com",
        "email_user": "test.linked.acc1@example.com",
        "password": "linkedpassword123", # Plaintext password for submission
        "imap_server": "imap.example.com",
        "imap_port": 993,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587
        # is_active will default to True in the model
    }
    response = client.post("/api/v1/email-accounts/", json=account_data, headers=auth_headers)
    assert response.status_code == 201, response.text
    linked_account = response.json()
    assert linked_account["email_address"] == "test.linked.acc1@example.com"
    assert "id" in linked_account
    assert linked_account["user_id"] is not None # User ID should be set by backend
    # Password should NOT be in the response

    # Verify account listing includes the new account
    response_list = client.get("/api/v1/email-accounts/", headers=auth_headers)
    assert response_list.status_code == 200, response_list.text
    accounts = response_list.json()
    assert isinstance(accounts, list)
    assert any(acc["email_address"] == "test.linked.acc1@example.com" and acc["id"] == linked_account["id"] for acc in accounts)

def test_link_email_account_missing_fields(client: TestClient, auth_headers: dict):
    # Missing 'password' which is required by schema if not OAuth
    # (Current schema makes password Optional, but let's assume it's needed for this test's purpose,
    #  or that server details are also required for a functional account linking)
    #  The EmailAccountCreate has password: Optional[str] = Field(None, min_length=1)
    #  Let's test without password.
    account_data_no_pass = {
        "email_address": "test.linked.nopass@example.com",
        "email_user": "test.linked.nopass@example.com",
        "imap_server": "imap.example.com",
        "imap_port": 993,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587
    }
    # This should be okay by current schema, password is not strictly required at schema level.
    # However, for practical use, an account needs password or token.
    # The API doesn't enforce this logic currently, only the schema.
    response = client.post("/api/v1/email-accounts/", json=account_data_no_pass, headers=auth_headers)
    assert response.status_code == 201, response.text # Expect success as schema allows optional password

    # Test with missing email_address (which is required)
    account_data_no_email = {
        "email_user": "test.linked.noemail@example.com",
        "password": "password123",
        "imap_server": "imap.example.com", "imap_port": 993,
        "smtp_server": "smtp.example.com", "smtp_port": 587
    }
    response_no_email = client.post("/api/v1/email-accounts/", json=account_data_no_email, headers=auth_headers)
    assert response_no_email.status_code == 422, response_no_email.text # Unprocessable Entity for Pydantic validation error


def test_list_email_accounts_unauthenticated(client: TestClient):
    response = client.get("/api/v1/email-accounts/")
    assert response.status_code == 401, response.text # Unauthorized

def test_list_email_accounts_empty(client: TestClient):
    # Create a new user who has no accounts
    token = get_auth_token(client, email="user.no.accounts@example.com", password="testpassword")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/email-accounts/", headers=headers)
    assert response.status_code == 200, response.text
    accounts = response.json()
    assert isinstance(accounts, list)
    assert len(accounts) == 0

# Add more tests:
# - Attempting to link account with invalid data types (e.g., port as string) -> 422
# - Attempting to access/modify another user's email account (should be prevented by user_id checks in CRUD)
# - Deleting an email account (if that functionality is added)
# - Updating an email account (if that functionality is added)
