"""
gemini_key.py

Single source of truth for retrieving the Gemini API key, wherever it's
needed in the project (routes, scrapers, background jobs, one-off scripts).

Usage:
    from app.gemini_key import get_gemini_api_key

    api_key = get_gemini_api_key()
    if api_key is None:
        raise RuntimeError("No Gemini API key configured yet")
"""

from __future__ import annotations

from typing import Optional

from cryptography.fernet import InvalidToken

from .crypto_utils import decrypt_value
from db.database import get_connection


def get_gemini_api_key() -> Optional[str]:
    """
    Fetch and decrypt the Gemini API key stored in the settings table.
    Returns None if no key has been set, or if it exists but can't be
    decrypted (e.g. ENCRYPTION_KEY changed since it was stored).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT gemini_api_key FROM settings WHERE id = 1")
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    encrypted = row["gemini_api_key"]
    if not encrypted:
        return None

    try:
        return decrypt_value(encrypted)
    except InvalidToken:
        return None