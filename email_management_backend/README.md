# Email Management Backend

This is the FastAPI backend for the Email Management Application. It provides APIs for user authentication, email account management, email processing, AI-driven features (categorization, suggestions, extraction), and more.

## Features

*   User authentication (JWT-based).
*   Secure storage of email account credentials (IMAP/SMTP passwords encrypted at rest using Fernet).
*   APIs for linking and managing multiple email accounts per user.
*   Background email fetching and processing using Celery, RabbitMQ, and Redis.
*   Parsing of raw email content into structured data (threads, messages, attachments).
*   Storage of email data in a PostgreSQL database.
*   AI-powered email categorization using Cerebras AI.
*   AI-powered reply suggestions for emails.
*   Specialized AI-driven data extraction for "Complaints/Suggestions" category emails.
*   API endpoints for retrieving threads, messages, attachments, and complaint data.
*   API endpoint for sending emails.
*   Rate limiting on sensitive/expensive endpoints.
*   Database schema management using Alembic migrations.
*   Unit and integration tests using Pytest.

## Tech Stack

*   Python 3.10+
*   FastAPI: Modern, fast (high-performance) web framework for building APIs.
*   Uvicorn: ASGI server for FastAPI.
*   SQLAlchemy: ORM for database interaction.
*   PostgreSQL: Relational database.
*   Alembic: Database migration tool for SQLAlchemy.
*   Pydantic: Data validation and settings management.
*   Celery: Distributed task queue for background processing.
*   RabbitMQ: Message broker for Celery.
*   Redis: In-memory data store for Celery results backend and rate limiting.
*   Passlib with bcrypt: For password hashing.
*   Python-JOSE: For JWT handling.
*   Cryptography (Fernet): For encrypting sensitive data.
*   Cerebras Cloud SDK: For interacting with Cerebras AI services.
*   SlowAPI: For rate limiting API endpoints.
*   Docker & Docker Compose: For containerization and local development environment.
*   Pytest: For unit and integration testing.
*   Flake8 & Black: For code linting and formatting.

## Project Structure

*   `app/`: Core application code.
    *   `api/`: API endpoint definitions.
    *   `core/`: Configuration, constants, core app setup (e.g., Celery, limiter).
    *   `crud/`: Create, Read, Update, Delete database operations.
    *   `database.py`: SQLAlchemy engine, session setup, Base model.
    *   `main.py`: FastAPI application instantiation and router inclusion.
    *   `models/`: SQLAlchemy ORM models.
    *   `schemas/`: Pydantic schemas for data validation and serialization.
    *   `services/`: Business logic services (email connection, parsing, AI interaction, categorization).
    *   `tasks.py`: Celery task definitions.
    *   `utils/`: Utility functions (e.g., encryption).
*   `alembic/`: Alembic migration scripts and configuration.
*   `tests/`: Unit and integration tests.
    *   `integration/`: Integration tests (require database and potentially other services).
    *   `services/`: Unit tests for services.
    *   `crud/`: Unit tests for CRUD functions.
*   `alembic.ini`: Alembic configuration file.
*   `Dockerfile`: For building the backend Docker image.
*   `pytest.ini`: Pytest configuration.
*   `requirements.txt`: Python dependencies.
*   `.env.example`: Example environment variables (gitignored `.env` file should be created from this).
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.

## Local Development (using Docker Compose)

Refer to the main project `README.md` in the root directory for instructions on setting up and running the entire application stack (including this backend) using Docker Compose.

## Manual Backend Setup (Alternative to Docker, for isolated development/testing)

1.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set Environment Variables**:
    *   Create a `.env` file in this directory (`email_management_backend/.env`) or set environment variables manually.
    *   Required variables include `DATABASE_URL`, `SECRET_KEY`, `FERNET_KEY`, `CEREBRAS_API_KEY`, etc. Refer to `app/core/config.py` and the root project `.env` file for a complete list.
    *   Ensure PostgreSQL, RabbitMQ, and Redis services are running and accessible as per your `.env` configuration.
4.  **Run Database Migrations**:
    *   Ensure `alembic.ini`'s `sqlalchemy.url` is correctly pointing to your database (or that `DATABASE_URL` env var is set and `env.py` uses it).
    *   From within the `email_management_backend` directory:
        ```bash
        alembic upgrade head
        ```
5.  **Run FastAPI Application**:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
    The application will be available at `http://localhost:8000`.

## Running Backend Tests Manually

1.  Ensure your virtual environment is active and dependencies (including dev/test ones like `pytest`) are installed.
2.  Set up a **test database** and configure `TEST_DATABASE_URL` environment variable as per `tests/integration/conftest.py`.
    ```bash
    export TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5434/email_manager_test_db"
    # (Ensure this test DB exists and the user has permissions)
    ```
3.  Run tests from the `email_management_backend` directory:
    ```bash
    pytest tests/
    ```

## API Documentation

Once the backend is running (either via Docker Compose or manually), API documentation (Swagger UI) is available at `/docs` (e.g., `http://localhost:8000/docs`). ReDoc documentation is at `/redoc`.
