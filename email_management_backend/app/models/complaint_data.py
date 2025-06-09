from sqlalchemy import Column, Integer, String, Text, Enum as DBEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

# It's good practice to define Enums for fields like issue_type and sentiment if they have fixed values
# However, for flexibility with AI output, String might be used initially, then validated against preferred values.
# For this model, we'll use String and validation can happen at service layer or rely on AI's enum from schema.

class ComplaintData(Base):
    __tablename__ = "complaint_suggestions"

    id = Column(Integer, primary_key=True, index=True)

    # Link to the original email message
    email_message_id = Column(Integer, ForeignKey("email_messages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Denormalize user_id for easier querying, though it's also on EmailMessage
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    submitter_email = Column(String, index=True, nullable=False)
    submitter_name = Column(String, nullable=True)

    issue_type = Column(String(50), nullable=False)  # e.g., "Complaint", "Suggestion", "Query"
    category_detail = Column(String(100), nullable=True) # e.g., "Billing", "Service Quality", "New Feature"
    product_service = Column(String(100), nullable=True) # Product/service mentioned

    summary = Column(Text, nullable=False) # AI-generated summary
    sentiment = Column(String(50), nullable=True) # e.g., "Positive", "Negative", "Neutral"

    extracted_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships (optional, but can be useful)
    # email_message = relationship("EmailMessage", back_populates="complaint_suggestion_data") # Add back_populates to EmailMessage if needed
    user = relationship("User")

# If EmailMessage needs a back_populates for a one-to-one (if unique=True on FK):
# In EmailMessage model:
# complaint_suggestion_data = relationship("ComplaintData", back_populates="email_message", uselist=False, cascade="all, delete-orphan")
