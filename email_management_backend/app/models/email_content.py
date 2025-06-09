from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, LargeBinary, JSON
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class EmailThread(Base):
    __tablename__ = "email_threads"

    id = Column(String, primary_key=True, index=True) # Could be a unique ID like the first message's Message-ID header or a generated UUID
    subject = Column(String, index=True, nullable=True) # Normalized subject of the thread
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    last_message_at = Column(DateTime, index=True, nullable=True)
    snippet = Column(String(255), nullable=True) # Store a short snippet of the last/first message
    participants_json = Column(JSON, nullable=True) # Store list of participant email addresses for quick display

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationship to messages in this thread
    messages = relationship("EmailMessage", back_populates="thread", cascade="all, delete-orphan")
    user = relationship("User")


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id_header = Column(String, unique=True, nullable=False, index=True) # From 'Message-ID'

    # Threading: Link to EmailThread table
    thread_id = Column(String, ForeignKey("email_threads.id", ondelete="CASCADE"), nullable=True, index=True)

    email_account_id = Column(Integer, ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True) # Denormalized for easier user-level queries

    subject = Column(String, index=True, nullable=True)
    sender_address = Column(String, index=True, nullable=True) # From 'From' header

    # Recipients are stored as JSON arrays of strings
    recipients_to = Column(JSON, nullable=True) # e.g., ["user1@example.com", "user2@example.com"]
    recipients_cc = Column(JSON, nullable=True)
    recipients_bcc = Column(JSON, nullable=True) # Usually not present in received emails, but can be stored if sending

    sent_at = Column(DateTime, nullable=True, index=True) # From 'Date' header
    received_at = Column(DateTime, default=datetime.datetime.utcnow, index=True) # When our system processed it

    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)

    headers = Column(JSON, nullable=True) # Store all headers as a JSON object (dict)

    # For simpler threading logic if not using a separate Thread table or for reference
    in_reply_to_header = Column(String, nullable=True, index=True) # From 'In-Reply-To'
    references_header = Column(Text, nullable=True) # From 'References'

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    is_fetched_complete = Column(Boolean, default=False, nullable=False) # Flag if full content + attachments are processed
    category = Column(String(50), nullable=True, index=True, default="INBOX") # Default to INBOX from constants

    # Relationships
    account = relationship("EmailAccount")
    user = relationship("User")
    thread = relationship("EmailThread", back_populates="messages")
    attachments = relationship("EmailAttachment", back_populates="email_message", cascade="all, delete-orphan")


class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id = Column(Integer, primary_key=True, index=True)
    email_message_id = Column(Integer, ForeignKey("email_messages.id", ondelete="CASCADE"), nullable=False, index=True)

    filename = Column(String, nullable=True) # Can be null if not specified
    content_type = Column(String, nullable=False)
    content_id = Column(String, nullable=True, index=True) # For inline attachments (CID)
    size_bytes = Column(Integer, nullable=False)

    # For storing attachment content:
    # Option 1: Store in DB (only for very small files, generally not recommended for large ones)
    # content_bytes = Column(LargeBinary, nullable=True)
    # Option 2: Store path to file on disk/S3
    storage_path = Column(String, nullable=True) # e.g., "attachments/user_id/message_id/filename"

    # Relationship
    email_message = relationship("EmailMessage", back_populates="attachments")
