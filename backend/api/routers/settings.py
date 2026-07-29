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

class AllergyToggle(BaseModel):
    allergy: str
    enabled: bool

class StapleItem(BaseModel):
    name: str

class ConfigSettings(BaseModel):
    gemini_api_key_set: bool
    gemini_api_key_preview: Optional[str] = None
    postal_code: Optional[str] = None

class SettingsResponse(BaseModel):
    stores: List[StoreToggle]
    allergies: List[AllergyToggle]
    staples: List[str]
    config: ConfigSettings

class SettingsPatch(BaseModel):
    stores: Optional[Dict[str, bool]] = None
    allergies: Optional[Dict[str, bool]] = None
    staples: Optional[List[str]] = None
    gemini_api_key: Optional[str] = None
    postal_code: Optional[str] = None

def _get_config(conn) -> ConfigSettings:
    cursor = conn.cursor()
    cursor.execute("SELECT gemini_api_key, postal_code FROM settings WHERE id = 1")
    row = cursor.fetchone()
    has_stored_value = bool(row and row["gemini_api_key"])
    postal_code = row["postal_code"] if row else None

    if not has_stored_value:
        return ConfigSettings(
            gemini_api_key_set=False, 
            gemini_api_key_preview=None,
            postal_code=postal_code
        )

    plain = get_gemini_api_key() 
    if plain is None:
        return ConfigSettings(
            gemini_api_key_set=True, 
            gemini_api_key_preview="••• (kan ikke leses)",
            postal_code=postal_code
        )

    return ConfigSettings(
        gemini_api_key_set=True, 
        gemini_api_key_preview=mask_value(plain),
        postal_code=postal_code 
    )


@router.get("", response_model=SettingsResponse)
def get_settings(conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT store, enabled FROM store_toggles")
    store_rows = cursor.fetchall()

    cursor.execute("SELECT allergy, enabled FROM allergens")
    allergy_rows = cursor.fetchall()

    cursor.execute("SELECT name FROM staples ORDER BY name")
    staple_rows = cursor.fetchall()

    return SettingsResponse(
        stores=[row_to_dict(row) for row in store_rows],
        allergies=[row_to_dict(row) for row in allergy_rows],
        staples=[row["name"] for row in staple_rows],
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
            
    if payload.allergies:
        for allergy, enabled in payload.allergies.items():
            cursor.execute(
                "UPDATE allergens SET enabled = ? WHERE allergy = ?",
                (enabled, allergy),
            )

    if payload.staples is not None:
        cursor.execute("SELECT name FROM staples")
        existing = {row["name"] for row in cursor.fetchall()}
        incoming = set(payload.staples)

        to_add = incoming - existing
        to_remove = existing - incoming

        for name in to_add:
            cursor.execute("INSERT OR IGNORE INTO staples (name) VALUES (?)", (name,))

        for name in to_remove:
            cursor.execute("DELETE FROM staples WHERE name = ?", (name,))

    if payload.postal_code is not None:
        cursor.execute(
            "UPDATE settings SET postal_code = ? WHERE id = 1",
            (payload.postal_code,),
        )

    if payload.gemini_api_key is not None:
        if payload.gemini_api_key == "":
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
    store_rows = cursor.fetchall()

    cursor.execute("SELECT allergy, enabled FROM allergens")
    allergy_rows = cursor.fetchall()

    cursor.execute("SELECT name FROM staples ORDER BY name")
    staple_rows = cursor.fetchall()

    return SettingsResponse(
        stores=[row_to_dict(row) for row in store_rows],
        allergies=[row_to_dict(row) for row in allergy_rows],
        staples=[row["name"] for row in staple_rows],
        config=_get_config(conn),
    )