from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models # For User model type hint
from app import schemas # For Pydantic schemas
from app.database import get_db
from app.security import get_current_user
from app.models.email_account import EmailAccount
from app.services.email_connector import connect_smtp, disconnect_smtp, send_email, EmailConnectionError, EmailSendError
from app.utils.encryption import decrypt_data
from app.core.config import FERNET_KEY # To check if encryption is available

router = APIRouter()

@router.post("/send-email", status_code=status.HTTP_202_ACCEPTED) # 202 Accepted as sending is async
async def send_composed_email(
    composed_email: schemas.compose.EmailCompose,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user),
):
    if not FERNET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Encryption service is not configured, cannot send email.",
        )

    # Fetch the sending EmailAccount
    account = db.query(EmailAccount).filter(
        EmailAccount.id == composed_email.from_account_id,
        EmailAccount.user_id == current_user.id # Ensure account belongs to the user
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sending account with ID {composed_email.from_account_id} not found or access denied.",
        )

    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sending account {account.email_address} is not active.",
        )

    # Ensure SMTP details are configured for the account
    if not all([account.smtp_server, account.smtp_port, (account.email_user or account.email_address)]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SMTP server details not configured for account {account.email_address}.",
        )

    # Decrypt password (assuming password-based auth for SMTP for now)
    # OAuth would require decrypting access_token and different SMTP logic.
    password = None
    if account.encrypted_password:
        try:
            password = decrypt_data(account.encrypted_password)
        except Exception as e:
            # Log this error securely
            print(f"Error decrypting password for account {account.email_address}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to prepare email for sending due to credential error.",
            )

    if not password: # Or a valid OAuth token
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No valid credentials available for sending account {account.email_address}.",
        )

    smtp_conn = None
    try:
        # Determine SSL/TLS settings (these should ideally be stored per account)
        # For now, let's assume standard TLS on port 587 or SSL on 465.
        # This logic needs to be more robust based on stored account settings.
        use_ssl = account.smtp_port == 465
        use_tls = not use_ssl # Assume TLS if not explicit SSL port (common for 587, 25)

        # TODO: Add specific flags like account.smtp_use_ssl, account.smtp_use_tls to EmailAccount model

        smtp_conn = connect_smtp(
            host=account.smtp_server,
            port=account.smtp_port,
            email_user=(account.email_user or account.email_address),
            password=password,
            use_ssl=use_ssl,
            use_tls=use_tls
        )

        # The sender_email for the message itself.
        # Using account.email_address as the visible "From" in the email.
        # Using account.email_user (if different) for SMTP authentication.
        actual_sender_for_header = account.email_address

        send_email(
            smtp_conn=smtp_conn,
            sender_email=actual_sender_for_header, # What appears in the "From" field
            recipient_email=composed_email.to_recipients, # send_email handles list
            subject=composed_email.subject,
            body_text=composed_email.body_text,
            body_html=composed_email.body_html
            # TODO: Add CC/BCC handling in send_email and EmailMessage object if needed
        )

        # Optional: Save to "Sent" folder via IMAP (skipped for this subtask's core)

        return {"message": "Email sent successfully."} # Or "Email queued for sending."

    except EmailConnectionError as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"SMTP Connection Error: {e}")
    except EmailSendError as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Email Sending Error: {e}")
    except Exception as e:
        # Log e
        print(f"Unexpected error during email sending: {e}") # Log this for debugging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while sending the email.")
    finally:
        if smtp_conn:
            disconnect_smtp(smtp_conn)
