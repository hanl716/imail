from .email_connector import (
    connect_imap,
    disconnect_imap,
    list_mailboxes,
    fetch_emails_in_mailbox,
    connect_smtp,
    disconnect_smtp,
    send_email,
    EmailConnectionError,
    EmailLoginError,
    MailboxSelectError,
    EmailFetchError,
    EmailSendError
)

__all__ = [
    "connect_imap",
    "disconnect_imap",
    "list_mailboxes",
    "fetch_emails_in_mailbox",
    "connect_smtp",
    "disconnect_smtp",
    "send_email",
    "EmailConnectionError",
    "EmailLoginError",
    "MailboxSelectError",
    "EmailFetchError",
    "EmailSendError"
]
