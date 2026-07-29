"""
Small helper for encrypting/decrypting secrets before they're written to
the `settings` table (e.g. gemini_api_key). The DB column stays TEXT — we
store the encrypted value as a base64-ish token string, not raw bytes.

Setup (one-time):
    pip install cryptography
    python -m app.crypto_utils generate-key
Copy the printed value into .env as:
    ENCRYPTION_KEY=<value>
Never commit .env. Never regenerate this key once secrets are stored —
doing so makes existing encrypted values undecryptable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

_ENV_VAR_NAME = "ENCRYPTION_KEY"


class CryptoConfigError(RuntimeError):
    pass


def _load_dotenv_if_present() -> None:
    if os.environ.get(_ENV_VAR_NAME):
        return
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == _ENV_VAR_NAME and value:
            os.environ[_ENV_VAR_NAME] = value
            return


def _get_fernet() -> Fernet:
    _load_dotenv_if_present()
    key = os.environ.get(_ENV_VAR_NAME)
    if not key:
        raise CryptoConfigError(
            f"{_ENV_VAR_NAME} is not set. Generate one with:\n"
            f"    python -m app.crypto_utils generate-key\n"
            f"and add it to your .env file."
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise CryptoConfigError(
            f"{_ENV_VAR_NAME} is not a valid Fernet key. "
            f"Generate a fresh one with: python -m app.crypto_utils generate-key"
        ) from exc


def encrypt_value(value: str) -> str:
    """Encrypt a plain string, returning a token safe to store in a TEXT column."""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_value(token: str) -> Optional[str]:
    """
    Decrypt a token previously produced by encrypt_value.
    Returns None if token is empty/None. Raises CryptoConfigError on bad key,
    InvalidToken (re-raised) if the token itself is corrupt/foreign.
    """
    if not token:
        return None
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        raise


def mask_value(value: Optional[str], visible: int = 4) -> Optional[str]:
    """For display only: 'AIzaSyAbc123xyz' -> '••••••••xyz'. Never send raw keys to the frontend."""
    if not value:
        return None
    if len(value) <= visible:
        return "•" * len(value)
    return "•" * (len(value) - visible) + value[-visible:]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "generate-key":
        print(Fernet.generate_key().decode())
    else:
        print("Usage: python -m app.crypto_utils generate-key")