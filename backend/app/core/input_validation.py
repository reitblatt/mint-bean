"""Input validation and sanitization for defense-in-depth security.

This module provides additional input validation beyond Pydantic's automatic validation
to protect against:
- SQL Injection (parameterized queries + validation)
- XSS (Cross-Site Scripting) attacks
- Command Injection
- Path Traversal
- LDAP Injection
- NoSQL Injection

Note: This is defense-in-depth. SQLAlchemy parameterized queries already prevent
SQL injection, but this adds an additional validation layer.
"""

import re
from typing import Any


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string for safe storage and display.

    Removes dangerous characters and limits length.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValueError: If input is invalid
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")

    # Remove null bytes (common in injection attacks)
    value = value.replace("\x00", "")

    # Limit length
    if len(value) > max_length:
        raise ValueError(f"String exceeds maximum length of {max_length}")

    return value.strip()


def validate_sql_safe(value: str) -> str:
    """
    Validate that a string doesn't contain SQL injection patterns.

    This is defense-in-depth - SQLAlchemy parameterized queries already
    prevent SQL injection, but this adds an extra validation layer.

    Args:
        value: String to validate

    Returns:
        Original value if safe

    Raises:
        ValueError: If dangerous SQL patterns detected
    """
    # Common SQL injection patterns
    dangerous_patterns = [
        r"(?i)\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\s",
        r"--",  # SQL comment
        r"/\*.*\*/",  # SQL comment block
        r";.*--",  # Command chaining
        r"(?i)\b(or|and)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+",  # Always true conditions
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, value):
            raise ValueError("Input contains potentially dangerous SQL patterns")

    return value


def validate_no_script_tags(value: str) -> str:
    """
    Validate that a string doesn't contain script tags (XSS prevention).

    Args:
        value: String to validate

    Returns:
        Original value if safe

    Raises:
        ValueError: If script tags detected
    """
    # Check for script tags (case-insensitive)
    if re.search(r"<\s*script[^>]*>", value, re.IGNORECASE):
        raise ValueError("Input contains script tags")

    # Check for event handlers (onclick, onload, etc.)
    if re.search(r"\bon\w+\s*=", value, re.IGNORECASE):
        raise ValueError("Input contains event handlers")

    # Check for javascript: protocol
    if re.search(r"javascript\s*:", value, re.IGNORECASE):
        raise ValueError("Input contains javascript: protocol")

    return value


def sanitize_html(value: str) -> str:
    """
    Sanitize HTML by escaping dangerous characters.

    Args:
        value: String to sanitize

    Returns:
        Sanitized string with HTML entities escaped
    """
    # Escape HTML special characters
    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;",
    }

    for char, entity in replacements.items():
        value = value.replace(char, entity)

    return value


def validate_safe_filename(filename: str) -> str:
    """
    Validate that a filename is safe (prevents path traversal).

    Args:
        filename: Filename to validate

    Returns:
        Original filename if safe

    Raises:
        ValueError: If filename is unsafe
    """
    # Check for path traversal patterns
    dangerous_patterns = [
        r"\.\.",  # Parent directory
        r"^/",  # Absolute path
        r"^\\",  # Windows absolute path
        r":",  # Windows drive letter
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, filename):
            raise ValueError("Filename contains path traversal patterns")

    # Only allow alphanumeric, dash, underscore, and dot
    if not re.match(r"^[a-zA-Z0-9._-]+$", filename):
        raise ValueError("Filename contains invalid characters")

    return filename


def validate_email_format(email: str) -> str:
    """
    Validate email format (additional check beyond email-validator).

    Args:
        email: Email address to validate

    Returns:
        Lowercase email if valid

    Raises:
        ValueError: If email format is invalid
    """
    # Basic email regex (not perfect but catches obvious issues)
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        raise ValueError("Invalid email format")

    # Limit length
    if len(email) > 254:  # RFC 5321
        raise ValueError("Email exceeds maximum length")

    # Normalize to lowercase
    return email.lower()


def validate_alphanumeric(value: str, allow_spaces: bool = False) -> str:
    """
    Validate that a string contains only alphanumeric characters.

    Args:
        value: String to validate
        allow_spaces: Whether to allow spaces

    Returns:
        Original value if valid

    Raises:
        ValueError: If non-alphanumeric characters found
    """
    pattern = r"^[a-zA-Z0-9\s]+$" if allow_spaces else r"^[a-zA-Z0-9]+$"

    if not re.match(pattern, value):
        raise ValueError("Input must contain only alphanumeric characters")

    return value


def validate_integer_range(
    value: Any, min_val: int | None = None, max_val: int | None = None
) -> int:
    """
    Validate that an integer is within a specific range.

    Args:
        value: Value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)

    Returns:
        Integer value if valid

    Raises:
        ValueError: If value is out of range
    """
    try:
        int_val = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError("Value must be an integer") from e

    if min_val is not None and int_val < min_val:
        raise ValueError(f"Value must be at least {min_val}")

    if max_val is not None and int_val > max_val:
        raise ValueError(f"Value must be at most {max_val}")

    return int_val


def validate_no_special_chars(value: str, allowed_chars: str = "") -> str:
    """
    Validate that a string doesn't contain special characters.

    Args:
        value: String to validate
        allowed_chars: String of additional allowed characters (e.g., "-_.")

    Returns:
        Original value if valid

    Raises:
        ValueError: If special characters found
    """
    # Allow alphanumeric and explicitly allowed characters
    pattern = f"^[a-zA-Z0-9{re.escape(allowed_chars)}]+$"

    if not re.match(pattern, value):
        raise ValueError(
            f"Input contains invalid characters (allowed: alphanumeric and '{allowed_chars}')"
        )

    return value


def sanitize_for_logging(value: str, max_length: int = 200) -> str:
    """
    Sanitize a string for safe logging (prevents log injection).

    Args:
        value: String to sanitize
        max_length: Maximum length for log output

    Returns:
        Sanitized string safe for logging
    """
    # Remove newlines and carriage returns (prevents log injection)
    value = value.replace("\n", " ").replace("\r", " ")

    # Remove null bytes
    value = value.replace("\x00", "")

    # Limit length
    if len(value) > max_length:
        value = value[:max_length] + "..."

    return value


# Validation decorator for functions
def validate_inputs(**validators):
    """
    Decorator to validate function inputs.

    Example:
        @validate_inputs(name=validate_alphanumeric, email=validate_email_format)
        def create_user(name: str, email: str):
            pass
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get function argument names
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each argument
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is not None:
                        bound_args.arguments[param_name] = validator(value)

            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper

    return decorator
