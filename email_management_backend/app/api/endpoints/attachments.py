import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models as db_models # For User model type hint
from app.database import get_db
from app.security import get_current_user
from app.crud import email_content as crud_email_content
from app.models.email_content import EmailAttachment # For type hint

router = APIRouter(prefix="/attachments", tags=["Attachments"])

@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """
    Allows downloading an attachment by its ID.
    Ensures the attachment belongs to the current user.
    """
    attachment = crud_email_content.get_attachment_by_id(
        db, attachment_id=attachment_id, user_id=current_user.id
    )

    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found or access denied.")

    if not attachment.content_bytes:
        # This means the attachment was too large for DB storage, or content is missing.
        # In a full system, this might redirect to S3 or a file server.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment content not available for direct download. (May be stored externally or too large)."
        )

    # Ensure filename is safe for use in Content-Disposition header
    filename = attachment.filename or f"attachment_{attachment.id}"
    # Basic sanitization: remove characters that could be problematic in headers
    safe_filename = "".join(c if c.isalnum() or c in ['.', '-', '_'] else '_' for c in filename)

    content_disposition_header = f"attachment; filename=\"{safe_filename}\""
    # For inline display for certain types (e.g. images, PDFs), could be:
    # if attachment.content_type.startswith("image/") or attachment.content_type == "application/pdf":
    #    content_disposition_header = f"inline; filename=\"{safe_filename}\""


    return StreamingResponse(
        io.BytesIO(attachment.content_bytes),
        media_type=attachment.content_type or "application/octet-stream", # Default media type
        headers={"Content-Disposition": content_disposition_header}
    )
