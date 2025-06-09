# Stage 1: Build stage (if there were compiled dependencies or build steps)
# For now, Python doesn't strictly need a separate build stage unless complex C extensions are involved.

# Stage 2: Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin -c "App User" appuser
# Don't chown /app yet, as files will be copied as root first

# Install system dependencies if any (e.g., for psycopg2 if not using -binary, or other tools)
# RUN apt-get update && apt-get install -y ... && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python dependencies
# Consider using a virtual environment inside Docker if preferred, but for simple cases direct install is fine.
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Now chown the app directory and its contents to the appuser
RUN chown -R appuser:appuser /app

# Ensure scripts are executable if any (e.g. for alembic migrations)
# Example: RUN chmod +x ./scripts/run_migrations.sh
# For alembic in CMD, ensure alembic is executable or called via python -m alembic

USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn
# The default path for user-installed packages like alembic might not be in $PATH for the non-root user.
# We might need to call it via its full path or ensure ~/.local/bin is in PATH.
# A simpler way is to use `python -m alembic`.
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
