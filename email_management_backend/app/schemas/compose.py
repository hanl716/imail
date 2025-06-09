from pydantic import BaseModel, EmailStr
from typing import List, Optional

class EmailCompose(BaseModel):
    from_account_id: int
    to_recipients: List[EmailStr]
    cc_recipients: List[EmailStr] = []
    bcc_recipients: List[EmailStr] = []
    subject: str
    body_text: str
    body_html: Optional[str] = None

    # For handling replies/forwards later
    # in_reply_to_message_id_header: Optional[str] = None
    # references_header: Optional[str] = None

    class Config:
        # Pydantic V2 example for schema extras if needed, though not for this model
        # model_config = {
        #     "json_schema_extra": {
        #         "examples": [
        #             {
        #                 "from_account_id": 1,
        #                 "to_recipients": ["recipient1@example.com"],
        #                 "cc_recipients": ["cc@example.com"],
        #                 "subject": "Hello there!",
        #                 "body_text": "This is the content of the email."
        #             }
        #         ]
        #     }
        # }
        pass
