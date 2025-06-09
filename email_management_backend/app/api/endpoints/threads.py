from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models # For current_user type hint
from app import schemas # For Pydantic models
from app.database import get_db
from app.security import get_current_user
from app.crud import email_content as crud_email_content # CRUD functions for email content

router = APIRouter()

@router.get("/", response_model=List[schemas.email_content.EmailThreadOutput])
def list_threads_for_user(
    account_id: Optional[int] = None, # New optional query parameter
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user),
):
    """
    List email threads for the authenticated user.
    Optionally filters by a specific email_account_id.
    """
    # Further validation: ensure the account_id (if provided) belongs to the current_user
    if account_id is not None:
        acc = db.query(db_models.EmailAccount).filter(
            db_models.EmailAccount.id == account_id,
            db_models.EmailAccount.user_id == current_user.id
        ).first()
        if not acc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Email account with ID {account_id} not found or access denied.")

    threads = crud_email_content.get_threads_for_user(
        db=db, user_id=current_user.id, account_id=account_id, skip=skip, limit=limit
    )
    # Pydantic will automatically map SQLAlchemy model fields to the schema.
    # Manual mapping/computation might be needed if schema fields differ significantly
    # or require complex calculations not directly on the model.
    # For example, if EmailThreadOutput required participant_names not just addresses,
    # that would be computed here or in the CRUD layer.
    return threads

@router.get("/{thread_id}/messages", response_model=List[schemas.email_content.EmailMessageOutput])
def list_messages_in_thread(
    thread_id: str,
    skip: int = 0,
    limit: int = 50, # Consider pagination for very long threads
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user),
):
    """
    List messages within a specific thread for the authenticated user.
    """
    messages = crud_email_content.get_messages_for_thread(
        db=db, thread_id=thread_id, user_id=current_user.id, skip=skip, limit=limit
    )
    if not messages and skip == 0: # Check if thread itself was valid but just empty
        # crud_get_messages_for_thread returns [] if thread not found for user.
        # We might want to distinguish "thread not found" from "thread is empty".
        # This currently doesn't, but the CRUD could raise an exception.
        # For now, an empty list is returned, which is acceptable.
        pass
    return messages

# Example: Endpoint to get a single message (could be useful for deep linking or specific actions)
# @router.get("/messages/{message_id_header}", response_model=schemas.email_content.EmailMessageOutput)
# def get_single_message(
#     message_id_header: str, # Ensure this is URL-encoded if passed as path param
#     db: Session = Depends(get_db),
#     current_user: models.user.User = Depends(get_current_user)
# ):
#     # URL decode message_id_header if necessary
#     import urllib.parse
#     decoded_message_id = urllib.parse.unquote(message_id_header)
#
#     message = crud_email_content.get_message_by_message_id_header(db, message_id_header=decoded_message_id, user_id=current_user.id)
#     if not message:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
#     return message
