from fastapi import FastAPI

app = FastAPI(title="Email Management Backend API")

# Import routers
from app.api.endpoints import auth as auth_router
from app.api.endpoints import email_accounts as email_accounts_router
from app.api.endpoints import threads as threads_router
from app.api.endpoints import actions as actions_router
from app.api.endpoints import ai_actions as ai_actions_router
from app.api.endpoints import complaints as complaints_router
from app.api.endpoints import attachments as attachments_router # New attachments router

@app.get("/")
async def root():
    return {"message": "Welcome to the Email Management Backend API"}

# Include routers
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(email_accounts_router.router, prefix="/api/v1/email-accounts", tags=["Email Accounts"])
app.include_router(threads_router.router, prefix="/api/v1/threads", tags=["Email Threads & Messages"])
app.include_router(actions_router.router, prefix="/api/v1/actions", tags=["Email Actions"])
app.include_router(ai_actions_router.router, prefix="/api/v1", tags=["AI Actions"])
app.include_router(complaints_router.router, prefix="/api/v1", tags=["Complaints & Suggestions"])
app.include_router(attachments_router.router, prefix="/api/v1", tags=["Attachments"]) # Attachments router, e.g. /api/v1/attachments/...
