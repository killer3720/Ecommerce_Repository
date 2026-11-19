
import os
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL

from main import app
from app.database import Base, DATABASE_URL, get_db
from app.models.product import Product


from tests.utils.api_client import APIClient


# --------------------------------------------------
# Test Database Configuration
# --------------------------------------------------

# Allow a separate test database to be selected through the environment. When
# omitted, use the application's configured database (currently the local
# ecommerce_test_db) so pytest can start without a separate shell setting.
TEST_DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER", "postgres"),
    password=os.environ["DB_PASSWORD"],
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database="ecommerce_test_db",
)

test_engine = create_engine(TEST_DATABASE_URL)

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
    join_transaction_mode="create_savepoint"
)


# --------------------------------------------------
# Create Test Tables Once Per Test Session
# --------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def create_test_tables():

    # Clean up any leftover data from previous runs.
    Base.metadata.drop_all(bind=test_engine)

    # Create tables for automated testing.
    Base.metadata.create_all(bind=test_engine)

    yield

    # Remove test tables when the entire test session ends.
    Base.metadata.drop_all(bind=test_engine)


# --------------------------------------------------
# Database Session Fixture
# --------------------------------------------------

@pytest.fixture
def db_session(create_test_tables):

    connection = test_engine.connect()

    # Start an outer transaction for this test.
    transaction = connection.begin()

    # Bind the SQLAlchemy session to this connection.
    db = TestingSessionLocal(bind=connection)

    try:
        yield db

    finally:
        db.close()

        # Roll back all changes made during this test.
        transaction.rollback()

        connection.close()


# --------------------------------------------------
# FastAPI Test Client
# --------------------------------------------------

@pytest.fixture
def client(db_session):

    # Redirect application database requests
    # to the current test's database session.
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Restore the original dependency configuration.
    app.dependency_overrides.pop(get_db, None)


# --------------------------------------------------
# API Client Fixture
# --------------------------------------------------

@pytest.fixture
def api_client(client):
    return APIClient(client)


# --------------------------------------------------
# JWT Authentication Fixtures
# --------------------------------------------------

@pytest.fixture
def admin_headers(client):

    response = client.post(
        "/token",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def inventory_headers(client):

    response = client.post(
        "/token",
        json={
            "username": "inventory",
            "password": "inventory123"
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def customer_headers(client):

    response = client.post(
        "/token",
        json={
            "username": "customer",
            "password": "customer123"
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }
