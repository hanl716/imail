import imaplib
import smtplib
import ssl
import logging # Import logging
from email.message import EmailMessage
from typing import List, Tuple, Any

logger = logging.getLogger(__name__) # Setup logger for this module

# Custom Exceptions for clarity (optional)
class EmailConnectionError(Exception):
    pass

class EmailLoginError(EmailConnectionError):
    pass

class MailboxSelectError(EmailConnectionError):
    pass

class EmailFetchError(EmailConnectionError):
    pass

class EmailSendError(Exception):
    pass


# --- IMAP Functions ---

def connect_imap(host: str, port: int, email_user: str, password: str, use_ssl: bool = True) -> imaplib.IMAP4:
    """
    Connects to an IMAP server and logs in.
    """
    try:
        if use_ssl:
            imap_conn = imaplib.IMAP4_SSL(host, port)
        else:
            imap_conn = imaplib.IMAP4(host, port)

        status, response = imap_conn.login(email_user, password)
        if status != 'OK':
            # Decode response for logging if it's bytes
            response_str = response[0].decode() if isinstance(response[0], bytes) else response[0]
            logger.error(f"IMAP login failed for {email_user} on {host}. Status: {status}, Response: {response_str}")
            raise EmailLoginError(f"IMAP login failed for {email_user}: {response_str}")
        logger.info(f"Successfully connected to IMAP server: {host} for user {email_user}")
        return imap_conn
    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP connection or login error for {email_user} on {host}: {e}", exc_info=True)
        raise EmailConnectionError(f"IMAP connection or login error for {email_user} on {host}: {e}")
    except Exception as e: # Catch other potential errors like socket errors
        logger.error(f"Unexpected error during IMAP connection for {email_user} on {host}: {e}", exc_info=True)
        raise EmailConnectionError(f"Unexpected error during IMAP connection for {email_user} on {host}: {e}")

def disconnect_imap(imap_conn: imaplib.IMAP4):
    """
    Logs out and closes the IMAP connection.
    """
    if not imap_conn:
        return
    try:
        imap_conn.logout()
        logger.info("Successfully logged out from IMAP server.")
    except imaplib.IMAP4.error as e:
        logger.warning(f"Error during IMAP logout: {e}", exc_info=True)
    finally:
        # IMAP4_SSL objects don't have a separate close, logout handles it.
        # For IMAP4 (non-SSL), close might be relevant if logout fails.
        # However, imaplib standard is just logout.
        pass


def list_mailboxes(imap_conn: imaplib.IMAP4) -> List[str]:
    """
    Lists all mailboxes.
    Returns a list of mailbox names.
    """
    mailboxes = []
    try:
        status, mailbox_data = imap_conn.list()
        if status == 'OK':
            for mb_info in mailbox_data:
                # Mailbox info is usually a byte string like:
                # b'(\\HasNoChildren) "/" "INBOX"'
                # We need to decode and extract the mailbox name
                parts = mb_info.decode().split('"')
                if len(parts) >= 3: # Basic parsing, might need refinement
                    mailboxes.append(parts[-2]) # The name is usually the second to last quoted string
            return mailboxes
        else:
            raise EmailFetchError(f"Failed to list mailboxes: {mailbox_data}")
    except imaplib.IMAP4.error as e:
        raise EmailFetchError(f"Error listing mailboxes: {e}")
    return mailboxes


def fetch_emails_in_mailbox(
    imap_conn: imaplib.IMAP4,
    mailbox: str = "INBOX",
    search_criteria: str = "ALL",
    count: int = 10
) -> List[Tuple[bytes, bytes]]: # Returns list of (email_id, raw_email_data)
    """
    Fetches a list of emails from the specified mailbox.
    Returns a list of tuples, where each tuple contains (email_id, raw_email_data).
    """
    raw_emails = []
    try:
        status, select_data = imap_conn.select(f'"{mailbox}"', readonly=True) # Use readonly for fetching
        if status != 'OK':
            raise MailboxSelectError(f"Failed to select mailbox {mailbox}: {select_data}")

        # Get total number of messages to adjust count if needed
        # total_messages = int(select_data[0].decode())

        status, email_ids_data = imap_conn.search(None, search_criteria)
        if status != 'OK':
            raise EmailFetchError(f"Failed to search emails in {mailbox}: {email_ids_data}")

        email_id_list = email_ids_data[0].split()
        if not email_id_list:
            return []

        # Fetch latest 'count' emails
        # Email IDs are typically sequential, highest number is most recent.
        # However, search can return them in any order. For simplicity, take last 'count' from the list.
        # For true "latest", sorting or more specific search criteria (e.g., by date) would be needed.
        # Or, UID SEARCH followed by UID FETCH with sorting.

        # Taking the last 'count' IDs from the list (often most recent, but not guaranteed by RFC)
        ids_to_fetch = email_id_list[-count:]

        if not ids_to_fetch:
            return []

        for email_id in reversed(ids_to_fetch): # Fetch in reverse to get newest first if list was ordered
            status, msg_data = imap_conn.fetch(email_id, "(RFC822)")
            if status == 'OK':
                # msg_data is a list of tuples, e.g., [(b'1 (RFC822 {size}', b'raw_email_header_and_body...'), b')']
                # We need the actual email content, which is typically msg_data[0][1]
                if msg_data and isinstance(msg_data[0], tuple) and len(msg_data[0]) == 2:
                    raw_emails.append((email_id, msg_data[0][1]))
                # Handle other formats if necessary, e.g. if not multipart
                elif msg_data and isinstance(msg_data[0], bytes) and len(msg_data) > 1 and isinstance(msg_data[1], bytes) : # some servers might return slightly different structure
                     raw_emails.append((email_id, msg_data[1]))


            else:
                logger.warning(f"Failed to fetch email ID {email_id.decode()} from {mailbox}: {msg_data}")

        return raw_emails
    except imaplib.IMAP4.error as e:
        logger.error(f"Error fetching emails from {mailbox}: {e}", exc_info=True)
        raise EmailFetchError(f"Error fetching emails from {mailbox}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching emails from {mailbox}: {e}", exc_info=True)
        raise EmailFetchError(f"Unexpected error fetching emails from {mailbox}: {e}")
    finally:
        # It's good practice to close the selected mailbox if you opened it non-readonly
        # or if you want to ensure state is reset, though with readonly it's less critical.
        # imap_conn.close() # This unselects the mailbox. Not strictly needed if always re-selecting.
        pass

# --- SMTP Functions ---

def connect_smtp(
    host: str,
    port: int,
    email_user: str,
    password: str,
    use_tls: bool = True,
    use_ssl: bool = False
) -> smtplib.SMTP:
    """
    Connects to an SMTP server and logs in.
    `use_ssl=True` for SMTP_SSL (usually port 465).
    `use_tls=True` for STARTTLS (usually port 587, or 25).
    """
    try:
        if use_ssl:
            smtp_conn = smtplib.SMTP_SSL(host, port)
        else:
            smtp_conn = smtplib.SMTP(host, port)
            if use_tls:
                smtp_conn.starttls(context=ssl.create_default_context()) # Ensure SSL context for TLS

        # Some servers might not require ehlo/helo before login, but it's good practice.
        # smtp_conn.ehlo() # or helo() if ehlo fails

        smtp_conn.login(email_user, password)
        logger.info(f"Successfully connected to SMTP server: {host} for user {email_user}")
        return smtp_conn
    except smtplib.SMTPException as e:
        logger.error(f"SMTP connection or login error for {email_user} on {host}: {e}", exc_info=True)
        raise EmailConnectionError(f"SMTP connection or login error for {email_user} on {host}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during SMTP connection for {email_user} on {host}: {e}", exc_info=True)
        raise EmailConnectionError(f"Unexpected error during SMTP connection for {email_user} on {host}: {e}")

def disconnect_smtp(smtp_conn: smtplib.SMTP):
    """
    Quits the SMTP connection.
    """
    if not smtp_conn:
        return
    try:
        smtp_conn.quit()
        logger.info("Successfully disconnected from SMTP server.")
    except smtplib.SMTPException as e:
        logger.warning(f"Error during SMTP quit: {e}", exc_info=True)


def send_email(
    smtp_conn: smtplib.SMTP,
    sender_email: str,
    recipient_email: str, # Can be a list of recipients for multiple To/Cc/Bcc
    subject: str,
    body_text: str,
    body_html: str | None = None
) -> bool:
    """
    Sends an email using the provided SMTP connection.
    """
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = recipient_email # If recipient_email is a list, EmailMessage handles it correctly
    msg['Subject'] = subject

    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype='html')

    try:
        smtp_conn.send_message(msg)
        logger.info(f"Email sent successfully from {sender_email} to {recipient_email}")
        return True
    except smtplib.SMTPException as e:
        logger.error(f"Failed to send email from {sender_email} to {recipient_email}: {e}", exc_info=True)
        raise EmailSendError(f"Failed to send email from {sender_email} to {recipient_email}: {e}")
    return False


def append_to_mailbox(imap_conn: imaplib.IMAP4, mailbox: str, email_message_obj: EmailMessage) -> bool:
    """
    Appends a given email.message.EmailMessage object to the specified mailbox.
    """
    try:
        message_bytes = email_message_obj.as_bytes()
        # Standard flags for a sent message usually include \Seen.
        # date_time can be None for imaplib to set current server time, or provide specific datetime.
        # Note on mailbox names: some servers are picky (e.g. Gmail uses "[Gmail]/Sent Mail").
        # For MVP, we'll use a common name like "Sent". This should ideally be configurable or auto-detected.

        # Ensure mailbox exists or create it (optional, some servers auto-create on APPEND)
        # status_create, _ = imap_conn.create(mailbox)
        # if status_create != 'OK' and 'exists' not in str(_).lower(): # crude check for "already exists"
        #     logger.warning(f"Could not create or ensure mailbox '{mailbox}' exists. Append may fail.")

        status, response = imap_conn.append(mailbox, r'(\Seen)', None, message_bytes)

        if status == 'OK':
            logger.info(f"Successfully appended email to mailbox '{mailbox}'")
            return True
        else:
            # Decode response for logging if it's bytes
            response_str = response[0].decode() if response and isinstance(response[0], bytes) else str(response)
            logger.error(f"Failed to append email to mailbox '{mailbox}': {response_str}")
            return False
    except Exception as e:
        logger.error(f"Error appending email to mailbox '{mailbox}': {e}", exc_info=True)
        return False
