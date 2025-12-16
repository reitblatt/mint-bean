"""Test JWT token creation and verification."""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))  # noqa: E402

from app.core.auth import create_access_token, decode_token  # noqa: E402
from app.core.config import settings  # noqa: E402

# Test token creation and verification
print(f"JWT_SECRET_KEY: {settings.JWT_SECRET_KEY}")
print(f"JWT_ALGORITHM: {settings.JWT_ALGORITHM}")

# Create a test token
test_data = {"sub": 1}
token = create_access_token(test_data)
print(f"\nGenerated token: {token[:50]}...")

# Try to decode it
try:
    decoded = decode_token(token)
    print(f"\nDecoded successfully: {decoded}")
except Exception as e:
    print(f"\nDecode failed: {e}")
