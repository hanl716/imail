from enum import Enum

class EmailCategory(Enum):
    INBOX = "Inbox"  # General, important, or fallback
    WORK = "Work"
    FINANCE = "Finance"  # For bank statements, invoices from financial institutions
    TAXES = "Taxes"
    TRAVEL = "Travel" # Flight, hotel, car rental confirmations
    SHOPPING_ORDERS = "Shopping/Orders" # Order confirmations, shipping updates from e-commerce
    NEWSLETTERS = "Newsletters" # Subscribed content, distinct from promotions
    PROMOTIONS = "Promotions" # Marketing, sales, unsolicited commercial emails
    SOCIAL = "Social Media" # Notifications from social media platforms
    FORUMS = "Forums/Groups" # Notifications from discussion groups, forums
    COMPLAINTS_SUGGESTIONS = "Complaints/Suggestions" # User-flagged or specific for this use case
    PERSONAL = "Personal" # Direct person-to-person communication
    SPAM = "Spam"
    OTHER = "Other"  # Fallback if no other category fits well

# Default category if none explicitly matched or AI fails
DEFAULT_CATEGORY = EmailCategory.INBOX.name # Or EmailCategory.OTHER.name depending on desired behavior

# For use in prompts and validation
EMAIL_CATEGORY_NAMES = [category.name for category in EmailCategory]
EMAIL_CATEGORY_VALUES = [category.value for category in EmailCategory] # Display names

# For generating a comma-separated list for prompts
CATEGORY_LIST_STR_FOR_PROMPT = ", ".join(EMAIL_CATEGORY_NAMES)

# JSON Schema for AI response validation
JSON_SCHEMA_FOR_CATEGORY_AI_RESPONSE = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": EMAIL_CATEGORY_NAMES
        },
        "confidence": { # Optional: AI could also return a confidence score
            "type": "number",
            "minimum": 0,
            "maximum": 1
        },
        "reasoning": { # Optional: AI could provide a brief reason for the category
            "type": "string"
        }
    },
    "required": ["category"]
}

JSON_SCHEMA_FOR_REPLY_SUGGESTIONS = {
    "type": "object",
    "properties": {
        "suggestions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 3 # Or as desired, e.g., 5 for more options
        }
    },
    "required": ["suggestions"]
}

JSON_SCHEMA_FOR_COMPLAINT_EXTRACTION = {
    "type": "object",
    "properties": {
        "email_address": {"type": "string", "description": "Submitter's email address, extracted from sender or body if explicitly mentioned."},
        "customer_name": {"type": "string", "description": "Submitter's name, if identifiable from sender or email body/signature."},
        "issue_type": {"type": "string", "enum": ["Complaint", "Suggestion", "Query", "Feedback", "NotApplicable"], "description": "The general type of the issue."},
        "category_detail": {"type": "string", "description": "A more specific category for the issue, e.g., 'Billing Error', 'Service Quality', 'Product Defect', 'New Feature Request', 'Website Bug'."},
        "product_service": {"type": "string", "description": "The specific product or service mentioned, if any (e.g., 'Subscription Plan X', 'Mobile App Login')."},
        "summary": {"type": "string", "description": "A concise summary of the core complaint, suggestion, or query."},
        "sentiment": {"type": "string", "enum": ["Positive", "Negative", "Neutral"], "description": "The overall sentiment of the email."}
    },
    "required": ["email_address", "issue_type", "summary", "sentiment"]
    # "product_service" and "category_detail" can be optional if not always present
}

# This could be used if Cerebras SDK has a more direct "tool use" feature like OpenAI's
# For now, we'll use the JSON_SCHEMA_FOR_COMPLAINT_EXTRACTION with response_format.
TOOL_SCHEMA_FOR_COMPLAINT_LOGGING = {
    "name": "log_complaint_or_suggestion",
    "description": "Logs the details of a customer complaint or suggestion based on email content.",
    "parameters": JSON_SCHEMA_FOR_COMPLAINT_EXTRACTION # Re-use the schema
}
