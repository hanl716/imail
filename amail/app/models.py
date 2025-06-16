"""
Defines the User model for authentication and user management.

This module currently uses a simple in-memory dictionary for user storage.
For production, this should be replaced with a persistent database (e.g., SQLAlchemy with PostgreSQL or SQLite).
"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# --- In-Memory User Storage (for demonstration purposes) ---
# This is a simple dictionary-based store. Not suitable for production.
# `users` maps usernames to User objects.
users = {}
# `user_id_to_username` maps user IDs to usernames for quick lookup by ID.
user_id_to_username = {}
# `next_user_id` is a simple counter for generating unique user IDs.
next_user_id = 1
# --- End In-Memory User Storage ---

class User(UserMixin):
    """
    User model representing a user of the application.

    Inherits from `UserMixin` to provide default implementations for properties
    required by Flask-Login (e.g., `is_authenticated`, `is_active`, `get_id`).
    """
    def __init__(self, username, password):
        """
        Initializes a new User instance.

        Args:
            username (str): The username for the new user.
            password (str): The plain-text password for the new user.
                            This will be hashed and stored.
        """
        global next_user_id # Use the global counter for user IDs
        self.id = next_user_id
        next_user_id += 1
        self.username = username
        self.password_hash = generate_password_hash(password) # Hash password on creation

        # Add user to in-memory stores
        users[self.username] = self
        user_id_to_username[self.id] = self.username

    def set_password(self, password):
        """
        Sets (or resets) the user's password.
        The provided password will be hashed before storing.

        Args:
            password (str): The new plain-text password.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Checks if the provided password matches the user's stored hashed password.

        Args:
            password (str): The plain-text password to check.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_username(username):
        """
        Retrieves a user by their username.

        Args:
            username (str): The username to search for.

        Returns:
            User: The User object if found, None otherwise.
        """
        return users.get(username)

    @staticmethod
    def get_by_id(user_id):
        """
        Retrieves a user by their ID.
        Required by Flask-Login's user_loader.

        Args:
            user_id (int or str): The ID of the user to retrieve.
                                  It's converted to int for internal lookup.

        Returns:
            User: The User object if found, None otherwise.
        """
        # Ensure user_id is of the correct type for dictionary lookup if necessary
        # (Our current setup uses int keys for user_id_to_username)
        try:
            uid = int(user_id)
        except ValueError:
            return None # Invalid user_id format

        username = user_id_to_username.get(uid)
        if username:
            return users.get(username)
        return None

    def __repr__(self):
        """
        String representation of the User object, useful for debugging.
        """
        return f'<User id={self.id} username={self.username}>'
