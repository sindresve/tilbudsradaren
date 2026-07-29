from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..crypto_utils import CryptoConfigError, encrypt_value, mask_value
from ..deps import get_db
from ..gemini_key import get_gemini_api_key
from ..utils import row_to_dict

router = APIRouter(prefix="/api/settings", tags=["settings"])


class StoreToggle(BaseModel):
    store: str
    enabled: bool


class ConfigSettings(BaseModel):
    # gemini_api_key is never sent back in full - only a masked preview,
    # plus whether one is set at all. The frontend uses `gemini_api_key_set`
    # to decide what to show; it never receives the real key back.
    gemini_api_key_set: bool
    gemini_api_key_preview: Optional[str] = None


class SettingsResponse(BaseModel):
    stores: List[StoreToggle]
    config: ConfigSettings


class SettingsPatch(BaseModel):
    # Keyed by store name, e.g. {"rema": true, "meny": false}.
    stores: Optional[Dict[str, bool]] = None
    # Plain-text key as typed by the user - encrypted before it touches the DB.
    # Sending an empty string clears the stored key.
    gemini_api_key: Optional[str] = None


def _get_config(conn) -> ConfigSettings:
    # Check whether *something* is stored, independent of whether it can
    # still be decrypted (key rotation edge case).
    cursor = conn.cursor()
    cursor.execute("SELECT gemini_api_key FROM settings WHERE id = 1")
    row = cursor.fetchone()
    has_stored_value = bool(row and row["gemini_api_key"])

    if not has_stored_value:
        return ConfigSettings(gemini_api_key_set=False, gemini_api_key_preview=None)

    plain = get_gemini_api_key()  # None if decrypt fails
    if plain is None:
        return ConfigSettings(gemini_api_key_set=True, gemini_api_key_preview="••• (kan ikke leses)")

    return ConfigSettings(gemini_api_key_set=True, gemini_api_key_preview=mask_value(plain))


@router.get("", response_model=SettingsResponse)
def get_settings(conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT store, enabled FROM store_toggles")
    rows = cursor.fetchall()

    return SettingsResponse(
        stores=[row_to_dict(row) for row in rows],
        config=_get_config(conn),
    )


@router.patch("", response_model=SettingsResponse)
def patch_settings(payload: SettingsPatch, conn=Depends(get_db)):
    cursor = conn.cursor()

    if payload.stores:
        for store, enabled in payload.stores.items():
            cursor.execute(
                "UPDATE store_toggles SET enabled = ? WHERE store = ?",
                (enabled, store),
            )

    if payload.gemini_api_key is not None:
        if payload.gemini_api_key == "":
            # Empty string = explicit clear
            cursor.execute("UPDATE settings SET gemini_api_key = NULL WHERE id = 1")
        else:
            try:
                encrypted = encrypt_value(payload.gemini_api_key)
            except CryptoConfigError as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc
            cursor.execute(
                "UPDATE settings SET gemini_api_key = ? WHERE id = 1",
                (encrypted,),
            )

    conn.commit()

    cursor.execute("SELECT store, enabled FROM store_toggles")
    rows = cursor.fetchall()

    return SettingsResponse(
        stores=[row_to_dict(row) for row in rows],
        config=_get_config(conn),
    )