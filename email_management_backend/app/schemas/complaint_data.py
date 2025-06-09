from pydantic import BaseModel
from typing import Optional, List # For potential future use if schema becomes complex
import datetime

class ComplaintDataOutput(BaseModel):
    id: int
    email_message_id: int
    submitter_email: str
    submitter_name: Optional[str] = None
    issue_type: str
    category_detail: Optional[str] = None
    product_service: Optional[str] = None
    summary: str
    sentiment: Optional[str] = None
    extracted_at: datetime.datetime

    # Field to be populated from related EmailMessage
    email_subject: Optional[str] = None

    class Config:
        orm_mode = True
