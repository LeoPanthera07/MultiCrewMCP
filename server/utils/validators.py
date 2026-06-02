"""Helper functions to validate environment variables, input queries, and order records."""

import re

def require_non_empty_string(value, field, max_len=200) -> str | None:
    """Returns an error message string if invalid, None if valid."""
    if not isinstance(value, str):
        return f"Field '{field}' must be a string."
    stripped = value.strip()
    if not stripped:
        return f"Field '{field}' cannot be empty."
    if len(stripped) > max_len:
        return f"Field '{field}' exceeds maximum length of {max_len} characters."
    return None

def validate_record_id(id: str) -> str | None:
    r"""Returns error if id doesn't match ^[A-Z0-9\-]{3,20}$ (case-insensitive).
    Returns None if valid."""
    if not isinstance(id, str):
        return "Record ID must be a string."
    # Case-insensitive match for [A-Z0-9\-] from length 3 to 20
    if not re.match(r"^[A-Za-z0-9\-]{3,20}$", id):
        return f"Record ID '{id}' must be between 3 and 20 alphanumeric characters or hyphens."
    return None
