from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models as db_models # For User model type hint
from app import schemas # For Pydantic schemas
from app.database import get_db
from app.security import get_current_user
from app.crud import complaint_data as crud_complaint_data # CRUD functions

router = APIRouter(prefix="/complaints-suggestions", tags=["Complaints & Suggestions"]) # Matching frontend route

@router.get("/", response_model=List[schemas.complaint_data.ComplaintDataOutput])
def list_complaints_and_suggestions_for_user(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """
    List all extracted complaints and suggestions for the authenticated user.
    """
    complaints = crud_complaint_data.get_complaints_for_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return complaints

# Example: Get a specific complaint by ID (if needed later)
# @router.get("/{complaint_id}", response_model=schemas.complaint_data.ComplaintDataOutput)
# def get_single_complaint_suggestion(
#     complaint_id: int,
#     db: Session = Depends(get_db),
#     current_user: db_models.User = Depends(get_current_user)
# ):
#     complaint = crud_complaint_data.get_complaint_by_id(db, complaint_id=complaint_id, user_id=current_user.id)
#     if not complaint:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint/Suggestion not found or access denied.")
#     return complaint
