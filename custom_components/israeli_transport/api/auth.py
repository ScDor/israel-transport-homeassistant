"""Authentication utilities for Israeli Transport API."""
from __future__ import annotations

import datetime

from ..const import API_KEY_SEED


def generate_api_key() -> str:
    """Generate the API key using XOR encryption with today's date.

    The API uses a simple XOR cipher where today's date (YYYY-MM-DD)
    is XORed with the seed string "natan" repeated cyclically.

    Returns:
        The encrypted API key as a string.
    """
    today = datetime.date.today().isoformat()  # Format: YYYY-MM-DD

    return "".join(
        chr(ord(date_char) ^ ord(API_KEY_SEED[i % len(API_KEY_SEED)]))
        for i, date_char in enumerate(today)
    )
