from sqlalchemy.orm import Session
from typing import List

from app.models.email_account import EmailAccount as EmailAccountModel
from app.schemas.email_account import EmailAccountCreate
from app.utils.encryption import encrypt_data


def create_email_account(db: Session, email_account_in: EmailAccountCreate, user_id: int) -> EmailAccountModel:
    encrypted_pass = None
    if email_account_in.password:
        encrypted_pass = encrypt_data(email_account_in.password)

    encrypted_access_tok = None
    if email_account_in.access_token:
        encrypted_access_tok = encrypt_data(email_account_in.access_token)

    encrypted_refresh_tok = None
    if email_account_in.refresh_token: # Assuming refresh_token was added to schema
        encrypted_refresh_tok = encrypt_data(email_account_in.refresh_token)

    db_email_account = EmailAccountModel(
        user_id=user_id,
        email_address=email_account_in.email_address,
        email_user=email_account_in.email_user if email_account_in.email_user else email_account_in.email_address,
        imap_server=email_account_in.imap_server,
        imap_port=email_account_in.imap_port,
        smtp_server=email_account_in.smtp_server,
        smtp_port=email_account_in.smtp_port,
        encrypted_password=encrypted_pass,
        encrypted_access_token=encrypted_access_tok,
        encrypted_refresh_token=encrypted_refresh_tok
        # Add other flags like imap_use_ssl etc. if they are in the model/schema
    )
    db.add(db_email_account)
    db.commit()
    db.refresh(db_email_account)
    return db_email_account


def get_email_accounts_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[EmailAccountModel]:
    return (
        db.query(EmailAccountModel)
        .filter(EmailAccountModel.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
