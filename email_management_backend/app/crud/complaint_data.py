from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Tuple # Tuple for query result if joining specific columns

from app.models.complaint_data import ComplaintData
from app.models.email_content import EmailMessage # For joining to get email_subject
from app.schemas.complaint_data import ComplaintDataOutput # For type hinting or structuring output

def get_complaints_for_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[ComplaintDataOutput]:
    """
    Fetches ComplaintData records for a user, ordered by extracted_at descending.
    Includes the subject of the original email.
    """
    results = (
        db.query(
            ComplaintData,
            EmailMessage.subject.label("email_subject")
        )
        .join(EmailMessage, ComplaintData.email_message_id == EmailMessage.id)
        .filter(ComplaintData.user_id == user_id) # Assuming user_id is on ComplaintData directly
        # If user_id was only on EmailMessage, filter would be: .filter(EmailMessage.user_id == user_id)
        .order_by(desc(ComplaintData.extracted_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Map results to the Pydantic schema ComplaintDataOutput
    output_list: List[ComplaintDataOutput] = []
    for complaint_data, email_subject in results:
        # Create a dictionary from the SQLAlchemy model instance
        complaint_dict = {column.name: getattr(complaint_data, column.name) for column in complaint_data.__table__.columns}
        # Add the joined email_subject
        complaint_dict["email_subject"] = email_subject
        output_list.append(ComplaintDataOutput(**complaint_dict))

    return output_list

# Example for getting a single complaint by ID (if needed later)
# def get_complaint_by_id(db: Session, complaint_id: int, user_id: int) -> Optional[ComplaintDataOutput]:
#     result = (
#         db.query(
#             ComplaintData,
#             EmailMessage.subject.label("email_subject")
#         )
#         .join(EmailMessage, ComplaintData.email_message_id == EmailMessage.id)
#         .filter(ComplaintData.id == complaint_id, ComplaintData.user_id == user_id)
#         .first()
#     )
#     if result:
#         complaint_data, email_subject = result
#         complaint_dict = {column.name: getattr(complaint_data, column.name) for column in complaint_data.__table__.columns}
#         complaint_dict["email_subject"] = email_subject
#         return ComplaintDataOutput(**complaint_dict)
#     return None
