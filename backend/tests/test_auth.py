"""Tests for authentication flows: registration, login, and JWT token handling."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import auth as auth_routes
from app.api.routes import values as values_routes
from app.auth import create_access_token, decode_access_token, hash_password
from app.core.database import get_db
from app.models import Base, User

# Create a separate in-memory database for auth tests
# Use a unique name to avoid conflicts with other test files
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:?cache=shared"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create a test-specific app instance to avoid conflicts with other test files
test_app = FastAPI()
test_app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
test_app.include_router(values_routes.router, prefix="/api/values", tags=["values"])

# Override only the database dependency
test_app.dependency_overrides[get_db] = override_get_db

client = TestClient(test_app)


@pytest.fixture(autouse=True)
def clean_database():
    """Clean up database before and after each test."""
    db = TestingSessionLocal()
    try:
        # Delete all data BEFORE each test
        db.query(User).delete()
        db.commit()
    finally:
        db.close()

    # Yield to run the test
    yield

    # Clean up after test as well
    db = TestingSessionLocal()
    try:
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


class TestRegistration:
    """Tests for user registration endpoint."""

    def test_register_new_user(self):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["is_active"] is True
        assert "password" not in data["user"]

    def test_register_duplicate_username(self):
        """Test registration fails with duplicate username."""
        # Register first user
        client.post(
            "/api/auth/register",
            json={
                "username": "duplicate",
                "email": "user1@example.com",
                "password": "pass1234",
            },
        )

        # Try to register with same username but different email
        response = client.post(
            "/api/auth/register",
            json={
                "username": "duplicate",
                "email": "user2@example.com",
                "password": "pass4567",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Username already registered"

    def test_register_duplicate_email(self):
        """Test registration fails with duplicate email."""
        # Register first user
        client.post(
            "/api/auth/register",
            json={
                "username": "user1",
                "email": "same@example.com",
                "password": "pass1234",
            },
        )

        # Try to register with same email but different username
        response = client.post(
            "/api/auth/register",
            json={
                "username": "user2",
                "email": "same@example.com",
                "password": "pass4567",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"


class TestLogin:
    """Tests for user login endpoint."""

    def test_login_success(self):
        """Test successful login with valid credentials."""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "username": "logintest",
                "email": "login@example.com",
                "password": "password123",
            },
        )

        # Login with valid credentials
        response = client.post(
            "/api/auth/login",
            json={
                "username": "logintest",
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "logintest"
        assert data["user"]["email"] == "login@example.com"

    def test_login_wrong_password(self):
        """Test login fails with incorrect password."""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "username": "user",
                "email": "user@example.com",
                "password": "correctpass",
            },
        )

        # Try to login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "username": "user",
                "password": "wrongpass",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_nonexistent_user(self):
        """Test login fails for non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "anypass",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_inactive_user(self):
        """Test login fails for inactive user."""
        # Create inactive user directly in database
        db = TestingSessionLocal()
        try:
            hashed = hash_password("password123")
            inactive_user = User(
                username="inactive",
                email="inactive@example.com",
                password_hash=hashed,
                is_active=False,
            )
            db.add(inactive_user)
            db.commit()
        finally:
            db.close()

        # Try to login
        response = client.post(
            "/api/auth/login",
            json={
                "username": "inactive",
                "password": "password123",
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Inactive user"


class TestJWTTokenHandling:
    """Tests for JWT token creation and validation."""

    def test_token_contains_user_id_as_string(self):
        """Test that JWT token stores user ID as a string per RFC 7519."""
        # Register user
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "tokentest",
                "email": "token@example.com",
                "password": "pass1234",
            },
        )

        token = register_response.json()["access_token"]

        # Decode token and verify 'sub' is a string
        payload = decode_access_token(token)
        assert "sub" in payload
        assert isinstance(payload["sub"], str)

        # Verify it can be converted back to int
        user_id = int(payload["sub"])
        assert user_id > 0

    def test_token_can_be_used_for_authenticated_endpoints(self):
        """Test that JWT token works with authenticated endpoints."""
        # Register user
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "authtest",
                "email": "auth@example.com",
                "password": "pass1234",
            },
        )

        token = register_response.json()["access_token"]

        # Use token to access authenticated endpoint (values API)
        response = client.get(
            "/api/values",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_invalid_token_returns_401(self):
        """Test that invalid token returns 401 error."""
        response = client.get(
            "/api/values",
            headers={"Authorization": "Bearer invalid-token-12345"},
        )

        assert response.status_code == 401

    def test_missing_token_returns_401(self):
        """Test that missing token returns 401 error."""
        response = client.get("/api/values")

        assert response.status_code == 401

    def test_string_to_int_conversion_in_get_current_user(self):
        """Test that get_current_user correctly converts string user ID to int."""
        # Register user
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "conversiontest",
                "email": "conversion@example.com",
                "password": "pass1234",
            },
        )

        token = register_response.json()["access_token"]

        # Create a value using the token (exercises get_current_user)
        # If get_current_user string-to-int conversion fails, this will return 401
        response = client.post(
            "/api/values",
            headers={"Authorization": f"Bearer {token}"},
            json={"statement": "Test value"},
        )

        assert response.status_code == 201
        # Verify the value was created successfully
        assert response.json()["statement"] == "Test value"
        assert response.json()["archived"] is False

    def test_token_with_invalid_user_id_format(self):
        """Test that token with non-integer user ID is rejected."""
        # Create token with invalid user ID format
        invalid_token = create_access_token(data={"sub": "not-a-number"})

        response = client.get(
            "/api/values",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

        assert response.status_code == 401
        assert "Invalid authentication credentials" in response.json()["detail"]


class TestPasswordHashing:
    """Tests for password hashing and verification functions."""

    def test_hash_password_produces_argon2_hash(self):
        """Test that hash_password produces an Argon2 hash."""
        from app.auth import hash_password

        password = "testpassword123"
        hashed = hash_password(password)

        # Argon2 hashes start with "$argon2"
        assert hashed.startswith("$argon2")
        # Hash should be different from the plain password
        assert hashed != password

    def test_verify_password_with_argon2_hash(self):
        """Test that verify_password correctly verifies Argon2 hashes."""
        from app.auth import hash_password, verify_password

        password = "correctpassword"
        hashed = hash_password(password)

        # Correct password should verify
        assert verify_password(password, hashed) is True
        # Wrong password should not verify
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_with_legacy_bcrypt_hash(self):
        """Test that verify_password correctly verifies legacy bcrypt hashes."""
        import bcrypt
        from app.auth import verify_password

        # Create a legacy bcrypt hash directly
        password = "legacypassword123"
        bcrypt_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        bcrypt_hash_str = bcrypt_hash.decode("utf-8")

        # Correct password should verify
        assert verify_password(password, bcrypt_hash_str) is True
        # Wrong password should not verify
        assert verify_password("wrongpassword", bcrypt_hash_str) is False

    def test_verify_password_distinguishes_hash_types(self):
        """Test that verify_password correctly routes to the right algorithm."""
        import bcrypt
        from app.auth import hash_password, verify_password

        password = "testpassword"

        # Create both types of hashes
        argon2_hash = hash_password(password)
        bcrypt_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

        # Both should verify correctly
        assert verify_password(password, argon2_hash) is True
        assert verify_password(password, bcrypt_hash) is True

        # Wrong password should fail for both
        assert verify_password("wrongpass", argon2_hash) is False
        assert verify_password("wrongpass", bcrypt_hash) is False

    def test_verify_password_with_invalid_hash(self):
        """Test that verify_password returns False for invalid hashes."""
        from app.auth import verify_password

        # Invalid hash formats should return False, not raise exceptions
        assert verify_password("password", "not-a-valid-hash") is False
        assert verify_password("password", "") is False
        assert verify_password("password", "$argon2invalid") is False

    def test_login_with_legacy_bcrypt_hash(self):
        """Test that users with legacy bcrypt hashes can still login."""
        import bcrypt

        # Create a user with a legacy bcrypt hash directly in database
        db = TestingSessionLocal()
        try:
            password = "legacyuserpass"
            bcrypt_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            legacy_user = User(
                username="legacyuser",
                email="legacy@example.com",
                password_hash=bcrypt_hash.decode("utf-8"),
                is_active=True,
            )
            db.add(legacy_user)
            db.commit()
        finally:
            db.close()

        # User should be able to login with their password
        response = client.post(
            "/api/auth/login",
            json={
                "username": "legacyuser",
                "password": password,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "legacyuser"
