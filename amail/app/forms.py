"""
Defines Flask-WTF forms for user authentication (registration and login).
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from .models import User # Used for username validation

class RegistrationForm(FlaskForm):
    """
    Form for user registration.
    Allows new users to sign up by providing a username, password, and password confirmation.
    """
    username = StringField(
        'Username',
        validators=[
            DataRequired(message="Username is required."),
            Length(min=4, max=25, message="Username must be between 4 and 25 characters.")
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message="Password is required."),
            Length(min=6, message="Password must be at least 6 characters long.")
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo('password', message="Passwords must match.")
        ]
    )
    submit = SubmitField('Register')

    def validate_username(self, username_field):
        """
        Custom validator to check if the username is already taken.
        This method is automatically called by Flask-WTF during form validation.

        Args:
            username_field (wtforms.fields.StringField): The username field from the form.

        Raises:
            ValidationError: If the username already exists in the user store.
        """
        user = User.get_by_username(username_field.data)
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

class LoginForm(FlaskForm):
    """
    Form for user login.
    Allows existing users to sign in with their username and password.
    """
    username = StringField(
        'Username',
        validators=[DataRequired(message="Username is required.")]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message="Password is required.")]
    )
    remember_me = BooleanField('Remember Me') # Option to keep the user logged in
    submit = SubmitField('Login')
