import email # For EmailMessage object construction
import email.utils # For formatdate and make_msgid
import logging # For logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app import models
from app import schemas
from app.core.limiter import limiter
from app.database import get_db
from app.security import get_current_user
from app.models.email_account import EmailAccount
from app.services import email_connector # Import as module to access all its functions
from app.utils.encryption import decrypt_data
from app.core.config import FERNET_KEY

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/send-email", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute") # Apply rate limit: 10 requests per minute
async def send_composed_email(
    request: Request, # Added request
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


        # --- Save to Sent Folder (Best Effort) ---
        logger.info(f"Attempting to save sent email to 'Sent' folder for account {account.id}")
        imap_conn_sent = None
        try:
            # Construct the EmailMessage object for saving
            msg_to_save = email.message.EmailMessage()
            # Ensure 'From' header is correctly set to the sending user's email address on the account
            msg_to_save["From"] = account.email_address
            msg_to_save["To"] = ", ".join(composed_email.to_recipients)
            if composed_email.cc_recipients:
                msg_to_save["Cc"] = ", ".join(composed_email.cc_recipients)
            # BCC recipients are NOT included in the headers of the stored sent message
            msg_to_save["Subject"] = composed_email.subject
            msg_to_save.set_content(composed_email.body_text)
            if composed_email.body_html:
                msg_to_save.add_alternative(composed_email.body_html, subtype='html')

            msg_to_save['Date'] = email.utils.formatdate(localtime=True) # Current time for sent date
            msg_to_save['Message-ID'] = email.utils.make_msgid() # Generate a unique Message-ID

            # Assuming password is used for IMAP, same as SMTP for this account
            # If OAuth tokens were used, this logic would differ (e.g., using access_token for IMAP)
            imap_password_to_use = password # Re-use decrypted SMTP password

            if account.imap_server and account.imap_port and (account.email_user or account.email_address) and imap_password_to_use:
                # Infer IMAP SSL from common port or use a stored account preference
                imap_use_ssl = account.imap_port == 993 # Common IMAP SSL port

                imap_conn_sent = email_connector.connect_imap(
                    host=account.imap_server,
                    port=account.imap_port,
                    email_user=(account.email_user or account.email_address),
                    password=imap_password_to_use,
                    use_ssl=imap_use_ssl
                )
                if imap_conn_sent:
                    # Common "Sent" folder names: "Sent", "[Gmail]/Sent Mail", "Sent Items"
                    # This should ideally be configurable per account or auto-detected.
                    sent_mailbox_name = "Sent" # MVP: Use a common default

                    append_success = email_connector.append_to_mailbox(imap_conn_sent, sent_mailbox_name, msg_to_save)
                    if not append_success:
                        logger.warning(f"Failed to append message to '{sent_mailbox_name}' for account {account.email_address}, but email was sent via SMTP.")
            else:
                logger.warning(f"Missing IMAP details or credentials for account {account.id}, cannot save to Sent folder.")

        except Exception as e_append:
            logger.error(f"Failed to save email to Sent folder for account {account.id}: {e_append}", exc_info=True)
        finally:
            if imap_conn_sent:
                email_connector.disconnect_imap(imap_conn_sent)
        # --- End Save to Sent Folder ---

        return {"message": "Email sent successfully. Attempted to save to Sent folder."}

    except email_connector.EmailConnectionError as e:
        logger.error(f"SMTP Connection Error for account {account.email_address}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"SMTP Connection Error: Could not connect to email server.")
    except email_connector.EmailSendError as e:
        logger.error(f"Email Sending Error for account {account.email_address}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Email Sending Error: Failed to send email.")
    except Exception as e:
        logger.error(f"Unexpected error during email sending process for account {account.email_address}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while sending the email.")
    finally:
        if smtp_conn:
            email_connector.disconnect_smtp(smtp_conn)
