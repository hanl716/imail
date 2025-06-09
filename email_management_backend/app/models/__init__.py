from .user import User
from .email_account import EmailAccount
from .email_content import EmailThread, EmailMessage, EmailAttachment
from .complaint_data import ComplaintData # New model for complaints/suggestions
from app.database import Base

__all__ = [
    "User",
    "EmailAccount",
    "EmailThread",
    "EmailMessage",
    "EmailAttachment",
    "ComplaintData", # Added new model
    "Base",
]
