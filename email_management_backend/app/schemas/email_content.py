from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Dict
import datetime

# --- Email Attachment Schemas ---
class EmailAttachmentOutput(BaseModel):
    id: int
    filename: Optional[str]
    content_type: str
    size_bytes: int
    content_id: Optional[str] = None

    class Config:
        orm_mode = True

# --- Email Message Schemas ---
class EmailMessageOutput(BaseModel):
    id: int
    message_id_header: str
    subject: Optional[str] = None
    sender_address: Optional[str] = None # This would be the raw 'From' address
    sent_at: Optional[datetime.datetime] = None # Make optional as parsing can fail
    received_at: Optional[datetime.datetime] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None # Consider security implications for rendering HTML
    is_read: bool
    category: Optional[str] = None # Added category field
    attachments: List[EmailAttachmentOutput] = []

    # For threading context if needed directly on message
    thread_id: Optional[str] = None
    in_reply_to_header: Optional[str] = None
    # references_header: Optional[str] = None # Usually not sent to client directly

    # Raw headers can be large, decide if needed for client
    # headers: Optional[Dict[str, Any]] = None

    recipients_to: Optional[List[str]] = None
    recipients_cc: Optional[List[str]] = None
    # bcc not usually included

    class Config:
        orm_mode = True

# --- Email Thread Schemas ---
class EmailThreadOutput(BaseModel):
    id: str
    subject: Optional[str] = None
    # user_id: int # Usually not exposed directly in thread list if API is user-scoped
    last_message_at: Optional[datetime.datetime] = None
    snippet: Optional[str] = None # e.g., from last message
    # Example: A simplified participants representation
    # For more complex participant info, a dedicated endpoint/schema might be better
    # participant_addresses: Optional[List[EmailStr]] = None

    # UI might also want message_count or unread_count for the thread
    # These would typically be computed fields or loaded with the thread
    # message_count: Optional[int] = None
    # unread_message_count: Optional[int] = None


    class Config:
        orm_mode = True
