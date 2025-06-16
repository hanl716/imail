import imaplib
import email
from email.header import decode_header
from flask import current_app # To access app.config

def decode_subject(header):
    """Decodes email subject header to a readable string."""
    decoded_parts = decode_header(header)
    subject = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                subject += part.decode(charset or 'utf-8', errors='replace')
            except LookupError: # Handle unknown charset
                subject += part.decode('utf-8', errors='replace') # Fallback to utf-8
        else:
            subject += part # Already a string
    return subject

def get_email_body(msg):
    """Extracts plain text and HTML body from an email message."""
    text_body = ""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" not in content_disposition: # ignore attachments
                if content_type == "text/plain" and not text_body:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        text_body = part.get_payload(decode=True).decode(charset, errors='replace')
                    except Exception as e:
                        print(f"Error decoding text part: {e}")
                        text_body = "[Could not decode text body]"
                elif content_type == "text/html" and not html_body:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = part.get_payload(decode=True).decode(charset, errors='replace')
                    except Exception as e:
                        print(f"Error decoding HTML part: {e}")
                        html_body = "[Could not decode HTML body]"
    else: # Not multipart, try to get the body directly
        content_type = msg.get_content_type()
        if content_type == 'text/plain':
            try:
                charset = msg.get_content_charset() or 'utf-8'
                text_body = msg.get_payload(decode=True).decode(charset, errors='replace')
            except Exception as e:
                print(f"Error decoding non-multipart text body: {e}")
                text_body = "[Could not decode body]"
    return text_body, html_body


def parse_sender(sender_header):
    """Parses the sender's email address from the 'From' header."""
    if not sender_header:
        return "Unknown Sender"
    # The From header can be "Display Name <email@example.com>" or just "email@example.com"
    # email.utils.parseaddr is good for this: ('Display Name', 'email@example.com')
    parsed_addr = email.utils.parseaddr(sender_header)
    return parsed_addr[1] if parsed_addr[1] else sender_header # return email part, or original if parsing fails


def fetch_emails(account_name, limit=30): # Increased limit to 30
    """
    Fetches emails from the specified account using IMAP.
    Returns a list of parsed email dictionaries.
    """
    if not current_app:
        print("Error: Flask app context not available.")
        return []

    email_accounts_config = current_app.config.get('EMAIL_ACCOUNTS')
    if not email_accounts_config or account_name not in email_accounts_config:
        print(f"Error: Configuration for account '{account_name}' not found.")
        return []

    config = email_accounts_config[account_name]
    imap_server = config.get("imap_server")
    email_address = config.get("email_address")
    password = config.get("password")
    folder = config.get("folder", "INBOX")

    if not all([imap_server, email_address, password]):
        print(f"Error: Missing IMAP credentials for account '{account_name}'. Please check your config or .env file.")
        # Optionally, you could raise an error here or return a specific message
        # For now, returning an empty list to avoid breaking the app if config is missing
        return []

    parsed_emails = []

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        mail.select(f'"{folder}"') # Folders can have spaces, quote them

        # Search for all emails and get UIDs
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            print(f"Error searching emails in {folder}: {status}")
            mail.logout()
            return []

        email_uids = messages[0].split()

        # Fetch latest 'limit' emails
        email_uids = email_uids[-limit:]

        for uid in reversed(email_uids): # Get newest first
            status, msg_data = mail.fetch(uid, "(RFC822)")
            if status == "OK":
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        raw_email = response_part[1]
                        msg = email.message_from_bytes(raw_email)

                        subject = decode_subject(msg["subject"])
                        # Use parse_sender to get a cleaner email address for grouping
                        sender_raw = msg["from"]
                        sender_email = parse_sender(sender_raw)
                        recipient = msg["to"]
                        date_raw = msg["date"]

                        # Attempt to parse date string into a datetime object for sorting (optional for now, can be complex)
                        # For simplicity, we'll keep it as a string from the email header.
                        # Proper date parsing would involve email.utils.parsedate_to_datetime

                        text_body, html_body = get_email_body(msg)

                        body_to_display = text_body if text_body else html_body

                        parsed_emails.append({
                            "uid": uid.decode(),
                            "subject": subject,
                            "from_raw": sender_raw, # Keep original "From" for display if needed
                            "from_email": sender_email, # Parsed email for grouping
                            "to": recipient,
                            "date": date_raw, # Keep as string for now
                            "body": body_to_display,
                            "snippet": (body_to_display[:150] + '...') if body_to_display else "", # Slightly longer snippet
                            "account_name": account_name # Added account_name
                        })
        mail.close()
        mail.logout()
    except imaplib.IMAP4.error as e:
        print(f"IMAP Error for account {account_name}: {e} (Server: {imap_server}, User: {email_address})")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while fetching emails for {account_name}: {e}")
        return []

    return parsed_emails
