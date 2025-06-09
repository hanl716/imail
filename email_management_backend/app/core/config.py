import os
from dotenv import load_dotenv
import secrets

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/email_manager_db")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    # In a real application, you might want to log this or handle it more gracefully
    # depending on whether the app can run without encryption (e.g., in a test mode).
    # For this application, credential encryption is critical.
    print("CRITICAL: FERNET_KEY environment variable not set. Application may not function securely.")
    # raise ValueError("FERNET_KEY must be set in the environment for credential encryption.")
    # Raising an error here might be too early if the app is run for other purposes (e.g. alembic generating script)
    # The encryption utility itself will raise an error if used without a key.

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Cerebras AI Configuration
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
if not CEREBRAS_API_KEY:
    print("WARNING: CEREBRAS_API_KEY not set. AI features requiring Cerebras will be disabled.")

# Redis URL for general use (e.g. rate limiting, caching)
# Using a different DB number (e.g. /1) than Celery results (e.g. /0) is good practice.
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")
