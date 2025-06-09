from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app import schemas
from app.database import get_db
from app.security import get_current_user
from app.crud import email_account as crud_email_account

router = APIRouter()

@router.post("/", response_model=schemas.email_account.EmailAccount, status_code=status.HTTP_201_CREATED)
def create_new_email_account(
    email_account_in: schemas.email_account.EmailAccountCreate,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user),
):
    # Optionally, check if this email address is already linked by this user
    # db_existing_account = db.query(models.email_account.EmailAccount)\
    #     .filter(models.email_account.EmailAccount.user_id == current_user.id)\
    #     .filter(models.email_account.EmailAccount.email_address == email_account_in.email_address)\
    #     .first()
    # if db_existing_account:
    #     raise HTTPException(status_code=400, detail="Email address already linked by this user")

    return crud_email_account.create_email_account(
        db=db, email_account_in=email_account_in, user_id=current_user.id
    )

@router.get("/", response_model=List[schemas.email_account.EmailAccount])
def read_user_email_accounts(
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    return crud_email_account.get_email_accounts_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
