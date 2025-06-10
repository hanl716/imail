import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting if needed for db_session fixture, though not directly used in this test file
from app.models.user import User as UserModel # For potential direct DB verification if needed

# client fixture is automatically available due to conftest.py

def test_user_registration_success(client: TestClient, db_session: Session): # Added db_session for potential verification
    email = "integration.user1@example.com"
    password = "testpassword123"

    response = client.post(
        "/api/v1/auth/users/", # Ensure this matches your router prefix in main.py
        json={"email": email, "password": password}
    )
    assert response.status_code == 201, response.text
    user_data = response.json()
    assert user_data["email"] == email
    assert "id" in user_data
    assert user_data["is_active"] is True

    # Optional: Direct DB verification (though API response is primary for integration test)
    db_user = db_session.query(UserModel).filter(UserModel.email == email).first()
    assert db_user is not None
    assert db_user.id == user_data["id"]

def test_user_registration_duplicate_email(client: TestClient):
    email = "integration.user2@example.com" # Use a different email to avoid conflict with other tests if run in parallel or if DB is not perfectly clean
    password = "testpassword123"

    # First registration
    response1 = client.post("/api/v1/auth/users/", json={"email": email, "password": password})
    assert response1.status_code == 201, response1.text

    # Attempt to register the same email again
    response2 = client.post("/api/v1/auth/users/", json={"email": email, "password": "anotherpassword"})
    assert response2.status_code == 400, response2.text # Bad Request for duplicates
    assert "Email already registered" in response2.json()["detail"]


def test_user_login_success(client: TestClient):
    email = "integration.loginuser@example.com"
    password = "testpassword123"

    # Register user first to ensure they exist for login
    reg_response = client.post("/api/v1/auth/users/", json={"email": email, "password": password})
    assert reg_response.status_code == 201, f"Registration failed, cannot proceed with login test. Response: {reg_response.text}"

    # Login user
    response = client.post(
        "/api/v1/auth/token/",
        data={"username": email, "password": password} # Form data for token endpoint
    )
    assert response.status_code == 200, response.text
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

def test_user_login_incorrect_password(client: TestClient):
    email = "integration.loginfail@example.com"
    password = "correctpassword"
    wrong_password = "wrongpassword"

    # Register user
    reg_response = client.post("/api/v1/auth/users/", json={"email": email, "password": password})
    assert reg_response.status_code == 201, f"Registration failed. Response: {reg_response.text}"

    # Attempt login with incorrect password
    response = client.post(
        "/api/v1/auth/token/",
        data={"username": email, "password": wrong_password}
    )
    assert response.status_code == 401, response.text # Unauthorized
    assert "Incorrect email or password" in response.json()["detail"]

def test_user_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/api/v1/auth/token/",
        data={"username": "nonexistent.user@example.com", "password": "anypassword"}
    )
    assert response.status_code == 401, response.text # Unauthorized
    assert "Incorrect email or password" in response.json()["detail"] # Same message for user not found or bad pass for security
