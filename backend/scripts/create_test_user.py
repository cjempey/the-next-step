#!/usr/bin/env python3
"""
Script to create a test user and retrieve JWT token for development/testing.

Usage (from backend directory):
    uv run python scripts/create_test_user.py [username] [email] [password]
    
Examples:
    uv run python scripts/create_test_user.py
    uv run python scripts/create_test_user.py myuser test@example.com mypass123
"""

import sys
import os

# Add parent directory to path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import User
from app.auth import hash_password, create_access_token


def create_test_user(
    username: str = "testuser",
    email: str = "test@example.com", 
    password: str = "testpass123"
) -> tuple[User, str]:
    """
    Create a test user and return the user object and JWT token.
    
    Args:
        username: Username for the test user
        email: Email for the test user
        password: Password for the test user
    
    Returns:
        Tuple of (User object, JWT token string)
    """
    db: Session = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"⚠️  User '{username}' already exists. Generating token for existing user...")
            access_token = create_access_token(data={"sub": existing_user.id})
            return existing_user, access_token
        
        # Create new user
        hashed_password = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate JWT token
        access_token = create_access_token(data={"sub": new_user.id})
        
        print(f"✅ User '{username}' created successfully!")
        return new_user, access_token
        
    finally:
        db.close()


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    username = sys.argv[1] if len(sys.argv) > 1 else "testuser"
    email = sys.argv[2] if len(sys.argv) > 2 else "test@example.com"
    password = sys.argv[3] if len(sys.argv) > 3 else "testpass123"
    
    print(f"Creating test user...")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print()
    
    try:
        user, token = create_test_user(username, email, password)
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        print()
        print("Make sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database is created and migrated (alembic upgrade head)")
        print("  3. Backend dependencies are installed (uv sync)")
        sys.exit(1)
    
    print()
    print("=" * 80)
    print("JWT TOKEN (copy this to web/.env):")
    print("=" * 80)
    print(token)
    print("=" * 80)
    print()
    print("Add to web/.env file:")
    print(f"VITE_AUTH_TOKEN={token}")
    print()
    print("Or use with curl:")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/api/values')
    print()


if __name__ == "__main__":
    main()
