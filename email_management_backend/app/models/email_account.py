from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, LargeBinary
from app.database import Base

class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # user_id should not be nullable
    email_address = Column(String, nullable=False, index=True)

    # IMAP/SMTP server details, can be discovered or entered by user
    imap_server = Column(String, nullable=True)
    imap_port = Column(Integer, nullable=True)
    smtp_server = Column(String, nullable=True)
    smtp_port = Column(Integer, nullable=True)

    # Username for the email account, might be different from email_address
    email_user = Column(String, nullable=True)

    # Encrypted credentials
    encrypted_password = Column(LargeBinary, nullable=True)  # For basic auth
    encrypted_access_token = Column(LargeBinary, nullable=True)  # For OAuth
    encrypted_refresh_token = Column(LargeBinary, nullable=True) # For OAuth

    is_active = Column(Boolean, default=True, nullable=False) # For enabling/disabling background tasks

    # Potentially add flags for OAuth vs Password auth, SSL/TLS settings etc.
    # is_oauth = Column(Boolean, default=False)
    # imap_use_ssl = Column(Boolean, default=True)
    # smtp_use_tls = Column(Boolean, default=True) # Or smtp_use_ssl

    # Add other relevant fields like is_oauth, refresh_token, etc. later
