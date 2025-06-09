import asyncio
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request # Added Request
from sqlalchemy.orm import Session

from app import models as db_models
from app.core.limiter import limiter # Import limiter
from app import schemas # Pydantic schemas
from app.database import get_db
from app.security import get_current_user
from app.crud import email_content as crud_email_content
from app.services.cerebras_ai_service import CerebrasAIService
from app.core.constants import JSON_SCHEMA_FOR_REPLY_SUGGESTIONS, EMAIL_CATEGORY_NAMES, CATEGORY_LIST_STR_FOR_PROMPT
from app.core.config import CEREBRAS_API_KEY # To check if AI is configured

router = APIRouter(prefix="/ai", tags=["AI Actions"])

# Helper to format message for prompt
def format_message_for_prompt(message: db_models.EmailMessage, max_body_len: int = 500) -> str:
    body_snippet = (message.body_text or "")[:max_body_len]
    if len(message.body_text or "") > max_body_len:
        body_snippet += "..."
    return f"Sender: {message.sender_address}\nSubject: {message.subject}\nBody Snippet: {body_snippet}\n"


@router.post("/suggest-reply/{message_id}", response_model=Dict[str, List[str]])
@limiter.limit("30/minute") # Apply rate limit: 30 requests per minute
async def suggest_reply_for_message(
    request: Request, # Added request
    message_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    if not CEREBRAS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI features are not configured on the server.",
        )

    target_message = crud_email_content.get_message_by_id(db, message_id=message_id, user_id=current_user.id)
    if not target_message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target message not found or access denied.")
    if not target_message.sent_at: # Ensure sent_at is available for ordering historical context
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target message is missing date information.")

    # Fetch historical context (last 2 messages in the same thread, older than current)
    historical_messages_prompt = "Historical Context (last 1-2 emails, if any):\n"
    if target_message.thread_id:
        previous_messages = crud_email_content.get_previous_messages_in_thread(
            db,
            thread_id=target_message.thread_id,
            current_message_sent_at=target_message.sent_at,
            user_id=current_user.id,
            limit=2
        )
        if previous_messages:
            # Reverse to have oldest first in context
            for msg in reversed(previous_messages):
                historical_messages_prompt += format_message_for_prompt(msg, max_body_len=200) + "\n" # Shorter snippets for history
        else:
            historical_messages_prompt += "No prior messages in this thread available for context.\n"
    else:
        historical_messages_prompt += "Message is not part of a thread or no thread ID available.\n"

    current_email_prompt = f"\nCurrent Email to Reply To:\n{format_message_for_prompt(target_message, max_body_len=1000)}"

    # System Prompt
    system_prompt = (
        "You are a helpful assistant that suggests concise email replies. "
        "Given the current email and optionally some historical context from the conversation, "
        "provide 2-3 brief, distinct reply suggestions. Each suggestion should be suitable for a quick reply. "
        "Focus on being helpful and relevant to the last message. "
        "Return the suggestions as a JSON object with a single key \"suggestions\", where the value is a list of strings. "
        "Example: {\"suggestions\": [\"Sounds good!\", \"I'll look into this.\", \"Can you provide more details?\"]}"
    )

    full_user_prompt = f"{historical_messages_prompt}{current_email_prompt}\n\nGenerate reply suggestions."

    messages_for_ai = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_user_prompt}
    ]

    response_format_options = {
        "type": "json_schema",
        "json_schema": {
            "name": "email_reply_suggestions_schema",
            "strict": True,
            "schema": JSON_SCHEMA_FOR_REPLY_SUGGESTIONS
        }
    }

    cerebras_service = CerebrasAIService() # Instantiates with key from env
    if not cerebras_service.is_active:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service is not available.")

    try:
        ai_response_data = await cerebras_service.get_chat_completion(
            messages=messages_for_ai,
            model="llama3.1-8b", # Or another suitable model
            response_format=response_format_options,
            temperature=0.6, # Adjust for desired creativity/determinism
            max_tokens=150 # Max tokens for the suggestions array
        )

        if ai_response_data and ai_response_data.get("choices"):
            choice = ai_response_data["choices"][0]
            if choice.get("message") and choice["message"].get("content"):
                content_str = choice["message"]["content"]
                try:
                    content_json = json.loads(content_str)
                    suggestions = content_json.get("suggestions")
                    if isinstance(suggestions, list) and all(isinstance(s, str) for s in suggestions):
                        return {"suggestions": suggestions}
                    else:
                        print(f"AI returned suggestions in unexpected format: {suggestions}")
                        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI returned suggestions in an unexpected format.")
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON response from AI for suggestions: {content_str}")
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to parse AI response for suggestions.")
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI response did not contain expected message content.")
        else:
            # This case includes if get_chat_completion returned None due to internal errors
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to get valid response from AI service.")

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        print(f"Error calling Cerebras AI for reply suggestions: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating AI reply suggestions: {e}")
    finally:
        await cerebras_service.close_client() # Ensure client is closed

# Note: Could add another endpoint for AI-assisted categorization if desired,
# similar to how it's done in Celery task but triggered via API.
# POST /categorize-email/{message_id} -> returns {"category": "CATEGORY_NAME"}
# This would use categorize_email_with_ai service method.
