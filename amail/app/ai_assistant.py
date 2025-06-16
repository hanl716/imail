"""
Provides AI-powered assistance for email processing.

This module includes the AIAssistant class, which offers functionalities like
email categorization, reply suggestion generation, and extraction of information
from specific email types (e.g., complaints, suggestions).
It is designed to be extensible with more advanced AI models, including
integration with external services like Cerebras.ai (currently mocked).
"""
import re
import string
from flask import current_app # For logging, especially when using CerebrasService

# Attempt to import CerebrasService for optional advanced AI features.
# If not found, Cerebras-dependent functionalities will be gracefully disabled.
try:
    from .cerebras_service import CerebrasService
except ImportError:
    CerebrasService = None # Define CerebrasService as None if import fails
    # Log this information if running within a Flask app context.
    # Avoids print statements during module import in non-app scenarios (e.g., direct testing if not careful).
    if current_app:
        current_app.logger.info("AIAssistant: CerebrasService module not found. Cerebras-specific features will be disabled.")
    # else: # For direct script execution, a print might be acceptable if needed for debugging.
        # print("INFO: AIAssistant: CerebrasService module not found. Cerebras-specific features will be disabled.")


class AIAssistant:
    """
    AI Assistant for email processing tasks.

    Provides methods for text preprocessing, email categorization (rule-based with
    placeholders for advanced model integration), information extraction from
    emails, and generating reply suggestions.
    """
    def __init__(self, cerebras_service_instance=None):
        """
        Initializes the AIAssistant.

        Args:
            cerebras_service_instance (CerebrasService, optional):
                An instance of CerebrasService for leveraging advanced AI models.
                If None, Cerebras-dependent features will be disabled. Defaults to None.
        """
        # Simple list of common English stopwords.
        # For more comprehensive stopword removal, consider using libraries like NLTK or spaCy.
        self.cerebras_service = cerebras_service_instance # Store the instance

        # Simple list of common English stopwords.
        # For more comprehensive stopword removal, consider using libraries like NLTK or spaCy.
        self.stopwords = set([
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", #NOSONAR
            "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", #NOSONAR
            "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
            "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
            "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
            "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
            "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
            "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "re",
            "ve", "ll", "m", "o", "subject", "body" # Added subject/body as they might appear from concatenation
        ])

    def preprocess_text(self, text_content):
        """
        Performs basic text preprocessing on the given text content.
        The steps include:
        1. Convert to lowercase.
        2. Remove punctuation.
        3. Tokenize (split into words).
        4. Remove common English stopwords (using the internal `self.stopwords` list).

        Args:
            text_content (str): The text string to preprocess.

        Returns:
            list: A list of processed (meaningful) tokens. Returns an empty list if input is empty.
        """
        if not text_content: # Handle empty input
            return []

        # 1. Convert to lowercase
        processed_text = text_content.lower()
        # 2. Remove punctuation (creates a translation table that maps each punctuation char to None)
        processed_text = processed_text.translate(str.maketrans('', '', string.punctuation))
        # 3. Tokenize (split into words by whitespace)
        tokens = processed_text.split()
        # 4. Remove stopwords
        # Note: This simple stopword list might need expansion or replacement for better results.
        meaningful_tokens = [token for token in tokens if token not in self.stopwords and token.strip()]

        return meaningful_tokens

    def categorize_email(self, email_data_dict):
        """
        Categorizes an email based on its content (subject and snippet) using a rule-based system.
        Includes a placeholder for future integration with Cerebras.ai for advanced categorization.

        Args:
            email_data_dict (dict): A dictionary containing email details, expected to have
                                 'subject' and 'snippet' (or 'body') keys.

        Returns:
            str: The determined category string (e.g., "Finance", "Complaint", "General").
        """
        subject = email_data_dict.get('subject', '')
        # Use 'snippet' for brevity, fallback to 'body' if snippet isn't available
        body_snippet = email_data_dict.get('snippet', email_data_dict.get('body', ''))

        # Combine subject and snippet for rule-based matching, convert to lowercase.
        # Preprocessing (tokenization, stopword removal) could be done here too for more advanced rules,
        # but for simple keyword matching, lowercase combined text is often sufficient.
        text_for_rules = (subject.lower() + " " + body_snippet.lower())

        if not text_for_rules.strip(): # If no textual content to analyze
            return "General" # Default category for empty emails

        # --- Placeholder for Cerebras.ai Advanced Categorization ---
        # If a CerebrasService instance is available, an attempt to use it for categorization
        # could be made here. The result could override or augment the rule-based approach.
        if hasattr(self, 'cerebras_service') and self.cerebras_service:
            # This is a conceptual example. The actual 'task_type' and 'data' structure
            # would depend on the specific Cerebras API for categorization.
            payload_for_cerebras = {"email_subject": subject, "email_body_snippet": body_snippet}

            # Log the intent to call Cerebras (actual call is mocked in CerebrasService for now)
            logger = current_app.logger if current_app else print
            logger.info(f"AIAssistant: Would call CerebrasService for advanced categorization. Data: {payload_for_cerebras}")

            # --- Example of how one might integrate the result (conceptual) ---
            # try:
            #     cerebras_response = self.cerebras_service.call_cerebras_api(
            #         task_type="advanced_email_categorization",
            #         data=payload_for_cerebras
            #     )
            #     if cerebras_response and cerebras_response.get('status') in ['success_mocked', 'success_actual']: # Check for success
            #         advanced_category = cerebras_response.get('result', {}).get('category_label')
            #         confidence = cerebras_response.get('result', {}).get('confidence_score', 0)
            #         if advanced_category and confidence > 0.7: # Example threshold
            #             logger.info(f"AIAssistant: Using category '{advanced_category}' from Cerebras.")
            #             # Potentially store more details from cerebras_response in email_data_dict
            #             email_data_dict['advanced_category_details'] = cerebras_response.get('result')
            #             return advanced_category # Return the category from Cerebras
            # except Exception as e:
            #     logger.error(f"AIAssistant: Error calling Cerebras for categorization: {e}")
            # --- End Conceptual Cerebras Integration Example ---
        # --- End Placeholder ---

        # Rule-Based Categorization (serves as fallback or primary method)
        # The order of these rules can be important if keywords overlap.
        # More specific categories (like Complaint) should generally precede broader ones (like Support).
        if any(keyword in text_for_rules for keyword in ["complain", "complaint", "unhappy", "disappointed", "poor service", "problem with", "issue with"]):
            return "Complaint"
        if any(keyword in text_for_rules for keyword in ["suggest", "suggestion", "recommend", "idea", "improve", "feature request", "feedback"]):
            return "Suggestion"
        if any(keyword in text_for_rules for keyword in ["invoice", "statement", "payment", "bill"]):
            return "Finance"
        if any(keyword in text_for_rules for keyword in ["meeting", "schedule", "appointment", "calendar", "zoom", "invite"]):
            return "Work/Calendar"
        if any(keyword in text_for_rules for keyword in ["help", "support", "ticket", "query", "assistance", "issue", "problem"]):
            return "Support"
        if any(keyword in text_for_rules for keyword in ["unsubscribe", "promotion", "offer", "discount", "sale"]):
            return "Promotions"

        return "General"


    def extract_complaint_suggestion_info(self, email_data_dict):
        """
        Extracts structured information from an email that has been categorized
        as a "Complaint" or "Suggestion".

        Args:
            email_data_dict (dict): The email data dictionary, which should include
                                 'category', 'from_email', 'subject', 'date' (or 'datetime_obj'),
                                 'snippet' (or 'body'), and 'account_name'.

        Returns:
            dict: A dictionary containing structured information:
                  {'type', 'sender', 'subject', 'date', 'summary', 'source_account'}.
        """
        # Use the parsed datetime_obj for logging if available and convert to ISO format string.
        # Otherwise, fall back to the original raw date string from the email header.
        date_value_to_log = email_data_dict.get('datetime_obj')
        if date_value_to_log and hasattr(date_value_to_log, 'isoformat'): # Check if it's a datetime object
            date_value_to_log = date_value_to_log.isoformat()
        else:
            date_value_to_log = email_data_dict.get('date', '') # Fallback to original date string

        extracted_info = {
            "type": email_data_dict.get('category', 'Unknown Type'), # Should be "Complaint" or "Suggestion"
            "sender": email_data_dict.get('from_email', 'Unknown Sender'),
            "subject": email_data_dict.get('subject', 'No Subject Provided'),
            "date": date_value_to_log,
            # Take a slightly longer summary for complaints/suggestions.
            "summary": email_data_dict.get('snippet', email_data_dict.get('body', ''))[:250],
            "source_account": email_data_dict.get('account_name', 'Unknown Account')
        }
        return extracted_info

    # --- Placeholder for Advanced Information Extraction (NER, Topic Modeling) ---
    # def extract_advanced_details(self, email_text_content):
    #     """
    #     (Future Enhancement)
    #     Uses more advanced NLP techniques like Named Entity Recognition (NER),
    #     topic modeling, or fine-tuned models to extract richer, structured details
    #     from email content (e.g., specific product names, issue types, sentiment scores).
    #     This could also leverage self.cerebras_service if available and applicable.
    #
    #     Args:
    #         email_text_content (str): The full text content of the email.
    #
    #     Returns:
    #         dict: A dictionary of extracted advanced details.
    #     """
    #     logger = current_app.logger if current_app else print
    #     logger.info("AIAssistant: Advanced detail extraction (NER, topic modeling) not yet implemented.")
    #     # Example: if self.cerebras_service:
    #     #     ner_results = self.cerebras_service.call_cerebras_api("ner", {"text": email_text_content})
    #     #     return {"entities": ner_results.get("entities", [])}
    #     return {"detected_entities": [], "main_topics": [], "sentiment_score": 0.0}
    # --- End Placeholder ---

    def generate_reply_suggestions(self, email_data_dict):
        """
        Generates a list of simple, rule-based reply suggestions based on the
        email's category and content (subject, snippet).

        Args:
            email_data_dict (dict): A dictionary containing email details, including
                                 'category', 'subject', and 'snippet'.

        Returns:
            list: A list of up to 3 suggested reply strings.
        """
        category = email_data_dict.get('category', 'General')
        subject_lower = email_data_dict.get('subject', '').lower()
        snippet_lower = email_data_dict.get('snippet', '').lower()
        # Combine subject and snippet for keyword checking in reply generation.
        text_content_for_replies = subject_lower + " " + snippet_lower
        Returns a list of suggestion strings.
        """
        category = email_data.get('category', 'General')
        subject_lower = email_data.get('subject', '').lower()
        snippet_lower = email_data.get('snippet', '').lower()
        text_content = subject_lower + " " + snippet_lower

        suggestions = []

        if category == "Work/Calendar":
            if "meeting" in text_content or "schedule" in text_content or "invite" in text_content:
                suggestions.extend([
                    "Sounds good, I'll be there.",
                    "Can you send a calendar invite?",
                    "I'm unable to make it at that time, can we reschedule?"
                ])
            if "question" in text_content:
                 suggestions.extend(["Let me check on that and get back to you."])
        elif category == "Finance":
            if "invoice" in text_content or "statement" in text_content:
                suggestions.extend([
                    "Thanks, I've received this.",
                    "Payment has been processed."
                ])
            if "bill" in text_content:
                suggestions.extend(["Thanks for the reminder."])
        elif category == "Support": # General support, not a complaint
            if "issue" in text_content or "problem" in text_content:
                suggestions.extend([
                    "Thanks for letting us know, we're looking into it.",
                    "Could you please provide more details on this issue?"
                ])
            elif "resolved" in text_content or "fixed" in text_content:
                 suggestions.extend(["Great to hear it's resolved! Thanks for confirming."])
            else: # General support query
                suggestions.extend(["How can I help you with this?", "Let me check on that for you."])
        elif category == "Complaint":
            suggestions.extend([
                "We are very sorry to hear about this. We will investigate immediately.",
                "Thank you for bringing this to our attention. Can you provide more specific details?",
                "Your feedback is important. We'll look into this and get back to you."
            ])
        elif category == "Suggestion":
            suggestions.extend([
                "Thank you for your suggestion! We'll consider it.",
                "That's a great idea, we appreciate your feedback.",
                "We'll pass this on to the relevant team."
            ])
        elif category == "Promotions":
            if "unsubscribe" in text_content:
                suggestions.extend(["Unsubscribe me please."]) # Though usually a link
            else:
                suggestions.extend(["No thank you."])


        # Generic suggestions if no specific rules matched or to augment existing ones
        if not suggestions or len(suggestions) < 2 : # Add some generics if not enough context-specific ones
            generic_suggestions = ["Thanks!", "Okay.", "Got it.", "Let me get back to you on this."]
            # Add generic ones that are not already present
            for gs in generic_suggestions:
                if gs not in suggestions and len(suggestions) < 3: # Limit total suggestions
                    suggestions.append(gs)

        if not suggestions: # Ensure always some suggestions
             suggestions = ["Thanks!", "Okay."]

        return suggestions[:3] # Return a maximum of 3 suggestions

    # --- Placeholder for Advanced Reply Generation ---
    # def generate_contextual_reply(self, email_text_sequence):
    #     """
    #     (Future) Generates more context-aware replies using NLP/NLG models.
    #     email_text_sequence: Could be the full email body or a sequence of turns in a conversation.
    #     """
    #     # This would involve:
    #     # 1. More sophisticated text preprocessing tailored for language models.
    #     # 2. Using a pre-trained language model (e.g., from Hugging Face Transformers).
    #     # 3. Fine-tuning the model on an email reply dataset (if available and feasible).
    #     # 4. Generating text using the model's generation capabilities (e.g., beam search).
    #     # 5. Post-processing the generated text for coherence, safety, and relevance.
    #     print("Advanced reply generation not yet implemented.")
    #     return ["(Advanced suggestion 1)", "(Advanced suggestion 2)"]
    # --- End Placeholder for Advanced Reply Generation ---


    # --- Placeholder for Future Model Training & Prediction (Scikit-learn based) ---
    # These methods illustrate where a more traditional ML model (e.g., Naive Bayes for text classification)
    # could be integrated. This would typically involve:
    # 1. Collecting and labeling a dataset of emails.
    # 2. Training a classifier (e.g., `train_sklearn_classifier` below).
    # 3. Saving the trained model (vectorizer and classifier).
    # 4. Loading the model in the AIAssistant for making predictions (`predict_category_with_sklearn_model`).

    # def train_sklearn_classifier(self, X_train_texts, y_train_labels, model_save_path="path_to_save_model.joblib"):
    #     """
    #     (Future Enhancement)
    #     Trains a text classifier.
    #     Trains a scikit-learn text classifier and saves it.
    #
    #     Args:
    #         X_train_texts (list): List of email text samples for training.
    #         y_train_labels (list): List of corresponding category labels.
    #         model_save_path (str, optional): Path to save the trained model.
    #     """
    #     from sklearn.feature_extraction.text import TfidfVectorizer
    #     from sklearn.naive_bayes import MultinomialNB
    #     from sklearn.pipeline import Pipeline
    #     # from joblib import dump # For saving the model
    #
    #     # Define a text processing function for TfidfVectorizer that uses our existing preprocess_text
    #     def_tfidf_preprocessor(text_content_str):
    #         return " ".join(self.preprocess_text(text_content_str)) # TF-IDF expects space-separated tokens
    #
    #     # Create a scikit-learn pipeline: TF-IDF Vectorizer -> Naive Bayes Classifier
    #     # This pipeline handles both feature extraction and classification.
    #     sklearn_text_classifier = Pipeline([
    #         ('tfidf', TfidfVectorizer(preprocessor=def_tfidf_preprocessor)),
    #         ('clf', MultinomialNB()), # Multinomial Naive Bayes is common for text
    #     ])
    #
    #     # Train the model
    #     sklearn_text_classifier.fit(X_train_texts, y_train_labels)
    #     logger = current_app.logger if current_app else print
    #     logger.info(f"Scikit-learn classifier trained. Saving to {model_save_path}")
    #
    #     # Save the trained pipeline (vectorizer + classifier)
    #     # dump(sklearn_text_classifier, model_save_path)
    #     # self.sklearn_model = sklearn_text_classifier # Optionally keep in memory
    #     # print(f"Model saved to {model_save_path}")


    # def load_sklearn_model(self, model_load_path="path_to_save_model.joblib"):
    #    """
    #    (Future Enhancement) Loads a pre-trained scikit-learn model.
    #    """
    #    from joblib import load
    #    try:
    #        self.sklearn_model = load(model_load_path)
    #        logger = current_app.logger if current_app else print
    #        logger.info(f"Scikit-learn model loaded successfully from {model_load_path}.")
    #    except FileNotFoundError:
    #        logger = current_app.logger if current_app else print
    #        logger.error(f"Scikit-learn model file not found at {model_load_path}.")
    #        self.sklearn_model = None # Ensure it's None if loading fails
    #    except Exception as e:
    #        logger = current_app.logger if current_app else print
    #        logger.error(f"Error loading scikit-learn model: {e}")
    #        self.sklearn_model = None


    # def predict_category_with_sklearn_model(self, email_text_content):
    #     """
    #     (Future Enhancement) Predicts email category using the loaded scikit-learn model.
    #     If the model is not loaded, it could fall back to rule-based categorization or raise an error.
    #
    #     Args:
    #         email_text_content (str): The combined text (e.g., subject + body) of the email.
    #
    #     Returns:
    #         str: The predicted category string, or None if prediction fails.
    #     """
    #     if hasattr(self, 'sklearn_model') and self.sklearn_model:
    #         # The TfidfVectorizer in the pipeline will use the custom preprocessor.
    #         # The input to `predict` should be a list or iterable of raw text strings.
    #         try:
    #             prediction = self.sklearn_model.predict([email_text_content])
    #             return prediction[0] # predict returns an array, get the first element
    #         except Exception as e:
    #             logger = current_app.logger if current_app else print
    #             logger.error(f"Error during scikit-learn model prediction: {e}")
    #             return None # Or a default category
    #     else:
    #         logger = current_app.logger if current_app else print
    #         logger.warning("Scikit-learn model not available for prediction. Falling back to rules or default.")
    #         # Fallback strategy could be to call the rule-based categorizer
    #         # return self.categorize_email_rule_based(email_text_content) # if such a method exists
    #         return None # Or a default "Uncategorized"
    # --- End Scikit-learn Placeholder ---


if __name__ == '__main__':
    # Example Usage (for testing this file directly)
    ai_assistant = AIAssistant()
    sample_email_1 = {
        "subject": "Your monthly bank statement is here",
        "snippet": "Dear customer, your latest invoice and statement are attached."
    }
    sample_email_2 = {
        "subject": "Meeting Reminder: Project Update",
        "snippet": "Hi team, just a reminder about our meeting scheduled for tomorrow to discuss project progress."
    }
    sample_email_3 = {
        "subject": "RE: Need help with my account",
        "snippet": "We received your support ticket regarding an issue with logging in."
    }
    sample_email_4 = {
        "subject": "Special Promotion just for you!",
        "snippet": "Don't miss out on our exclusive summer sale. Get 50% off on selected items. To unsubscribe, click here."
    }
    sample_email_5 = {
        "subject": "Hello from Grandma",
        "snippet": "Just checking in, hope you are doing well. Love, Grandma",
        "category": "General" # Manually add category for testing suggestions
    }
    sample_email_1['category'] = ai_assistant.categorize_email(sample_email_1)
    sample_email_2['category'] = ai_assistant.categorize_email(sample_email_2)
    sample_email_3['category'] = ai_assistant.categorize_email(sample_email_3) # Support
    sample_email_4['category'] = ai_assistant.categorize_email(sample_email_4) # Promotions

    sample_complaint = {
        "subject": "Very unhappy with recent purchase",
        "snippet": "I bought a product and it broke after one day. This is a complaint about poor service.",
        "from_email": "test@example.com", "date": "2024-01-15", "account_name": "test_account"
    }
    sample_complaint['category'] = ai_assistant.categorize_email(sample_complaint)

    sample_suggestion = {
        "subject": "Idea for new feature",
        "snippet": "I suggest you add a dark mode to the app. It would improve user experience.",
        "from_email": "user@example.com", "date": "2024-01-16", "account_name": "test_account"
    }
    sample_suggestion['category'] = ai_assistant.categorize_email(sample_suggestion)


    print(f"Email 1 ({sample_email_1['subject']}) Cat: {sample_email_1['category']} -> Suggestions: {ai_assistant.generate_reply_suggestions(sample_email_1)}")
    print(f"Email 2 ({sample_email_2['subject']}) Cat: {sample_email_2['category']} -> Suggestions: {ai_assistant.generate_reply_suggestions(sample_email_2)}")
    print(f"Email 3 ({sample_email_3['subject']}) Cat: {sample_email_3['category']} -> Suggestions: {ai_assistant.generate_reply_suggestions(sample_email_3)}")
    print(f"Email 4 ({sample_email_4['subject']}) Cat: {sample_email_4['category']} -> Suggestions: {ai_assistant.generate_reply_suggestions(sample_email_4)}")
    print(f"Email 5 ({sample_email_5['subject']}) Cat: {sample_email_5['category']} -> Suggestions: {ai_assistant.generate_reply_suggestions(sample_email_5)}")
    print(f"Complaint ({sample_complaint['subject']}) Cat: {sample_complaint['category']} -> Suggestions: {ai_assistant.generate_reply_suggestions(sample_complaint)}")
    print(f"Suggestion ({sample_suggestion['subject']}) Cat: {sample_suggestion['category']} -> Suggestions: {ai_assistant.generate_reply_suggestions(sample_suggestion)}")

    if sample_complaint['category'] in ["Complaint", "Suggestion"]:
        extracted_info = ai_assistant.extract_complaint_suggestion_info(sample_complaint)
        print(f"Extracted info from complaint: {extracted_info}")

    if sample_suggestion['category'] in ["Complaint", "Suggestion"]:
        extracted_info_sugg = ai_assistant.extract_complaint_suggestion_info(sample_suggestion)
        print(f"Extracted info from suggestion: {extracted_info_sugg}")

    processed = ai_assistant.preprocess_text("This is a Subject: with some Punctuation! and stopwords.")
    print(f"Processed tokens: {processed}")
