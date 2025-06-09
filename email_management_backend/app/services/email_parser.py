import email
from email.parser import BytesParser
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime, getaddresses
import re
from typing import List, Dict, Any, TypedDict, Optional, Tuple
import chardet # For robust encoding detection

class ParsedAttachment(TypedDict):
    filename: Optional[str]
    content_type: str
    content_id: Optional[str]
    size_bytes: int
    payload: Optional[bytes] # Payload might be None if too large for DB storage

class ParsedEmailData(TypedDict):
    message_id_header: Optional[str]
    subject: Optional[str]
    sender_name: Optional[str]
    sender_address: str
    recipients_to: List[Tuple[Optional[str], str]] # List of (name, email)
    recipients_cc: List[Tuple[Optional[str], str]]
    recipients_bcc: List[Tuple[Optional[str], str]] # Usually empty from received mail
    sent_at: Optional[datetime.datetime]
    body_text: Optional[str]
    body_html: Optional[str]
    body_text_snippet: Optional[str] # Added for categorization
    headers: Dict[str, Any] # Store all headers
    in_reply_to_header: Optional[str]
    references_header: Optional[str]
    attachments: List[ParsedAttachment]

def _decode_header_value(header_value: Optional[str]) -> Optional[str]:
    if header_value is None:
        return None
    try:
        decoded_parts = decode_header(header_value)
        return str(make_header(decoded_parts))
    except Exception:
        # If decoding fails, return the original or a placeholder
        # This can happen with malformed headers
        return header_value

def _parse_addresses(address_str: Optional[str]) -> List[Tuple[Optional[str], str]]:
    if not address_str:
        return []
    # getaddresses expects a sequence of address strings.
    # If the header is already parsed by email.message.Message, it might be a list of tuples/strings.
    # For safety, ensure we handle a raw string header.
    parsed_addrs = getaddresses([address_str]) # Pass as a list to handle single string
    return [(name if name else None, addr) for name, addr in parsed_addrs if addr]


def parse_raw_email(raw_email_bytes: bytes) -> Optional[ParsedEmailData]:
    if not raw_email_bytes:
        return None

    try:
        msg = BytesParser().parsebytes(raw_email_bytes)
    except Exception as e:
        print(f"Error parsing email bytes: {e}")
        return None

    all_headers = {k.lower(): v for k, v in msg.items()}

    subject = _decode_header_value(msg.get('Subject'))

    from_header_value = msg.get('From')
    from_parsed = _parse_addresses(from_header_value)
    sender_name, sender_address = from_parsed[0] if from_parsed else (None, "unknown@example.com")

    to_header_value = msg.get('To')
    recipients_to = _parse_addresses(to_header_value)

    cc_header_value = msg.get('Cc')
    recipients_cc = _parse_addresses(cc_header_value)

    bcc_header_value = msg.get('Bcc') # Usually not present in received mail
    recipients_bcc = _parse_addresses(bcc_header_value)

    date_str = msg.get('Date')
    sent_at = None
    if date_str:
        try:
            sent_at = parsedate_to_datetime(date_str)
        except Exception: # Handle parsing errors for non-standard date formats
            sent_at = None # Or try other parsing methods

    message_id_header = msg.get('Message-ID')
    in_reply_to_header = msg.get('In-Reply-To')
    references_header = msg.get('References') # This can be a list of Message-IDs

    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[ParsedAttachment] = []

    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition")
        charset = part.get_content_charset() or 'utf-8' # Default to utf-8

        if content_disposition == "attachment" or (part.get_filename() and content_disposition != "inline"):
            filename = part.get_filename()
            if filename: # Decode filename if necessary
                filename = _decode_header_value(filename)

            payload_bytes_full = part.get_payload(decode=True)
            payload_to_store = None
            MAX_ATTACHMENT_SIZE_DB = 1 * 1024 * 1024 # 1MB limit for DB storage
            if len(payload_bytes_full) <= MAX_ATTACHMENT_SIZE_DB:
                payload_to_store = payload_bytes_full
            # Else: payload_to_store remains None, indicating it's too large for DB.
            # A storage_path would be set by Celery task if saving to disk/S3.

            attachments.append({
                "filename": filename,
                "content_type": content_type,
                "content_id": part.get("Content-ID"),
                "size_bytes": len(payload_bytes_full),
                "payload": payload_to_store
            })
        elif content_type == "text/plain" and body_text is None and content_disposition != "attachment":
            try:
                payload_bytes = part.get_payload(decode=True)
                body_text = payload_bytes.decode(charset, errors='replace')
            except Exception as e:
                print(f"Error decoding text/plain part: {e}")
                body_text = "Error decoding content."
        elif content_type == "text/html" and body_html is None and content_disposition != "attachment":
            try:
                payload_bytes = part.get_payload(decode=True)
                body_html = payload_bytes.decode(charset, errors='replace')
            except Exception as e:
                print(f"Error decoding text/html part: {e}")
                body_html = "Error decoding content."
        elif content_disposition == "inline" and part.get_filename(): # Inline images treated as attachments too
            filename = part.get_filename()
            if filename:
                filename = _decode_header_value(filename)
            payload_bytes_full = part.get_payload(decode=True)
            payload_to_store = None
            MAX_ATTACHMENT_SIZE_DB = 1 * 1024 * 1024 # 1MB limit for DB storage (consistent)
            if len(payload_bytes_full) <= MAX_ATTACHMENT_SIZE_DB:
                payload_to_store = payload_bytes_full

            attachments.append({
                "filename": filename,
                "content_type": content_type,
                "content_id": part.get("Content-ID"),
                "size_bytes": len(payload_bytes_full),
                "payload": payload_to_store
            })

    # If only HTML is found, try to convert a snippet to text (optional, basic)
    if body_html and not body_text:
        try:
            # Basic conversion: remove tags for a plain text version.
            # More sophisticated conversion might use libraries like html2text.
            plain_text_from_html = re.sub('<[^<]+?>', '', body_html)
            body_text = plain_text_from_html[:1000] # Limit length for snippet
        except Exception:
            pass # Ignore if conversion fails



    body_text_snippet = (body_text[:500] + '...') if body_text and len(body_text) > 500 else body_text

    return {
        "message_id_header": message_id_header,
        "subject": subject,
        "sender_name": sender_name,
        "sender_address": sender_address,
        "recipients_to": recipients_to,
        "recipients_cc": recipients_cc,
        "recipients_bcc": recipients_bcc,
        "sent_at": sent_at,
        "body_text": body_text,
        "body_html": body_html,
        "body_text_snippet": body_text_snippet, # Add snippet to returned dict
        "headers": dict(all_headers), # Convert email.message.Message items view to dict
        "in_reply_to_header": in_reply_to_header,
        "references_header": references_header,
        "attachments": attachments,
    }

# Example usage (for testing this parser)
if __name__ == '__main__':
    # A very basic raw email string (replace with actual raw email bytes)
    sample_raw_email_bytes = b"""Date: Mon, 1 Jul 2024 10:00:00 +0000
From: Sender <sender@example.com>
To: Recipient <recipient@example.com>
Subject: Test Email Subject with attachment
Message-ID: <test12345@example.com>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============1234567890=="

--===============1234567890==
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit

This is the plain text body of the email.
Hello World!

--===============1234567890==
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: 7bit

<html><body><p>This is the <b>HTML</b> body of the email.</p><p>Hello World!</p></body></html>
--===============1234567890==
Content-Type: application/octet-stream; name="test_attachment.txt"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="test_attachment.txt"

SGVsbG8gd29ybGQhIFRoaXMgaXMgYSB0ZXN0IGF0dGFjaG1lbnQuCg==
--===============1234567890==--
"""
    parsed_email = parse_raw_email(sample_raw_email_bytes)
    if parsed_email:
        print(f"Subject: {parsed_email['subject']}")
        print(f"From: {parsed_email['sender_name']} <{parsed_email['sender_address']}>")
        print(f"To: {parsed_email['recipients_to']}")
        print(f"Date: {parsed_email['sent_at']}")
        print(f"Message-ID: {parsed_email['message_id_header']}")
        print(f"Text Body: {parsed_email['body_text'][:50]}...")
        print(f"HTML Body: {parsed_email['body_html'][:50]}...")
        print(f"Attachments: {len(parsed_email['attachments'])}")
        if parsed_email['attachments']:
            print(f" - Filename: {parsed_email['attachments'][0]['filename']}")
            print(f" - Content-Type: {parsed_email['attachments'][0]['content_type']}")
            print(f" - Size: {parsed_email['attachments'][0]['size_bytes']} bytes")
            # print(f" - Payload: {parsed_email['attachments'][0]['payload']}")
    else:
        print("Failed to parse email.")
