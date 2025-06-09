import json
import logging
from typing import Optional

from app.core.constants import (
    EmailCategory,
    DEFAULT_CATEGORY,
    EMAIL_CATEGORY_NAMES,
    CATEGORY_LIST_STR_FOR_PROMPT,
    JSON_SCHEMA_FOR_CATEGORY_AI_RESPONSE
)
from app.services.cerebras_ai_service import CerebrasAIService

logger = logging.getLogger(__name__)

# Keep the old rule-based system as a fallback or alternative
# For simplicity in this step, we'll define a new async function for AI categorization
# and the Celery task will decide which one to call or how to manage fallbacks.

async def categorize_email_with_ai(
    sender: str,
    subject: str,
    body_snippet: str, # Expecting a non-optional snippet for AI
    cerebras_service: CerebrasAIService
) -> str:
    """
    Categorizes an email using Cerebras AI.
    Returns a category key (string name of EmailCategory enum member).
    """
    if not cerebras_service.is_active:
        logger.warning("Cerebras AI service not active. Cannot perform AI categorization.")
        # Optionally, call the old rule-based categorize_email here as a fallback
        # return rule_based_categorize_email(sender, subject, body_snippet)
        return DEFAULT_CATEGORY

    system_prompt = (
        f"You are an expert email categorization assistant. Analyze the provided email content "
        f"(sender, subject, body snippet) and classify it into one of the following categories: "
        f"{CATEGORY_LIST_STR_FOR_PROMPT}. Your response MUST be a JSON object strictly adhering to the "
        f"provided schema, with a single key \"category\" and the value being one of the allowed categories."
    )

    user_prompt_content = f"Sender: {sender}\nSubject: {subject}\nBody Snippet: {body_snippet}\n\nPlease categorize this email."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_content}
    ]

    # Use the schema defined in constants.py for response_format
    response_format_options = {
        "type": "json_schema",
        "json_schema": {
            "name": "email_category_schema", # Optional name
            "strict": True, # Enforce schema
            "schema": JSON_SCHEMA_FOR_CATEGORY_AI_RESPONSE # Use the schema from constants
        }
    }

    # Choose an appropriate model - smaller/faster one might be okay for classification
    model_for_classification = "llama3.1-8b" # Or another suitable model like BTLM-3B-8K-chat

    try:
        logger.info(f"Requesting AI categorization for email (Sub: {subject[:30]}...)")
        completion_data = await cerebras_service.get_chat_completion(
            messages=messages,
            model=model_for_classification,
            response_format=response_format_options,
            temperature=0.1, # Lower temperature for more deterministic classification
            max_tokens=50    # Category name and JSON structure is small
        )

        if completion_data and completion_data.get("choices"):
            choice = completion_data["choices"][0]
            if choice.get("message") and choice["message"].get("content"):
                content_str = choice["message"]["content"]
                try:
                    # The content should be a JSON string due to response_format
                    content_json = json.loads(content_str)
                    category_name = content_json.get("category")

                    if category_name in EMAIL_CATEGORY_NAMES:
                        logger.info(f"AI categorized email (Sub: {subject[:30]}) as: {category_name}")
                        return category_name
                    else:
                        logger.warning(f"AI returned an invalid or unexpected category: '{category_name}'. Raw response: {content_str}")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response from AI for categorization. Raw response: {content_str}")
            else:
                logger.warning(f"AI response choice did not contain expected message content. Response: {completion_data}")
        else:
            logger.warning(f"No valid choices found in AI response for categorization. Response: {completion_data}")

    except Exception as e:
        logger.error(f"An unexpected error occurred during AI categorization call: {e}", exc_info=True)

    logger.warning(f"AI categorization failed or returned invalid data for email (Sub: {subject[:30]}). Falling back to default category.")
    # Optionally, call rule-based fallback here
    # return rule_based_categorize_email(sender, subject, body_snippet)
    return DEFAULT_CATEGORY


# --- Keep the old rule-based system for fallback or direct use if AI is off ---
# (Copied from previous state of this file, can be pruned if not needed as fallback)
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
FORUMS_KEYWORDS_SENDER = ['googlegroups.com', 'discoursemail.com']
FORUMS_KEYWORDS_SUBJECT = ['digest', 'discussion update', 'new post in']
SPAM_KEYWORDS_SUBJECT_BODY = [
    'free money', '!!!', '$$$', 'winner', 'congratulations you have won',
    'claim your prize', 'urgent action required', 'limited time offer', 'click here now',
    'viagra', 'cialis', 'pharmacy'
]

def rule_based_categorize_email(sender: str, subject: str, body_snippet: Optional[str]) -> str:
    sender_lower = sender.lower() if sender else ""
    subject_lower = subject.lower() if subject else ""
    body_snippet_lower = body_snippet.lower() if body_snippet else ""

    for keyword in SPAM_KEYWORDS_SUBJECT_BODY:
        if keyword in subject_lower or keyword in body_snippet_lower:
            return EmailCategory.SPAM.name
    for domain in SOCIAL_KEYWORDS_SENDER:
        if domain in sender_lower: return EmailCategory.SOCIAL.name
    for phrase in SOCIAL_KEYWORDS_SUBJECT:
        if phrase in subject_lower: return EmailCategory.SOCIAL.name
    # For newsletters, specific keywords might be better than general 'promotion' ones
    if "newsletter" in subject_lower or "newsletter" in sender_lower or 'newsletter@' in sender_lower:
        return EmailCategory.NEWSLETTERS.name
    for keyword in PROMOTION_KEYWORDS_BODY: # Check body for unsubscribe links etc.
        if keyword in body_snippet_lower: return EmailCategory.PROMOTIONS.name
    for keyword in PROMOTION_KEYWORDS_SUBJECT_SENDER:
        if keyword in subject_lower or keyword in sender_lower: return EmailCategory.PROMOTIONS.name
    for keyword in UPDATES_KEYWORDS_SUBJECT_SENDER: # Includes finance, orders, etc.
        if keyword in subject_lower or keyword in sender_lower: return EmailCategory.UPDATES.name
    for domain in FORUMS_KEYWORDS_SENDER:
        if domain in sender_lower: return EmailCategory.FORUMS.name
    for phrase in FORUMS_KEYWORDS_SUBJECT:
        if phrase in subject_lower: return EmailCategory.FORUMS.name

    # More specific rules can be added here for WORK, FINANCE, TAXES, TRAVEL, PERSONAL etc.
    # Example for FINANCE (very basic)
    if any(kw in subject_lower for kw in ["bank statement", "payment confirmation", "financial update"]):
        return EmailCategory.FINANCE.name

    return DEFAULT_CATEGORY
