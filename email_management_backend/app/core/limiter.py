from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import REDIS_URL # Import REDIS_URL from your config

# Determine storage URI: use Redis if REDIS_URL is set, otherwise fallback to in-memory.
# This is important for environments where Redis might not be available (e.g., some test setups).
storage_uri = REDIS_URL if REDIS_URL else "memory://"

limiter = Limiter(
    key_func=get_remote_address,        # Uses the client's IP address as the key
    storage_uri=storage_uri,            # Specifies Redis (or memory) as the storage
    strategy="fixed-window",            # Rate limiting strategy (e.g., fixed-window, moving-window)
    # default_limits=["100/minute"]     # Optional: default limits for all routes not explicitly decorated
)

# You can also define named limits here if you prefer, e.g.:
# limiter.limit("5/minute", "login_attempts")
# And then use @limiter.limit("login_attempts") in your routes.

# The RateLimitExceeded exception and _rate_limit_exceeded_handler are re-exported
# so they can be easily imported into main.py for app configuration.
