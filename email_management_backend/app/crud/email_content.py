from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc
from typing import List, Optional

from app.models.email_content import EmailThread, EmailMessage, EmailAttachment
# User model might be needed for some specific checks, but user_id is primary filter
# from app.models.user import User

def get_threads_for_user(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> List[EmailThread]:
    """
    Fetches threads for a user, ordered by the last message timestamp.
    """
    return (
        db.query(EmailThread)
        .filter(EmailThread.user_id == user_id)
        .order_by(desc(EmailThread.last_message_at)) # Ensure last_message_at is updated
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


# Potentially, functions to get/create attachments could be here too,
# but they are often handled as part of message creation/retrieval.
# Example:
# def get_attachment_by_id(db: Session, attachment_id: int, user_id: int) -> Optional[EmailAttachment]:
#     """ Fetches an attachment, ensuring it belongs to a message owned by the user. """
#     return db.query(EmailAttachment)\
#         .join(EmailAttachment.email_message)\
#         .filter(EmailMessage.user_id == user_id, EmailAttachment.id == attachment_id)\
#         .first()
