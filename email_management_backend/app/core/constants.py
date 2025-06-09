from enum import Enum

class EmailCategory(Enum):
    INBOX = "Inbox"
    UPDATES = "Updates"
    PROMOTIONS = "Promotions"
    SOCIAL = "Social"
    FORUMS = "Forums"
    SPAM = "Spam"
    OTHER = "Other" # Default if no other category fits

# For direct use if Enum is not preferred in some places
EMAIL_CATEGORIES_DICT = {category.name: category.value for category in EmailCategory}

# Default category if none explicitly matched
DEFAULT_CATEGORY = EmailCategory.INBOX.name
