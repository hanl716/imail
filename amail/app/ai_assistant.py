import re
import string

class AIAssistant:
    def __init__(self):
        # Simple list of stopwords, can be expanded or replaced with NLTK's list
        self.stopwords = set([
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
            "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers",
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

    def preprocess_text(self, text):
        """
        Preprocesses text: lowercase, remove punctuation, tokenize, remove stopwords.
        Returns a list of processed tokens.
        """
        if not text:
            return []
        # Lowercase
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Tokenize (split into words)
        tokens = text.split()
        # Remove stopwords
        processed_tokens = [token for token in tokens if token not in self.stopwords]
        return processed_tokens

    def categorize_email(self, email_data):
        """
        Categorizes an email based on its content using simple rules.
        email_data is a dictionary like {'subject': '...', 'body': '...', ...}
        Returns a category string.
        """
        subject = email_data.get('subject', '')
        # Use 'snippet' as it's already extracted and shorter than full 'body'
        body_snippet = email_data.get('snippet', email_data.get('body', ''))

        combined_text = subject + " " + body_snippet

        if not combined_text.strip(): # If no text content
            return "General"

        processed_tokens = self.preprocess_text(combined_text)

        # For rule-based, we can check tokens or the raw lowercase text
        # Using raw lowercase text for simplicity with keywords that might be multi-word
        # or to avoid issues if a keyword itself is a stopword (though unlikely for good keywords)

        text_for_rules = (subject.lower() + " " + body_snippet.lower())

        # Refined Rule-Based Categorization
        # Order matters: more specific rules should come first if there's overlap potential.
        if any(keyword in text_for_rules for keyword in ["complain", "complaint", "unhappy", "disappointed", "poor service", "problem with", "issue with"]):
            return "Complaint"
        if any(keyword in text_for_rules for keyword in ["suggest", "suggestion", "recommend", "idea", "improve", "feature request", "feedback"]):
            return "Suggestion"
        if any(keyword in text_for_rules for keyword in ["invoice", "statement", "payment", "bill"]):
            return "Finance"
        if any(keyword in text_for_rules for keyword in ["meeting", "schedule", "appointment", "calendar", "zoom", "invite"]):
            return "Work/Calendar"
        # "issue" was part of Support, but also Complaint. Complaint is more specific.
        # If not a complaint, then it might be a general support request.
        if any(keyword in text_for_rules for keyword in ["help", "support", "ticket", "query", "assistance", "issue", "problem"]): # "issue", "problem" can be here if not a complaint
            return "Support"
        if any(keyword in text_for_rules for keyword in ["unsubscribe", "promotion", "offer", "discount", "sale"]):
            return "Promotions"

        return "General"

    def extract_complaint_suggestion_info(self, email_data):
        """
        Extracts basic information from an email categorized as Complaint or Suggestion.
        """
        # Ensure datetime_obj is used if available, otherwise fall back to raw date string
        date_to_log = email_data.get('datetime_obj')
        if date_to_log and hasattr(date_to_log, 'isoformat'): # Check if it's a datetime object
            date_to_log = date_to_log.isoformat()
        else: # Fallback to the original date string from email
            date_to_log = email_data.get('date', '')

        return {
            "type": email_data.get('category', 'Unknown'), # Should be "Complaint" or "Suggestion"
            "sender": email_data.get('from_email', 'Unknown Sender'),
            "subject": email_data.get('subject', 'No Subject'),
            "date": date_to_log,
            "summary": email_data.get('snippet', email_data.get('body', ''))[:200], # Increased summary length
            "source_account": email_data.get('account_name', 'Unknown Account')
        }

    # --- Placeholder for Advanced Information Extraction ---
    # def extract_detailed_info_ner(self, text):
    #     """
    #     (Future) Uses NER or other NLP techniques to extract more detailed information.
    #     For example: product names, specific issues, sentiment analysis score, etc.
    #     """
    #     # 1. Pre-trained NER models (e.g., spaCy, NLTK, Hugging Face Transformers)
    #     #    to identify entities like PRODUCT, ORGANIZATION, LOCATION, PERSON.
    #     # 2. Custom NER model fine-tuned on domain-specific data.
    #     # 3. Topic modeling (e.g., LDA, NMF) to identify key themes.
    #     # 4. Sentiment analysis to quantify the tone (positive, negative, neutral).
    #     print("Advanced information extraction not yet implemented.")
    #     return {"entities": [], "sentiment": "neutral", "topics": []}
    # --- End Placeholder ---

    def generate_reply_suggestions(self, email_data):
        """
        Generates simple reply suggestions based on email category and content.
        email_data is a dictionary like {'subject': '...', 'snippet': '...', 'category': '...'}
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


    # --- Placeholder for Future Model Training ---
    # def train_classifier(self, X_train_texts, y_train_labels):
    #     """
    #     Trains a text classifier.
    #     X_train_texts: list of email texts (e.g., subject + body)
    #     y_train_labels: list of corresponding categories
    #     """
    #     from sklearn.feature_extraction.text import TfidfVectorizer
    #     from sklearn.naive_bayes import MultinomialNB
    #     from sklearn.pipeline import make_pipeline
    #
    #     # Create a pipeline: TF-IDF Vectorizer -> Naive Bayes Classifier
    #     self.model = make_pipeline(
    #         TfidfVectorizer(preprocessor=self.preprocess_text_for_tfidf), # Custom preprocessor or default
    #         MultinomialNB()
    #     )
    #
    #     # Train the model
    #     self.model.fit(X_train_texts, y_train_labels)
    #     print("Classifier trained.")

    # def preprocess_text_for_tfidf(self, text):
    #     # For TF-IDF, we usually want to return a string of space-separated tokens
    #     return " ".join(self.preprocess_text(text))

    # def predict_category_with_model(self, email_text):
    #     """
    #     Predicts category using the trained scikit-learn model.
    #     """
    #     if hasattr(self, 'model') and self.model:
    #         preprocessed_text_for_model = self.preprocess_text_for_tfidf(email_text)
    #         return self.model.predict([preprocessed_text_for_model])[0]
    #     else:
    #         # Fallback to rule-based if model not trained/loaded
    #         # This part would need to be adjusted based on how email_text is structured here
    #         # For now, this method assumes it's called by a wrapper that handles data structure
    #         print("Model not available, falling back to rules (if implemented in this path).")
    #         # This is just an example; the actual call to rule-based would need email_data
    #         # return self.categorize_email_rule_based_from_text(email_text) # Hypothetical
    #         return "Error: Model not trained"
    # --- End Placeholder ---

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
