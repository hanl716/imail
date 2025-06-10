# Email Management Application

This is a full-stack application designed for managing and interacting with email accounts, featuring an IM-like interface, AI-powered email categorization, reply suggestions, and complaint/suggestion data extraction.

The application is built with a FastAPI backend, a Vue.js frontend, and uses Celery for background tasks with RabbitMQ as the message broker and Redis for results/caching. PostgreSQL is used for the database. Docker and Docker Compose are used for containerization and local development orchestration.

## Features (Conceptual & Implemented)

*   User authentication (Registration, Login, Logout with JWT).
*   Linking multiple email accounts (IMAP/SMTP credentials stored encrypted).
*   IM-like interface for viewing email threads and messages.
*   Multi-account switching in the UI.
*   Background email fetching and processing via Celery.
*   AI-powered email categorization (using Cerebras AI).
*   AI-powered reply suggestions for emails (using Cerebras AI).
*   Special handling for "Complaints/Suggestions" category, including AI-driven information extraction.
*   UI to display extracted complaint/suggestion data with basic charts.
*   Basic email composition and sending.
*   Display of email attachments with download links for small files.
*   API-level integration tests and initial frontend unit tests.
*   CI/CD pipeline outline and GitHub Actions workflow.
*   Rate limiting on key API endpoints.

## Prerequisites

*   Docker Engine (e.g., Docker Desktop)
*   Docker Compose (usually included with Docker Desktop)
*   Access to a Cerebras AI environment and an API Key (for AI features)
*   Python (for generating Fernet key locally if needed, though can also be done in Docker)

## Local Development Setup

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd <repository_name> # e.g., email-management-platform
    ```

2.  **Create Environment File (`.env`)**:
    *   In the project root directory, create a file named `.env`.
    *   Copy the content from the example below (or a provided `.env.example` if available in the future) into your `.env` file.
    *   **Crucially, edit this `.env` file** to replace placeholder values with your actual secrets and configurations:

    ```env
    # PostgreSQL Credentials
    POSTGRES_USER=app_user
    POSTGRES_PASSWORD=app_password_strong # Replace with a strong password
    POSTGRES_DB=email_manager_db

    # Backend Environment Variables
    # Ensure POSTGRES_PASSWORD here matches the one above for consistency
    BACKEND_DATABASE_URL=postgresql://app_user:app_password_strong@db:5432/email_manager_db
    BACKEND_SECRET_KEY=a_very_secure_and_random_jwt_secret_key_please_change_me_for_production # Replace!
    BACKEND_ALGORITHM=HS256
    BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES=30
    # Generate a Fernet key using: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    BACKEND_FERNET_KEY=your_unique_base64_encoded_32_byte_fernet_key_here # Replace!
    BACKEND_CEREBRAS_API_KEY="your_actual_cerebras_api_key_from_cloud.cerebras.ai" # Replace!

    # Celery Configuration
    CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
    CELERY_RESULT_BACKEND=redis://redis:6379/0

    # Redis URL (for rate limiting, etc.)
    REDIS_URL=redis://redis:6379/1

    # RabbitMQ Credentials (for the rabbitmq service itself)
    RABBITMQ_DEFAULT_USER=guest
    RABBITMQ_DEFAULT_PASS=guest
    ```

3.  **Build and Start Services**:
    ```bash
    docker-compose build
    docker-compose up -d
    ```
    *   This will build the Docker images for the backend and frontend, and start all services (PostgreSQL, RabbitMQ, Redis, backend, frontend, Celery worker, Celery beat) in detached mode.
    *   The first time the backend starts, Alembic migrations will run automatically (as per backend Dockerfile CMD) to set up the database schema.

4.  **Accessing the Application**:
    *   Frontend UI: `http://localhost:8080`
    *   Backend API Docs (Swagger UI): `http://localhost:8000/docs`
    *   RabbitMQ Management UI: `http://localhost:15672` (Default user: `guest`, pass: `guest`)
    *   Flower (Celery Monitoring - if added to docker-compose later): `http://localhost:5555`

## Running Tests

### Backend Tests
Ensure Docker Compose services (especially the test database if configured for integration tests) are running or accessible.
```bash
cd email_management_backend
# Set TEST_DATABASE_URL if your conftest.py expects it and it's different from dev DB
# export TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5434/email_manager_test_db"
pytest tests/
```
(See `email_management_backend/tests/integration/conftest.py` for test database setup details).

### Frontend Tests
```bash
cd email_management_frontend
npm run test:unit
# Or: yarn test:unit
```

## Project Structure Overview

*   `.env`: Root environment variables for Docker Compose (gitignored).
*   `docker-compose.yml`: Defines all services for local development and orchestration.
*   `PRODUCTION_CHECKLIST.md`: Important considerations for deploying to production.
*   `.github/workflows/ci.yml`: GitHub Actions CI/CD pipeline definition.
*   `email_management_backend/`: Contains the FastAPI backend application.
    *   `README.md`: Backend-specific details.
*   `email_management_frontend/`: Contains the Vue.js frontend application.
    *   `README.md`: Frontend-specific details.

## Further Documentation

*   Backend details: `email_management_backend/README.md`
*   Frontend details: `email_management_frontend/README.md`
*   Production Deployment Checklist: `PRODUCTION_CHECKLIST.md`

---
*This project was developed with the assistance of an AI agent.*
