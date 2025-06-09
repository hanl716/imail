import datetime
import asyncio # Added for running async AI categorization
from app.core.celery_config import celery_app
from app.services.email_connector import connect_imap, disconnect_imap, fetch_emails_in_mailbox
import json # For parsing AI extraction response
import logging # For better logging
import datetime
import asyncio # Added for running async AI categorization
from app.core.celery_config import celery_app
from app.services.email_connector import connect_imap, disconnect_imap, fetch_emails_in_mailbox
from app.services.email_parser import parse_raw_email
from app.services.categorization_service import categorize_email_with_ai, rule_based_categorize_email
from app.services.cerebras_ai_service import CerebrasAIService
from app.utils.encryption import decrypt_data
from app.database import SessionLocal
from app.models.email_account import EmailAccount
from app.core.constants import DEFAULT_CATEGORY, EmailCategory, JSON_SCHEMA_FOR_COMPLAINT_EXTRACTION # Import new constants
from app.models.email_content import EmailMessage, EmailAttachment, EmailThread
from app.models.complaint_data import ComplaintData # Import new ComplaintData model
from app.core.config import FERNET_KEY
from sqlalchemy.orm.exc import NoResultFound
# Ensure logger is available if not configured globally for Celery
logger = logging.getLogger(__name__)
if not logger.handlers: # Basic config if no handlers present
    logging.basicConfig(level=logging.INFO)
from sqlalchemy import select

@celery_app.task(name="app.tasks.debug_task")
def debug_task(message: str):
    print(f"Celery task 'debug_task' received: {message}")
    return f"Debug task processed: {message}"

def get_or_create_thread(db: SessionLocal, parsed_data: dict, user_id: int, email_account_id: int, existing_message: EmailMessage = None) -> str:
    """
    Determines or creates a thread ID for a message.
    This is a simplified threading logic. A more robust one would involve deeper analysis
    of In-Reply-To and References headers, potentially building a graph.
    """
    # Try to find thread by In-Reply-To or References from existing messages
    # This part is complex and needs a good strategy.
    # For now, a basic approach:
    # 1. If existing_message and it has a thread_id, use it.
    # 2. If In-Reply-To matches an existing message's message_id_header, use its thread_id.
    # 3. If References contains a message_id_header of an existing message, use its thread_id.
    # 4. Otherwise, create a new thread using the current message's message_id_header as the thread_id,
    #    or use the subject if message_id is missing (though message_id should usually be present).

    if existing_message and existing_message.thread_id:
        return existing_message.thread_id

    # Check In-Reply-To
    if parsed_data.get('in_reply_to_header'):
        try:
            parent_msg = db.query(EmailMessage).filter(
                EmailMessage.message_id_header == parsed_data['in_reply_to_header'],
                EmailMessage.user_id == user_id # Ensure thread is scoped to user
            ).first()
            if parent_msg and parent_msg.thread_id:
                return parent_msg.thread_id
        except NoResultFound:
            pass

    # Check References (simplified: check first reference)
    if parsed_data.get('references_header'):
        references = parsed_data['references_header'].split()
        if references:
            try:
                ref_msg = db.query(EmailMessage).filter(
                    EmailMessage.message_id_header == references[0], # Check first reference
                    EmailMessage.user_id == user_id
                ).first()
                if ref_msg and ref_msg.thread_id:
                    return ref_msg.thread_id
            except NoResultFound:
                pass

    # If no existing thread found, create a new one
    # The new thread_id could be the current message's Message-ID or a new UUID.
    # Using Message-ID makes it somewhat content-addressable initially.
    new_thread_id = parsed_data.get('message_id_header') or f"thread_subject_{parsed_data.get('subject', 'untitled')}_{datetime.datetime.utcnow().timestamp()}"

    # Check if this thread_id already exists (e.g. if it's based on message_id of first email in a new thread)
    # Check if this thread_id already exists for this user AND account.
    # This ensures threads are scoped per account if desired, though Message-IDs are usually globally unique.
    # For simplicity, let's assume thread_id (based on Message-ID) is globally unique enough for user context.
    # The main addition here is associating the thread with an account if it's newly created.
    thread = db.query(EmailThread).filter_by(id=new_thread_id, user_id=user_id).first()
    if not thread:
        thread = EmailThread(
            id=new_thread_id,
            subject=parsed_data.get('subject', 'No Subject'), # Or try to get subject from first message of thread if more complex
            user_id=user_id,
            email_account_id=email_account_id # Associate with the account
        )
        db.add(thread)
        # db.commit() can be handled later in the main transaction block
    elif not thread.email_account_id : # If thread exists but somehow misses account_id (e.g. old data)
        thread.email_account_id = email_account_id # Update it
        # db.add(thread) # Mark for update
    return new_thread_id


@celery_app.task(name="app.tasks.fetch_emails_for_account_task", bind=True, max_retries=3, default_retry_delay=60)
def fetch_emails_for_account_task(self, account_id: int):
    if not FERNET_KEY:
        print(f"Skipping account {account_id}: Encryption key not available.")
        return f"Error: Encryption key not available for account {account_id}"

    db = SessionLocal()
    try:
        account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not account:
            print(f"Account {account_id} not found.")
            return f"Account {account_id} not found."
        if not account.is_active:
            print(f"Account {account.email_address} ({account_id}) is not active.")
            return f"Account {account.email_address} ({account_id}) is inactive."

        password = None
        if account.encrypted_password:
            try:
                password = decrypt_data(account.encrypted_password)
            except Exception as e:
                print(f"Failed to decrypt password for account {account.email_address} ({account_id}): {e}")
                return f"Credential decryption failed for {account.email_address} ({account_id})."

        if not password:
             print(f"No usable credentials for account {account.email_address} ({account_id}).")
             return f"No usable credentials for account {account.email_address} ({account_id})."

        print(f"Fetching emails for {account.email_address}...")
        imap_conn = None
        try:
            if not all([account.imap_server, account.imap_port, (account.email_user or account.email_address)]):
                print(f"Missing IMAP details for {account.email_address} ({account_id}).")
                return f"Missing IMAP details for {account.email_address} ({account_id})."

            imap_conn = connect_imap(
                host=account.imap_server, port=account.imap_port,
                email_user=(account.email_user or account.email_address), password=password
            )

            # Fetch a limited number of recent emails to avoid overwhelming the system
            raw_emails_data = fetch_emails_in_mailbox(imap_conn, mailbox="INBOX", count=10) # Fetch up to 10

            processed_count = 0
            for _, raw_email_bytes in raw_emails_data: # email_id_on_server is also available
                parsed_data = parse_raw_email(raw_email_bytes)
                if not parsed_data or not parsed_data.get('message_id_header'):
                    print("Failed to parse email or missing Message-ID header. Skipping.")
                    continue

                # Check for duplicates
                existing_message = db.query(EmailMessage).filter(
                    EmailMessage.message_id_header == parsed_data['message_id_header'],
                    EmailMessage.user_id == account.user_id # ensure user scope
                ).first()

                if existing_message and existing_message.is_fetched_complete: # is_fetched_complete to allow re-processing if partial
                    print(f"Message {parsed_data['message_id_header']} already exists and is complete. Skipping.")
                    continue

                thread_id = get_or_create_thread(db, parsed_data, account.user_id, account.id, existing_message) # Pass account.id

                # Fetch the thread to update its properties
                # This commit for thread creation might be early if outer commit fails,
                # but get_or_create_thread might have already added it.
                # Consider committing thread creation separately or as part of main commit.
                # For now, assume thread exists or was just created by get_or_create_thread.
                current_thread = db.query(EmailThread).filter(EmailThread.id == thread_id, EmailThread.user_id == account.user_id).first()
                if not current_thread: # Should not happen if get_or_create_thread works correctly
                    print(f"CRITICAL: Thread with ID {thread_id} not found after get_or_create. Skipping message processing.")
                    continue


                if existing_message: # Update existing message (e.g., if it was partially fetched)
                    print(f"Updating existing message {existing_message.message_id_header}")
                    db_message = existing_message
                else: # Create new message
                    print(f"Creating new message for {parsed_data['message_id_header']}")
                    db_message = EmailMessage(user_id=account.user_id, email_account_id=account.id)

                db_message.message_id_header = parsed_data['message_id_header']
                db_message.thread_id = thread_id
                db_message.subject = parsed_data.get('subject')
                db_message.sender_address = parsed_data.get('sender_address')
                # Store recipients as list of email strings for simplicity in JSON
                db_message.recipients_to = [addr for name, addr in parsed_data.get('recipients_to', [])]
                db_message.recipients_cc = [addr for name, addr in parsed_data.get('recipients_cc', [])]
                db_message.recipients_bcc = [addr for name, addr in parsed_data.get('recipients_bcc', [])]
                db_message.sent_at = parsed_data.get('sent_at')
                db_message.received_at = datetime.datetime.utcnow() # Override if re-processing
                db_message.body_text = parsed_data.get('body_text')
                db_message.body_html = parsed_data.get('body_html')
                db_message.headers = parsed_data.get('headers')
                db_message.in_reply_to_header = parsed_data.get('in_reply_to_header')
                db_message.references_header = parsed_data.get('references_header')
                db_message.is_read = False # Mark as unread by default
                db_message.is_fetched_complete = True # Mark as fully processed

                # AI Categorization
                category = DEFAULT_CATEGORY # Default category
                cerebras_service_instance = CerebrasAIService() # Instantiate here
                if cerebras_service_instance.is_active:
                    try:
                        snippet_for_ai = parsed_data.get('body_text_snippet', '') # Use the new snippet field
                        if not snippet_for_ai and parsed_data.get('body_text'): # Fallback if snippet missing
                             snippet_for_ai = (parsed_data.get('body_text')[:500] + '...') if len(parsed_data.get('body_text','')) > 500 else parsed_data.get('body_text','')

                        category = asyncio.run(categorize_email_with_ai(
                            sender=parsed_data.get('sender_address',''),
                            subject=parsed_data.get('subject',''),
                            body_snippet=snippet_for_ai,
                            cerebras_service=cerebras_service_instance
                        ))
                    except Exception as e_cat_ai:
                        print(f"AI categorization call failed for message {parsed_data['message_id_header']}: {e_cat_ai}")
                        # Fallback to rule-based if AI fails
                        category = rule_based_categorize_email(
                            sender=parsed_data.get('sender_address',''),
                            subject=parsed_data.get('subject',''),
                            body_snippet=snippet_for_ai
                        )
                    finally:
                        # Ensure client is closed if created per task run
                        asyncio.run(cerebras_service_instance.close_client())
                else:
                    print(f"Cerebras service not active for message {parsed_data['message_id_header']}, using rule-based categorization.")
                    snippet_for_rules = parsed_data.get('body_text_snippet', '')
                    if not snippet_for_rules and parsed_data.get('body_text'):
                        snippet_for_rules = (parsed_data.get('body_text')[:500] + '...') if len(parsed_data.get('body_text','')) > 500 else parsed_data.get('body_text','')
                    category = rule_based_categorize_email(
                        sender=parsed_data.get('sender_address',''),
                        subject=parsed_data.get('subject',''),
                        body_snippet=snippet_for_rules
                    )
                db_message.category = category

                if not existing_message:
                    db.add(db_message)

                # Update thread properties based on this new/updated message
                if current_thread:
                    current_thread.updated_at = datetime.datetime.utcnow() # Always update this
                    if db_message.sent_at and (not current_thread.last_message_at or db_message.sent_at > current_thread.last_message_at):
                        current_thread.last_message_at = db_message.sent_at
                        current_thread.snippet = (db_message.body_text or "")[:255] # Update snippet from latest message

                    # Update participants (simple list of unique sender addresses)
                    # A more complex system might store full name/email objects
                    if db_message.sender_address:
                        participants = set(current_thread.participants_json or [])
                        participants.add(db_message.sender_address)
                        current_thread.participants_json = list(participants)

                # Handle attachments - first remove old ones if updating message
                if existing_message:
                    # Efficiently delete existing attachments for this message
                    db.query(EmailAttachment).filter(EmailAttachment.email_message_id == existing_message.id).delete(synchronize_session=False)

                for attachment_data in parsed_data.get('attachments', []):
                    db_attachment = EmailAttachment(
                        # email_message_id will be set if db_message is persisted or by relationship backref
                        filename=attachment_data['filename'],
                        content_type=attachment_data['content_type'],
                        content_id=attachment_data['content_id'],
                        size_bytes=attachment_data['size_bytes'],
                        content_bytes=attachment_data.get('payload') # Save payload if available (parser rules apply)
                        # storage_path=... # If not storing in DB or for larger files
                    )
                    # Associate with the message. If message is new, this needs to happen after message is added or flushed.
                    # If using relationships, can append to db_message.attachments list.
                    db_message.attachments.append(db_attachment) # This relies on relationship configuration

                # After saving db_message and it has an ID, and if it's a complaint/suggestion:
                if category == EmailCategory.COMPLAINTS_SUGGESTIONS.name:
                    logger.info(f"Email {db_message.id} categorized as {category}. Attempting detail extraction.")
                    if cerebras_service_instance.is_active: # Assuming service is still available from categorization step
                        extraction_prompt_messages = [
                            {"role": "system", "content": "You are an assistant that processes customer feedback. Analyze the following email. If it is a complaint or suggestion, extract its details into the specified JSON format using the provided schema. If not, return an empty JSON object or a JSON object with an 'issue_type' of 'NotApplicable'."},
                            {"role": "user", "content": f"Email Content:\nSender: {parsed_data.get('sender_address','')}\nSubject: {parsed_data.get('subject','')}\nBody: {parsed_data.get('body_text_snippet','')}"} # Use full body if snippet too short body_text
                        ]
                        extraction_response_format = {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "complaint_extraction_schema",
                                "strict": True,
                                "schema": JSON_SCHEMA_FOR_COMPLAINT_EXTRACTION
                            }
                        }
                        try:
                            extraction_data_response = await cerebras_service_instance.get_chat_completion(
                                messages=extraction_prompt_messages,
                                model="llama3.1-8b", # Or specific model for extraction
                                response_format=extraction_response_format,
                                temperature=0.0 # Low temperature for factual extraction
                            )
                            if extraction_data_response and extraction_data_response.get("choices"):
                                choice = extraction_data_response["choices"][0]
                                if choice.get("message") and choice["message"].get("content"):
                                    content_str = choice["message"]["content"]
                                    try:
                                        extracted_json = json.loads(content_str)
                                        # Validate extracted_json and save to ComplaintData model
                                        if extracted_json.get("summary") and extracted_json.get("issue_type") != "NotApplicable":
                                            # Check if complaint data already exists for this message_id
                                            existing_complaint = db.query(ComplaintData).filter_by(email_message_id=db_message.id).first()
                                            if not existing_complaint:
                                                new_complaint = ComplaintData(
                                                    email_message_id=db_message.id,
                                                    user_id=db_message.user_id,
                                                    submitter_email=extracted_json.get("email_address", parsed_data.get('sender_address','')),
                                                    submitter_name=extracted_json.get("customer_name"),
                                                    issue_type=extracted_json.get("issue_type"),
                                                    category_detail=extracted_json.get("category_detail"),
                                                    product_service=extracted_json.get("product_service"),
                                                    summary=extracted_json.get("summary"),
                                                    sentiment=extracted_json.get("sentiment")
                                                )
                                                db.add(new_complaint)
                                                logger.info(f"Extracted and saved complaint/suggestion for email {db_message.id}")
                                            else:
                                                logger.info(f"Complaint/suggestion data already exists for email {db_message.id}. Skipping creation.")
                                        else:
                                            logger.info(f"AI did not extract a valid summary or marked as NotApplicable for email {db_message.id}. Response: {content_str}")
                                    except json.JSONDecodeError:
                                        logger.error(f"Failed to parse JSON from AI for complaint extraction: {content_str}")
                        except Exception as e_extract:
                            logger.error(f"Error during AI complaint/suggestion extraction for email {db_message.id}: {e_extract}")
                        # Note: cerebras_service_instance.close_client() is handled after all emails for an account are processed.

                processed_count += 1

            # Commit all changes for this account's fetch operation (including messages, threads, attachments, complaints)
            db.commit()
            print(f"Successfully processed and stored {processed_count} emails for account {account.email_address} ({account_id}).")

        except Exception as e:
            db.rollback() # Rollback on error during fetching or processing for this account
            print(f"Error processing emails for {account.email_address}: {e}")
            # self.retry(exc=e) # Example of retrying the task
            return f"Error for {account.email_address}: {e}"
        finally:
            if imap_conn:
                disconnect_imap(imap_conn)
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Major error in fetch_emails_for_account_task for account {account_id}: {e}")
        # self.retry(exc=e)
        return f"Major error processing account {account_id}: {e}"
    finally:
        if db:
            db.close()

    return f"Completed email fetch for account {account_id} ({account.email_address if account else 'N/A'})."

@celery_app.task(name="app.tasks.periodic_fetch_all_emails")
def periodic_fetch_all_emails():
    print("Periodic task: Fetching all emails for all active accounts...")
    db = SessionLocal()
    try:
        active_accounts = db.query(EmailAccount).filter(EmailAccount.is_active == True).all()
        if not active_accounts:
            print("No active accounts found.")
            return "No active accounts."
        for account in active_accounts:
            print(f"Queueing email fetch for account ID: {account.id} ({account.email_address})")
            fetch_emails_for_account_task.delay(account.id)
    finally:
        db.close()
    return f"Queued email fetching for {len(active_accounts) if active_accounts else 0} active accounts."
