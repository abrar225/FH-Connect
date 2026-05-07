"""
core/ids.py — ID generation utilities.

Provides consistent ID and trace_id generation across all modules.
"""

import uuid


def new_id() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def new_trace_id() -> str:
    """Generate a new trace ID. Same format as new_id but semantically distinct."""
    return str(uuid.uuid4())
