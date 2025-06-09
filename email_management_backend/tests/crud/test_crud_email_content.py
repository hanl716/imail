import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session # For type hinting
from typing import Optional, List
import datetime

from app.crud import email_content as crud_email_content
from app.models.email_content import EmailMessage, EmailThread, EmailAttachment
from app.models.user import User # Assuming User model might be relevant for context
from app.models.email_account import EmailAccount # Assuming EmailAccount model for context

# --- Fixtures for Mock Data ---
@pytest.fixture
def mock_user() -> User:
    user = User(id=1, email="test@example.com", hashed_password="fakehashedpassword", is_active=True)
    return user

@pytest.fixture
def mock_email_account(mock_user: User) -> EmailAccount:
    account = EmailAccount(
        id=1,
        user_id=mock_user.id,
        email_address="testacc@example.com",
        is_active=True
        # Other fields like server details, encrypted creds can be omitted for this context
        # unless specifically tested by a CRUD involving them.
    )
    # account.user = mock_user # If relationship is used in code being tested
    return account

@pytest.fixture
def mock_email_thread(mock_user: User, mock_email_account: EmailAccount) -> EmailThread:
    thread = EmailThread(
        id="thread123",
        subject="Test Thread Subject",
        user_id=mock_user.id,
        email_account_id=mock_email_account.id,
        last_message_at=datetime.datetime.utcnow()
    )
    return thread

@pytest.fixture
def mock_email_message(mock_user: User, mock_email_account: EmailAccount, mock_email_thread: EmailThread) -> EmailMessage:
    message = EmailMessage(
        id=1,
        message_id_header="<msg1@example.com>",
        thread_id=mock_email_thread.id,
        email_account_id=mock_email_account.id,
        user_id=mock_user.id,
        subject="Test Email Subject",
        sender_address="sender@example.com",
        sent_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=10),
        received_at=datetime.datetime.utcnow(),
        body_text="This is a test email body.",
        is_read=False,
        is_fetched_complete=True,
        category="INBOX"
    )
    # message.user = mock_user # If relationships are directly accessed
    # message.account = mock_email_account
    # message.thread = mock_email_thread
    return message

@pytest.fixture
def mock_db_session() -> MagicMock:
    session = MagicMock(spec=Session)
    # Configure common query patterns if needed, or per-test
    # Example: session.query(Model).filter(...).first.return_value = ...
    return session

# --- Tests for get_message_by_id ---
def test_get_message_by_id_found(mock_db_session: MagicMock, mock_email_message: EmailMessage, mock_user: User):
    # Configure the mock session for this specific test case
    # Query for EmailMessage, filter by id and user_id, then options(selectinload), then first()
    mock_db_session.query(EmailMessage).filter().options().first.return_value = mock_email_message

    result = crud_email_content.get_message_by_id(db=mock_db_session, message_id=mock_email_message.id, user_id=mock_user.id)

    assert result is not None
    assert result.id == mock_email_message.id
    assert result.message_id_header == mock_email_message.message_id_header
    # Check that query was called as expected (simplified check)
    mock_db_session.query(EmailMessage).filter().options().first.assert_called_once()

def test_get_message_by_id_not_found(mock_db_session: MagicMock, mock_user: User):
    mock_db_session.query(EmailMessage).filter().options().first.return_value = None

    result = crud_email_content.get_message_by_id(db=mock_db_session, message_id=999, user_id=mock_user.id)

    assert result is None
    mock_db_session.query(EmailMessage).filter().options().first.assert_called_once()

def test_get_message_by_id_wrong_user(mock_db_session: MagicMock, mock_email_message: EmailMessage, mock_user: User):
    # This test assumes the filter for user_id in get_message_by_id is effective.
    # The mock setup here simulates that the DB would return None if the user_id doesn't match.
    mock_db_session.query(EmailMessage).filter().options().first.return_value = None

    result = crud_email_content.get_message_by_id(db=mock_db_session, message_id=mock_email_message.id, user_id=mock_user.id + 1) # Different user ID

    assert result is None

# --- Tests for get_threads_for_user ---
def test_get_threads_for_user_no_account_id(mock_db_session: MagicMock, mock_email_thread: EmailThread, mock_user: User):
    mock_threads = [mock_email_thread]
    # query().filter().order_by().offset().limit().all()
    mock_db_session.query(EmailThread).filter().order_by().offset().limit().all.return_value = mock_threads

    result = crud_email_content.get_threads_for_user(db=mock_db_session, user_id=mock_user.id, skip=0, limit=10)

    assert result == mock_threads
    # Add more specific assertions about how filter was called if needed
    # Example: mock_db_session.query(EmailThread).filter.assert_any_call(EmailThread.user_id == mock_user.id)

def test_get_threads_for_user_with_account_id(mock_db_session: MagicMock, mock_email_thread: EmailThread, mock_user: User, mock_email_account: EmailAccount):
    mock_threads = [mock_email_thread] # Assume this thread matches the account_id
    mock_email_thread.email_account_id = mock_email_account.id # Ensure fixture matches

    # query().filter().filter().order_by().offset().limit().all()
    mock_db_session.query(EmailThread).filter().filter().order_by().offset().limit().all.return_value = mock_threads

    result = crud_email_content.get_threads_for_user(
        db=mock_db_session,
        user_id=mock_user.id,
        account_id=mock_email_account.id,
        skip=0, limit=10
    )

    assert result == mock_threads
    # Add more specific assertions about how filter was called for user_id and account_id

# --- Tests for get_previous_messages_in_thread ---
# Similar structure: mock the query chain and its result, then assert.

# (Further tests for other CRUD functions can be added here)
