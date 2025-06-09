from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class EmailAccountBase(BaseModel):
    email_address: EmailStr
    email_user: Optional[str] = None # Username for login, if different from email_address

    imap_server: Optional[str] = None
    imap_port: Optional[int] = None
    # imap_use_ssl: bool = True # Example: add flags for connection settings

    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    # smtp_use_tls: bool = True # Example

class EmailAccountCreate(EmailAccountBase):
    # For password-based auth
    password: Optional[str] = Field(None, min_length=1) # Require if providing, but field itself is optional

    # For OAuth2 based auth
    access_token: Optional[str] = Field(None, min_length=1)
    refresh_token: Optional[str] = Field(None, min_length=1) # Optional for now

    # Ensure at least one form of authentication is provided if not just saving metadata
    # This validation can be done at the API endpoint or service layer.
    # Example:
    # @validator('password', always=True)
    # def check_auth_method(cls, v, values):
    #     if not v and not values.get('access_token'):
    #         # This logic is complex for Pydantic v1, easier in v2 with model_validator
    #         # For now, API layer can check this.
    #         pass
    #     return v


class EmailAccount(EmailAccountBase): # For API responses
    id: int
    user_id: int
    # email_address, email_user, imap_server etc. are inherited from EmailAccountBase

    # DO NOT include password, access_token, refresh_token (even encrypted) in API responses by default.
    # These are sensitive and should only be handled internally.

    class Config:
        orm_mode = True
