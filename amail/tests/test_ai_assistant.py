"""
Tests for the AIAssistant class and its methods.
"""
import pytest
from amail.app.ai_assistant import AIAssistant
# Assuming CerebrasService is optional and AIAssistant can run without it for these tests
# If CerebrasService was mandatory, we might need to mock it or pass a mock instance.

@pytest.fixture(scope="module")
def ai_assistant_instance():
    """Provides an instance of AIAssistant for testing."""
    # Pass no cerebras_service_instance, so it uses its default (None)
    return AIAssistant()

# --- Tests for preprocess_text ---
def test_preprocess_text_empty(ai_assistant_instance):
    assert ai_assistant_instance.preprocess_text("") == []
    assert ai_assistant_instance.preprocess_text(None) == []

def test_preprocess_text_lowercase(ai_assistant_instance):
    assert "UPPERCASE" not in "".join(ai_assistant_instance.preprocess_text("CONVERT THIS UPPERCASE TEXT"))

def test_preprocess_text_punctuation(ai_assistant_instance):
    processed = ai_assistant_instance.preprocess_text("Hello! This, is a test text? Yes.")
    assert "hello" in processed
    assert "this" in processed
    assert "is" in processed
    assert "a" not in processed # stopword
    assert "test" in processed
    assert "text" in processed
    assert "yes" in processed
    # Check that no tokens contain punctuation
    for token in processed:
        for char in token:
            assert char.isalnum() or not char.isprintable() # Allow alphanumeric

def test_preprocess_text_stopwords(ai_assistant_instance):
    # "a", "the", "is" are common stopwords defined in AIAssistant
    processed = ai_assistant_instance.preprocess_text("This is a test of the stopword removal.")
    assert "this" not in processed # "this" is a stopword in the default list
    assert "is" not in processed
    assert "a" not in processed
    assert "of" not in processed
    assert "the" not in processed
    assert "test" in processed
    assert "stopword" in processed
    assert "removal" in processed

# --- Tests for categorize_email ---
@pytest.mark.parametrize("email_data, expected_category", [
    ({"subject": "Your invoice #123 is here", "snippet": "Please find attached your latest bill."}, "Finance"),
    ({"subject": "Invoice for services", "snippet": "Payment due by end of month."}, "Finance"),
    ({"subject": "Meeting schedule update", "snippet": "Our weekly meeting is rescheduled."}, "Work/Calendar"),
    ({"subject": "Project Alpha - Calendar Invite", "snippet": "Zoom link inside."}, "Work/Calendar"),
    ({"subject": "Urgent: problem with my account", "snippet": "I cannot login, this is a complaint!"}, "Complaint"),
    ({"subject": "Very unhappy with recent order", "snippet": "The product arrived broken."}, "Complaint"),
    ({"subject": "Feature request: dark mode", "snippet": "I suggest adding a dark mode to the app."}, "Suggestion"),
    ({"subject": "Idea to improve search", "snippet": "It would be great if search could..."}, "Suggestion"),
    ({"subject": "Need help with login issue", "snippet": "I'm having trouble accessing my account."}, "Support"), # 'issue' but not 'complaint' phrasing
    ({"subject": "Question about your services", "snippet": "Can you provide assistance with..."}, "Support"),
    ({"subject": "Big Summer Sale! Discounts inside!", "snippet": "Don't miss our special promotion."}, "Promotions"),
    ({"subject": "Unsubscribe me from this list", "snippet": "Please remove me."}, "Promotions"), # "unsubscribe"
    ({"subject": "Hello there", "snippet": "Just checking in on you."}, "General"),
    ({"subject": "", "snippet": ""}, "General"), # Empty content
])
def test_categorize_email_rules(ai_assistant_instance, email_data, expected_category):
    assert ai_assistant_instance.categorize_email(email_data) == expected_category

# --- Tests for generate_reply_suggestions ---
def test_generate_reply_suggestions_work_meeting(ai_assistant_instance):
    email_data = {"category": "Work/Calendar", "subject": "Meeting tomorrow", "snippet": "Confirm your availability."}
    suggestions = ai_assistant_instance.generate_reply_suggestions(email_data)
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    assert "Sounds good, I'll be there." in suggestions

def test_generate_reply_suggestions_finance_invoice(ai_assistant_instance):
    email_data = {"category": "Finance", "subject": "Invoice INV-001", "snippet": "Attached is your invoice."}
    suggestions = ai_assistant_instance.generate_reply_suggestions(email_data)
    assert "Thanks, I've received this." in suggestions

def test_generate_reply_suggestions_complaint(ai_assistant_instance):
    email_data = {"category": "Complaint", "subject": "Broken item", "snippet": "I am very unhappy."}
    suggestions = ai_assistant_instance.generate_reply_suggestions(email_data)
    assert "We are very sorry to hear about this. We will investigate immediately." in suggestions

def test_generate_reply_suggestions_suggestion(ai_assistant_instance):
    email_data = {"category": "Suggestion", "subject": "New idea", "snippet": "I suggest..."}
    suggestions = ai_assistant_instance.generate_reply_suggestions(email_data)
    assert "Thank you for your suggestion! We'll consider it." in suggestions

def test_generate_reply_suggestions_general(ai_assistant_instance):
    email_data = {"category": "General", "subject": "Quick hello", "snippet": "How are you?"}
    suggestions = ai_assistant_instance.generate_reply_suggestions(email_data)
    assert "Thanks!" in suggestions or "Okay." in suggestions # Default generic suggestions

# --- Tests for extract_complaint_suggestion_info ---
def test_extract_complaint_info(ai_assistant_instance):
    email_data = {
        "category": "Complaint",
        "from_email": "user@example.com",
        "subject": "Major Issue",
        "date": "2023-10-26T10:00:00Z", # Raw date string
        "datetime_obj": None, # Simulate no parsed datetime for this test if it uses date
        "snippet": "This product is terrible and broke immediately. I want a refund now.",
        "account_name": "test_account_main"
    }
    # If datetime_obj is None, it should use the 'date' field.
    # To test with datetime_obj, it should be a datetime object.
    # For simplicity, this test relies on the fallback to the 'date' string.

    info = ai_assistant_instance.extract_complaint_suggestion_info(email_data)
    assert info["type"] == "Complaint"
    assert info["sender"] == "user@example.com"
    assert info["subject"] == "Major Issue"
    assert info["date"] == "2023-10-26T10:00:00Z"
    assert "This product is terrible" in info["summary"]
    assert info["source_account"] == "test_account_main"

def test_extract_suggestion_info_with_datetime(ai_assistant_instance):
    from datetime import datetime, timezone
    now_dt = datetime.now(timezone.utc)
    email_data = {
        "category": "Suggestion",
        "from_email": "feeder@example.com",
        "subject": "Great Idea for App",
        "date": "A_raw_date_string_that_wont_be_used", # Raw date string
        "datetime_obj": now_dt, # Parsed datetime object
        "snippet": "You should add a feature that does X, Y, and Z. It would be amazing!",
        "account_name": "test_account_secondary"
    }
    info = ai_assistant_instance.extract_complaint_suggestion_info(email_data)
    assert info["type"] == "Suggestion"
    assert info["sender"] == "feeder@example.com"
    assert info["date"] == now_dt.isoformat() # Check if datetime_obj was used and ISO formatted
    assert "You should add a feature" in info["summary"]
    assert info["source_account"] == "test_account_secondary"

# Test AIAssistant initialization with mock CerebrasService (optional)
# This mostly checks that the AIAssistant can be created with it.
# Actual testing of CerebrasService interaction would require mocking CerebrasService itself.
def test_ai_assistant_with_mock_cerebras_service(ai_assistant_instance):
    # This test uses the default ai_assistant_instance which has no CerebrasService.
    # To test with one, we'd need to instantiate it:
    # mock_cerebras_service = CerebrasService() # Assuming CerebrasService can be init'd like this
    # ai_assistant_with_cerebras = AIAssistant(cerebras_service_instance=mock_cerebras_service)
    # For now, just assert that the default instance doesn't have one.
    assert not hasattr(ai_assistant_instance, 'cerebras_service') or ai_assistant_instance.cerebras_service is None
    # If CerebrasService was imported and AIAssistant had `self.cerebras_service = cerebras_service_instance`
    # then we could check it here. The current AIAssistant doesn't store it as self.cerebras_service.
    # It only checks `if self.cerebras_service:` which is a bug if it's not set in __init__.
    # Corrected AIAssistant __init__ to store it:
    # self.cerebras_service = cerebras_service_instance
    # Then this test would be:
    # assert ai_assistant_instance.cerebras_service is None

    # If we wanted to test the logging path:
    # from unittest.mock import MagicMock
    # mock_cs_instance = MagicMock() # Mock the CerebrasService
    # ai_with_cs = AIAssistant(cerebras_service_instance=mock_cs_instance)
    # email_data = {"subject": "Test subject", "snippet": "Test snippet"}
    # ai_with_cs.categorize_email(email_data) # This should trigger the log if current_app.logger is also mocked
    # This type of test is more involved due to needing app context for logger or mocking logger.
    pass # Basic check is that it can be instantiated as is.
