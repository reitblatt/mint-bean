#!/usr/bin/env python3
"""Quick test script for encryption functionality."""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from app.core.encryption import decrypt_value, encrypt_value, is_encrypted


def test_basic_encryption():
    """Test basic encryption/decryption."""
    print("Testing basic encryption...")

    # Test string
    plaintext = "my-secret-api-key-12345"
    print(f"  Original: {plaintext}")

    # Encrypt
    encrypted = encrypt_value(plaintext)
    print(
        f"  Encrypted: {encrypted[:50]}..." if len(encrypted) > 50 else f"  Encrypted: {encrypted}"
    )

    # Decrypt
    decrypted = decrypt_value(encrypted)
    print(f"  Decrypted: {decrypted}")

    # Verify
    assert decrypted == plaintext, "Decryption failed!"
    assert is_encrypted(encrypted), "is_encrypted detection failed!"
    assert not is_encrypted(plaintext), "False positive for is_encrypted!"

    print("  ✓ Basic encryption test passed\n")


def test_none_and_empty():
    """Test handling of None and empty strings."""
    print("Testing None and empty values...")

    # Test None
    assert encrypt_value(None) is None
    assert decrypt_value(None) is None
    print("  ✓ None handling correct")

    # Test empty string
    assert encrypt_value("") == ""
    assert decrypt_value("") == ""
    print("  ✓ Empty string handling correct\n")


def test_model_integration():
    """Test encryption with AppSettings model."""
    print("Testing AppSettings model integration...")

    from app.core.database import SessionLocal
    from app.models.app_settings import AppSettings

    db = SessionLocal()
    try:
        # Get or create settings
        settings = db.query(AppSettings).first()
        if not settings:
            settings = AppSettings(plaid_environment="sandbox")
            db.add(settings)
            db.commit()

        # Test setting and getting encrypted value
        test_secret = "test-plaid-secret-abc123"
        settings.plaid_sandbox_secret = test_secret
        db.commit()

        # Refresh from DB
        db.refresh(settings)

        # Verify the stored value is encrypted
        assert is_encrypted(settings._plaid_sandbox_secret), "Secret not encrypted in database!"

        # Verify decryption works via property
        assert settings.plaid_sandbox_secret == test_secret, "Decryption via property failed!"

        print(f"  Original: {test_secret}")
        print(f"  Stored (encrypted): {settings._plaid_sandbox_secret[:50]}...")
        print(f"  Retrieved (decrypted): {settings.plaid_sandbox_secret}")
        print("  ✓ Model integration test passed\n")

    finally:
        db.close()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Encryption Test Suite")
    print("=" * 60)
    print()

    # Check for encryption key
    if not os.getenv("ENCRYPTION_KEY"):
        print("❌ ERROR: ENCRYPTION_KEY not set in environment")
        sys.exit(1)

    try:
        test_basic_encryption()
        test_none_and_empty()
        test_model_integration()

        print("=" * 60)
        print("✅ All encryption tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
