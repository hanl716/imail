import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app # Main FastAPI app
from app.database import Base, get_db
from app.core.config import DATABASE_URL # To form a default test DB URL
import os

# It's critical that TEST_DATABASE_URL points to a database that can be wiped and recreated.
# For local testing, this might be a local PostgreSQL instance or a Dockerized one.
# For CI, this would be a service container (e.g., services: postgres: ... in GitHub Actions).
DEFAULT_TEST_DB_URL = "postgresql://test_user:test_password@localhost:5434/email_manager_test_db"
# The user/pass/port/db name should match what the CI service or local test DB is configured with.
# If DATABASE_URL is `postgresql://app_user:app_password_strong@db:5432/email_manager_db`
# then DATABASE_URL + "_test" would be `postgresql://app_user:app_password_strong@db:5432/email_manager_db_test`
# This assumes the 'db' service is accessible and the user has rights to create/drop 'email_manager_db_test'.

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DB_URL)


engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db_session_wide():
    # This runs once per test session.
    # Ensures tables are created based on current models.
    # For evolving schemas, running Alembic migrations is more robust.
    # from alembic.config import Config
    # from alembic import command
    #
    # print(f"Setting up test database: {TEST_DATABASE_URL}")
    # # Ensure alembic.ini is found or configure programmatically
    # # Assuming alembic.ini is in the root of email_management_backend
    # alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'alembic.ini')
    # if not os.path.exists(alembic_ini_path):
    #     # Try relative to CWD if tests are run from backend root
    #     alembic_ini_path = "alembic.ini"
    #
    # if os.path.exists(alembic_ini_path):
    #     alembic_cfg = Config(alembic_ini_path)
    #     alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    #     print("Dropping all existing tables in test database (if any)...")
    #     command.downgrade(alembic_cfg, "base") # Ensure clean state
    #     print("Applying all migrations to test database...")
    #     command.upgrade(alembic_cfg, "head")
    # else:
    #     print(f"WARNING: alembic.ini not found at {alembic_ini_path} or default. Using Base.metadata.create_all().")
    #     print("Dropping all existing tables in test database (if any)...")
    Base.metadata.drop_all(bind=engine) # Ensure clean state before creating
    print("Creating all tables in test database using Base.metadata.create_all()...")
    Base.metadata.create_all(bind=engine)

    yield # Tests run here

    print("Tearing down test database (dropping all tables)...")
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Session: # Type hint for clarity
    """
    Provides a transactional scope for tests. Rolls back changes after each test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session # Test runs with this session

    session.close()
    transaction.rollback() # Rollback any changes made during the test
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient: # Type hint for clarity
    """
    Provides a FastAPI TestClient that uses the transactional db_session fixture.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            # db_session.close() # Closing is handled by the db_session fixture itself after transaction rollback
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client # Test runs with this client

    del app.dependency_overrides[get_db] # Clean up the override after test
