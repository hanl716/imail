"""
Handles interactions with IMAP email servers for fetching and parsing emails.

This service connects to an IMAP server using credentials from the application configuration,
retrieves emails, parses their content (subject, sender, body, attachments),
and returns them in a structured format.
"""
import imaplib # For IMAP communication
import email # For parsing email messages (standard library)
from email.header import decode_header # For decoding email headers (e.g., subject, sender)
from email.utils import parseaddr # For parsing email addresses like "Name <email@example.com>"
from flask import current_app # To access Flask application context (e.g., config, logger)

# Module-level logger can be used if preferred, or use current_app.logger within functions.
# import logging
# logger = logging.getLogger(__name__)

def decode_subject(header_string):
    """
    Decodes an email subject header string to a human-readable format.
    Handles various character encodings that might be present in email headers.

    Args:
        header_string (str): The raw subject header string.

    Returns:
        str: The decoded subject string. Returns the original if decoding fails or not needed.
    """
    if not header_string:
        return ""
    decoded_parts = decode_header(header_string)
    subject_str = ""
    for part_content, part_charset in decoded_parts:
        if isinstance(part_content, bytes):
            try:
                # If charset is None, decode_header often means it's ascii or a default.
                # Using 'utf-8' as a robust fallback. 'errors=replace' prevents crashes.
                subject_str += part_content.decode(part_charset or 'utf-8', errors='replace')
            except LookupError: # Happens if the charset is unknown to Python's codecs
                subject_str += part_content.decode('utf-8', errors='replace') # Fallback to UTF-8
        elif isinstance(part_content, str):
            subject_str += part_content # Part is already a string
        # else: ignore if part_content is not bytes or str (though decode_header should handle this)
    return subject_str if subject_str else header_string # Return original if decoding resulted in empty

def get_email_body(email_message):
    """
    Extracts plain text and HTML body content from an `email.message.Message` object.
    It prioritizes plain text. If not found, it takes HTML. Attachments are ignored here.

    Args:
        email_message (email.message.Message): The parsed email message object.

    Returns:
        tuple: (text_body, html_body) where each can be a string or empty string.
    """
    text_body = ""
    html_body = ""
    # Walk through all parts of the email message
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Check if the part is an attachment; if so, skip it for body extraction.
            if "attachment" in content_disposition:
                continue

            # Extract plain text body, if not already found
            if content_type == "text/plain" and not text_body:
                try:
                    payload = part.get_payload(decode=True) # Decode from Base64 or Quoted-Printable
                    charset = part.get_content_charset() or 'utf-8' # Guess charset or default to UTF-8
                    text_body = payload.decode(charset, errors='replace')
                except Exception as e:
                    # Log error if current_app context is available, otherwise print
                    log_func = current_app.logger.error if current_app else print
                    log_func(f"Error decoding text part: {e}")
                    text_body = "[Could not decode plain text body]"
            # Extract HTML body, if not already found
            elif content_type == "text/html" and not html_body:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    html_body = payload.decode(charset, errors='replace')
                except Exception as e:
                    log_func = current_app.logger.error if current_app else print
                    log_func(f"Error decoding HTML part: {e}")
                    html_body = "[Could not decode HTML body]"
    else: # Not a multipart message, payload is directly on the message object
        content_type = email_message.get_content_type()
        if content_type == 'text/plain':
            try:
                payload = email_message.get_payload(decode=True)
                charset = email_message.get_content_charset() or 'utf-8'
                text_body = payload.decode(charset, errors='replace')
            except Exception as e:
                log_func = current_app.logger.error if current_app else print
                log_func(f"Error decoding non-multipart text body: {e}")
                text_body = "[Could not decode body]"
        # Note: Could add similar handling for non-multipart HTML emails if necessary

    return text_body, html_body


def parse_sender(sender_header_string):
    """
    Parses the sender's name and email address from a 'From' or 'To' header string.

    Args:
        sender_header_string (str): The raw header string (e.g., "John Doe <john.doe@example.com>").

    Returns:
        str: The email address part if successfully parsed, otherwise the original header string or a default.
             The goal here is to get a clean email address for grouping or contact matching.
    """
    if not sender_header_string:
        return "Unknown Sender"

    # `parseaddr` returns a tuple: (Real Name, email_address)
    # Example: "John Doe <johndoe@example.com>" -> ('John Doe', 'johndoe@example.com')
    # Example: "johndoe@example.com" -> ('', 'johndoe@example.com')
    name, addr = parseaddr(sender_header_string)

    # Return the address part if it's a valid-looking email (contains '@').
    # Otherwise, the original string might be the best guess (or it's not an email address).
    return addr if '@' in addr else sender_header_string


def fetch_emails(account_name, limit=30):
    """
    Fetches a list of emails from the specified IMAP account.

    Connects to the IMAP server, logs in, selects a mailbox (folder),
    searches for emails, fetches their content, and parses them into a
    structured list of dictionaries. Each dictionary represents an email
    and includes details like subject, sender, body, date, and attachments.

    Args:
        account_name (str): The key for the email account in `current_app.config['EMAIL_ACCOUNTS']`.
        limit (int, optional): The maximum number of recent emails to fetch. Defaults to 30.

    Returns:
        list: A list of dictionaries, where each dictionary contains parsed email data.
              Returns an empty list if fetching fails or no emails are found.
    """
    Returns a list of parsed email dictionaries.
    """
    # Use current_app.logger if available (within Flask request context), otherwise fallback to print.
    log_info = current_app.logger.info if current_app else lambda x: print(f"INFO: {x}")
    log_error = current_app.logger.error if current_app else lambda x: print(f"ERROR: {x}")
    log_warning = current_app.logger.warning if current_app else lambda x: print(f"WARNING: {x}")

    if not current_app: # Should ideally not happen if called from a Flask route
        log_warning("Flask app context not available in fetch_emails. Logging to print.")
        # Depending on strictness, could return [] here or raise an error.
        # For now, proceed with print logging if no app context.

    email_accounts_config = current_app.config.get('EMAIL_ACCOUNTS') if current_app else None
    if not email_accounts_config or account_name not in email_accounts_config:
        log_error(f"Configuration for email account '{account_name}' not found.")
        return []

    config = email_accounts_config[account_name]
    imap_server = config.get("imap_server")
    email_address = config.get("email_address")
    password = config.get("password")
    folder = config.get("folder", "INBOX") # Default to INBOX if not specified

    if not all([imap_server, email_address, password]):
        log_error(f"Missing IMAP credentials for account '{account_name}'. Please check configuration.")
        return []

    parsed_emails = [] # List to store successfully parsed email data

    try:
        log_info(f"Connecting to IMAP server: {imap_server} for account: {email_address}")
        mail = imaplib.IMAP4_SSL(imap_server) # Use SSL for secure connection
        mail.login(email_address, password)

        # Select the mailbox/folder. Quote folder name to handle spaces or special characters.
        status, select_data = mail.select(f'"{folder}"')
        if status != "OK":
            log_error(f"Failed to select folder '{folder}': {select_data[0].decode('utf-8', errors='replace')}")
            mail.logout()
            return []
        log_info(f"Selected folder '{folder}'. Number of messages: {select_data[0].decode('utf-8', errors='replace')}")

        # Search for all emails in the selected folder and get their UIDs
        status, messages_data = mail.search(None, "ALL") # Search for all messages
        if status != "OK":
            log_error(f"Failed to search emails in '{folder}': {messages_data[0].decode('utf-8', errors='replace')}")
            mail.logout()
            return []

        email_uids_bytes = messages_data[0].split() # UIDs are returned as a space-separated string of bytes
        log_info(f"Found {len(email_uids_bytes)} email UIDs in '{folder}'. Fetching last {limit}.")

        # Fetch the latest 'limit' emails by taking the last 'limit' UIDs
        # UIDs are typically sequential and increasing, so last ones are newest.
        email_uids_to_fetch = email_uids_bytes[-limit:]

        # Iterate over UIDs in reverse to process newest emails first
        for uid_bytes in reversed(email_uids_to_fetch):
            # Fetch the full email message (RFC822 format)
            status, msg_data_parts = mail.fetch(uid_bytes, "(RFC822)")
            if status == "OK":
                # msg_data_parts is a list of tuples, e.g., [(b'1 (RFC822 {size}', email_bytes), b')']
                # We need the actual email bytes, which is typically response_part[1] of the first tuple part.
                for response_part in msg_data_parts:
                    if isinstance(response_part, tuple) and len(response_part) == 2:
                        raw_email_bytes = response_part[1]
                        # Parse the raw email bytes into an email.message.Message object
                        email_message_obj = email.message_from_bytes(raw_email_bytes)

                        # Decode headers (Subject, From, To, Date)
                        subject = decode_subject(email_message_obj["subject"])
                        sender_raw_header = email_message_obj["from"]
                        sender_email_address = parse_sender(sender_raw_header)
                        recipient_header = email_message_obj["to"] # Can be multiple, comma-separated
                        date_raw_header = email_message_obj["date"]

                        # Extract body content (plain text and HTML)
                        text_body, html_body = get_email_body(email_message_obj)
                        # Prioritize plain text for display snippet, fallback to HTML if plain is empty
                        body_to_display_for_snippet = text_body if text_body else html_body

                        # --- Attachment Handling ---
                        attachments_metadata_list = []
                        if email_message_obj.is_multipart():
                            for part in email_message_obj.walk():
                                content_disposition = str(part.get("Content-Disposition"))
                                # Check if the part is an attachment
                                if "attachment" in content_disposition:
                                    filename = part.get_filename()
                                    if filename: # If filename exists, decode it
                                        decoded_fn_parts = decode_header(filename)
                                        decoded_fn_str = ""
                                        for fn_content, fn_charset in decoded_fn_parts:
                                            if isinstance(fn_content, bytes):
                                                try:
                                                    decoded_fn_str += fn_content.decode(fn_charset or 'utf-8', 'replace')
                                                except LookupError: # Unknown charset
                                                    decoded_fn_str += fn_content.decode('utf-8', 'replace')
                                            else: # Already a string
                                                decoded_fn_str += fn_content
                                        filename = decoded_fn_str if decoded_fn_str else "untitled_attachment"
                                    else: # No filename in Content-Disposition
                                        filename = "untitled_attachment"

                                    attachment_content_type = part.get_content_type()
                                    attachment_payload_bytes = part.get_payload(decode=True) # Get raw attachment bytes

                                    attachments_metadata_list.append({
                                        'filename': filename,
                                        'content_type': attachment_content_type,
                                        'size': len(attachment_payload_bytes),
                                        'payload': attachment_payload_bytes # Include raw bytes for potential upload
                                    })
                        # --- End Attachment Handling ---

                        # Construct the email dictionary with parsed data
                        email_details_dict = {
                            "uid": uid_bytes.decode(), # Store UID for potential future operations (e.g., delete, mark as read)
                            "subject": subject,
                            "from_raw": sender_raw_header, # Original "From" header
                            "from_email": sender_email_address, # Parsed sender email
                            "to": recipient_header, # Original "To" header
                            "date": date_raw_header, # Original "Date" header
                            "body": body_to_display_for_snippet, # Store the preferred body for snippet/initial view
                                                              # Could also store both text_body and html_body if needed separately
                            "snippet": (body_to_display_for_snippet[:150] + '...') if body_to_display_for_snippet else "",
                            "account_name": account_name, # Identify source account
                            "attachments": attachments_metadata_list # List of attachment metadata dictionaries
                        }
                        parsed_emails.append(email_details_dict)
                        break # Processed this email UID, move to next UID in outer loop

        # Close connection and logout from IMAP server
        mail.close() # Close the selected mailbox
        mail.logout()
        log_info(f"Successfully fetched and parsed {len(parsed_emails)} emails from {account_name}.")

    except imaplib.IMAP4.error as e: # Handle IMAP-specific errors (e.g., login failure, server issues)
        log_error(f"IMAP Error for account {account_name} (Server: {imap_server}, User: {email_address}): {e}")
        # Optionally, re-raise or return a more specific error message to the caller
        return []
    except Exception as e: # Catch any other unexpected errors during the process
        log_error(f"An unexpected error occurred while fetching emails for {account_name}: {e}", exc_info=True)
        return []

    return parsed_emails
