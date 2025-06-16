"""
Tests for authentication functionality (registration, login, logout).
Uses the test_client fixture from conftest.py.
"""
import pytest
from flask import url_for, get_flashed_messages

# Note: The User model is in-memory. `test_client` fixture in conftest.py
# should handle resetting the user store before each test.

def test_registration_page_loads(test_client):
    """Test that the registration page loads correctly."""
    response = test_client.get(url_for('auth.register'))
    assert response.status_code == 200
    assert b"Register</h1>" in response.data # Assuming H1 for Register title

def test_successful_registration(test_client):
    """Test successful user registration and redirection to login."""
    response = test_client.post(url_for('auth.register'), data={
        'username': 'testuser',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True) # follow_redirects to check final destination

    assert response.status_code == 200 # Should be on login page
    assert b"Login</h1>" in response.data # Check for Login page content
    # Check for flashed message (requires session handling by test client)
    # For this to work, SECRET_KEY must be set for the test app, which it is in conftest.
    # Flashed messages are often checked by inspecting the response data if rendered in template,
    # or by checking the session if `get_flashed_messages` is used carefully with test client context.
    # Simpler: check if the response data contains the success message.
    assert b"Congratulations, you are now a registered user!" in response.data

    # Verify user is in the (mocked/in-memory) database - this requires access to user model
    from amail.app.models import User
    user = User.get_by_username("testuser")
    assert user is not None
    assert user.username == "testuser"

def test_registration_duplicate_username(test_client):
    """Test registration with a username that already exists."""
    # First, register a user
    test_client.post(url_for('auth.register'), data={
        'username': 'testuserdup',
        'password': 'password123',
        'confirm_password': 'password123'
    }) # Don't follow redirects, just register

    # Attempt to register the same username again
    response = test_client.post(url_for('auth.register'), data={
        'username': 'testuserdup',
        'password': 'password456',
        'confirm_password': 'password456'
    })
    assert response.status_code == 200 # Should re-render registration form with error
    assert b"That username is already taken." in response.data

def test_login_page_loads(test_client):
    """Test that the login page loads correctly."""
    response = test_client.get(url_for('auth.login'))
    assert response.status_code == 200
    assert b"Login</h1>" in response.data

def test_successful_login(test_client):
    """Test successful user login and redirection to dashboard."""
    # Register user first
    test_client.post(url_for('auth.register'), data={
        'username': 'loginuser',
        'password': 'password123',
        'confirm_password': 'password123'
    })

    # Attempt login
    response = test_client.post(url_for('auth.login'), data={
        'username': 'loginuser',
        'password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Dashboard</h1>" in response.data # Should be on dashboard page
    assert b"Logged in successfully." in response.data
    # current_user should be active if session is handled, but that's harder to check directly here
    # Instead, check if a protected route like dashboard is accessible and shows user-specific info.
    assert b"Welcome, loginuser!" in response.data


def test_login_incorrect_password(test_client):
    """Test login with an incorrect password."""
    test_client.post(url_for('auth.register'), data={
        'username': 'loginuserfail',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    response = test_client.post(url_for('auth.login'), data={
        'username': 'loginuserfail',
        'password': 'wrongpassword'
    }, follow_redirects=True) # Follow redirect to see the flashed message on the login page

    assert response.status_code == 200 # Stays on login page
    assert b"Login</h1>" in response.data # Still on login page
    assert b"Invalid username or password." in response.data

def test_login_nonexistent_user(test_client):
    """Test login with a username that does not exist."""
    response = test_client.post(url_for('auth.login'), data={
        'username': 'nonexistentuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200 # Stays on login page
    assert b"Login</h1>" in response.data
    assert b"Invalid username or password." in response.data # Same message for user not found or bad pass

def test_logout(test_client):
    """Test user logout."""
    # Register and login a user
    test_client.post(url_for('auth.register'), data={'username': 'logoutuser', 'password': 'password', 'confirm_password': 'password'})
    test_client.post(url_for('auth.login'), data={'username': 'logoutuser', 'password': 'password'}, follow_redirects=True)

    # Logout
    response = test_client.get(url_for('auth.logout'), follow_redirects=True)
    assert response.status_code == 200
    assert b"Login</h1>" in response.data # Should redirect to login page
    assert b"You have been logged out successfully." in response.data

    # Try accessing dashboard - should be redirected to login
    response_dashboard = test_client.get(url_for('auth.dashboard'), follow_redirects=True)
    assert b"Login</h1>" in response_dashboard.data # Check if it's the login page
    assert b"Please log in to access this page." in response_dashboard.data # Standard Flask-Login message


def test_dashboard_access_unauthenticated(test_client):
    """Test accessing dashboard when not logged in."""
    response = test_client.get(url_for('auth.dashboard'), follow_redirects=True)
    assert response.status_code == 200
    assert b"Login</h1>" in response.data # Should be redirected to login
    assert b"Please log in to access this page." in response.data

def test_dashboard_access_authenticated(test_client):
    """Test accessing dashboard when logged in."""
    # Register and login
    test_client.post(url_for('auth.register'), data={'username': 'dashuser', 'password': 'password', 'confirm_password': 'password'})
    test_client.post(url_for('auth.login'), data={'username': 'dashuser', 'password': 'password'}, follow_redirects=True)

    response = test_client.get(url_for('auth.dashboard'))
    assert response.status_code == 200
    assert b"Dashboard</h1>" in response.data
    assert b"Welcome, dashuser!" in response.data
    # Check that the logout link is present, not login/register
    assert b"Logout" in response.data
    assert b"Login" not in response.data # Be careful if "Login" appears in other contexts
    assert b"Register" not in response.data
