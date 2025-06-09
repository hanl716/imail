import re
from typing import Optional
from app.core.constants import EmailCategory, DEFAULT_CATEGORY

# Pre-compile regexes for efficiency if they are complex
# For simple string checks, lowercasing is often enough.

# Keywords for different categories (examples, can be expanded significantly)
PROMOTION_KEYWORDS_BODY = ['unsubscribe', 'view this email in your browser', 'no-reply@', 'newsletter@']
PROMOTION_KEYWORDS_SUBJECT_SENDER = ['promotion', 'deal', 'offer', 'discount', 'sale']

UPDATES_KEYWORDS_SUBJECT_SENDER = [
    'invoice', 'bill', 'statement', 'order confirmation', 'shipping update',
    'your order', 'receipt', 'payment reminder', 'account activity', 'security alert'
]

SOCIAL_KEYWORDS_SENDER = [
    'facebookmail.com', 'twitter.com', 'linkedin.com', 'instagram.com',
    'pinterest.com', 'youtube.com', 'nextdoor.com'
]
SOCIAL_KEYWORDS_SUBJECT = [
    'mentioned you', 'tagged you', 'commented on your post', 'new connection request',
    'event reminder'
]


FORUMS_KEYWORDS_SENDER = ['googlegroups.com', 'discoursemail.com'] # Example forum domains
FORUMS_KEYWORDS_SUBJECT = ['digest', 'discussion update', 'new post in']


SPAM_KEYWORDS_SUBJECT_BODY = [
    'free money', '!!!', '$$$', 'winner', 'congratulations you have won',
    'claim your prize', 'urgent action required', 'limited time offer', 'click here now',
    'viagra', 'cialis', 'pharmacy' # Common spam terms
]


def categorize_email(sender: str, subject: str, body_snippet: Optional[str]) -> str:
    """
    Categorizes an email based on simple rules.
    Returns a category key (string name of EmailCategory enum member).
    """
    sender_lower = sender.lower() if sender else ""
    subject_lower = subject.lower() if subject else ""
    body_snippet_lower = body_snippet.lower() if body_snippet else ""

    # Rule order matters. More specific or aggressive rules (like SPAM) can go first.

    # SPAM Check (aggressive early check)
    for keyword in SPAM_KEYWORDS_SUBJECT_BODY:
        if keyword in subject_lower or keyword in body_snippet_lower:
            return EmailCategory.SPAM.name

    # SOCIAL
    for domain in SOCIAL_KEYWORDS_SENDER:
        if domain in sender_lower:
            return EmailCategory.SOCIAL.name
    for phrase in SOCIAL_KEYWORDS_SUBJECT:
        if phrase in subject_lower:
            return EmailCategory.SOCIAL.name

    # PROMOTIONS (check body for unsubscribe, then subject/sender)
    for keyword in PROMOTION_KEYWORDS_BODY:
        if keyword in body_snippet_lower:
            return EmailCategory.PROMOTIONS.name
    for keyword in PROMOTION_KEYWORDS_SUBJECT_SENDER:
        if keyword in subject_lower or keyword in sender_lower: # Check sender for e.g. "deals@..."
            return EmailCategory.PROMOTIONS.name

    # UPDATES
    for keyword in UPDATES_KEYWORDS_SUBJECT_SENDER:
        if keyword in subject_lower or keyword in sender_lower:
            return EmailCategory.UPDATES.name

    # FORUMS
    for domain in FORUMS_KEYWORDS_SENDER:
        if domain in sender_lower:
            return EmailCategory.FORUMS.name
    for phrase in FORUMS_KEYWORDS_SUBJECT:
        if phrase in subject_lower:
            return EmailCategory.FORUMS.name

    # If no specific category matched, use the default.
    # Could also have an "OTHER" category if INBOX is meant for primary, direct emails.
    # For now, defaulting to INBOX as a general bucket.
    return DEFAULT_CATEGORY
