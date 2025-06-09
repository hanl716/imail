from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, asc
from typing import List, Optional
import datetime # For type hinting datetime objects

from app.models.email_content import EmailThread, EmailMessage, EmailAttachment
# User model might be needed for some specific checks, but user_id is primary filter
# from app.models.user import User

def get_threads_for_user(
    db: Session,
    user_id: int,
    account_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20
) -> List[EmailThread]:
    """
    Fetches threads for a user, ordered by the last message timestamp.
    Optionally filters by a specific email_account_id.
    """
    query = db.query(EmailThread).filter(EmailThread.user_id == user_id)

    if account_id is not None:
        query = query.filter(EmailThread.email_account_id == account_id)

    return (
        query.order_by(desc(EmailThread.last_message_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_messages_for_thread(db: Session, thread_id: str, user_id: int, skip: int = 0, limit: int = 50) -> List[EmailMessage]:
    """
    Fetches messages for a specific thread ID and user, ordered by sent_at.
    Includes attachments.
    """
    # First, verify the thread belongs to the user to prevent data leakage
    thread = db.query(EmailThread).filter(EmailThread.id == thread_id, EmailThread.user_id == user_id).first()
    if not thread:
        return [] # Or raise HTTPException(status_code=404, detail="Thread not found or access denied")

    return (
        db.query(EmailMessage)
        .filter(EmailMessage.thread_id == thread_id)
        .filter(EmailMessage.user_id == user_id) # Double check user_id for safety, though thread check should suffice
        .options(selectinload(EmailMessage.attachments)) # Efficiently load attachments
        .order_by(EmailMessage.sent_at) # Display oldest first in a thread usually
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_message_by_message_id_header(db: Session, message_id_header: str, user_id: int) -> Optional[EmailMessage]:
    """
    Retrieves a specific email message by its Message-ID header, ensuring it belongs to the user.
    """
    return db.query(EmailMessage).filter(
        EmailMessage.message_id_header == message_id_header,
        EmailMessage.user_id == user_id
    ).first()

def get_message_by_id(db: Session, message_id: int, user_id: int) -> Optional[EmailMessage]:
    """
    Retrieves a specific email message by its primary key ID, ensuring it belongs to the user.
    """
    return db.query(EmailMessage).filter(
        EmailMessage.id == message_id,
        EmailMessage.user_id == user_id
    ).options(selectinload(EmailMessage.attachments)).first() # Also load attachments


def get_previous_messages_in_thread(
    db: Session,
    thread_id: str,
    current_message_sent_at: datetime.datetime,
    user_id: int,
    limit: int = 2
) -> List[EmailMessage]:
    """
    Fetches a few messages from the same thread that were sent before the current message.
    """
    if not current_message_sent_at: # Should ideally not happen if current message is valid
        return []

    return db.query(EmailMessage).filter(
        EmailMessage.thread_id == thread_id,
        EmailMessage.user_id == user_id,
        EmailMessage.sent_at < current_message_sent_at # Messages sent before the current one
    ).order_by(desc(EmailMessage.sent_at)).limit(limit).all() # Get the most recent ones before current


# Potentially, functions to get/create attachments could be here too,
# but they are often handled as part of message creation/retrieval.
# Example:
def get_attachment_by_id(db: Session, attachment_id: int, user_id: int) -> Optional[EmailAttachment]:
    """ Fetches an attachment, ensuring it belongs to a message owned by the user. """
    return db.query(EmailAttachment)\
        .join(EmailAttachment.email_message)\
        .filter(EmailMessage.user_id == user_id, EmailAttachment.id == attachment_id)\
        .first()
