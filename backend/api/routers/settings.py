from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..utils.crypto_utils import CryptoConfigError, encrypt_value, mask_value
from ..utils.deps import get_db
from ..utils.gemini_key import get_gemini_api_key
from ..utils.utils import row_to_dict
from api.utils.notifications import send_discord_message, send_email

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
    email_to: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    webhook_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_enabled: bool = False
    weekly_budget: Optional[float] = None

class SettingsResponse(BaseModel):
    stores: List[StoreToggle]
    allergies: List[AllergyToggle]
    staples: List[str]
    config: ConfigSettings
    email_to: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    webhook_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_enabled: bool = False
    weekly_budget: Optional[float] = None

class SettingsPatch(BaseModel):
    stores: Optional[Dict[str, bool]] = None
    allergies: Optional[Dict[str, bool]] = None
    staples: Optional[List[str]] = None
    gemini_api_key: Optional[str] = None
    postal_code: Optional[str] = None
    email_to: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    webhook_enabled: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_enabled: Optional[bool] = None
    weekly_budget: Optional[float] = None

def _get_config(conn) -> ConfigSettings:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT gemini_api_key, postal_code, email_to, discord_webhook_url, webhook_enabled, "
        "smtp_host, smtp_port, smtp_username, smtp_enabled, weekly_budget FROM settings WHERE id = 1"
    )
    row = cursor.fetchone()
    has_stored_value = bool(row and row["gemini_api_key"])
    postal_code = row["postal_code"] if row else None
    email_to = row["email_to"] if row else None
    discord_webhook_url = row["discord_webhook_url"] if row else None
    webhook_enabled = bool(row["webhook_enabled"]) if row else False
    smtp_host = row["smtp_host"] if row else None
    smtp_port = row["smtp_port"] if row else None
    smtp_username = row["smtp_username"] if row else None
    smtp_enabled = bool(row["smtp_enabled"]) if row else False
    weekly_budget = row["weekly_budget"] if row else None

    base = dict(
        postal_code=postal_code,
        email_to=email_to,
        discord_webhook_url=discord_webhook_url,
        webhook_enabled=webhook_enabled,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_enabled=smtp_enabled,
        weekly_budget=weekly_budget,
    )

    if not has_stored_value:
        return ConfigSettings(gemini_api_key_set=False, gemini_api_key_preview=None, **base)

    plain = get_gemini_api_key()
    if plain is None:
        return ConfigSettings(gemini_api_key_set=True, gemini_api_key_preview="••• (kan ikke leses)", **base)

    return ConfigSettings(gemini_api_key_set=True, gemini_api_key_preview=mask_value(plain), **base)


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

    print(payload)

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

    if payload.email_to is not None:
        cursor.execute(
            "UPDATE settings SET email_to = ? WHERE id = 1",
            (payload.email_to,),
        )

    if payload.discord_webhook_url is not None:
        cursor.execute("UPDATE settings SET discord_webhook_url = ? WHERE id = 1", (payload.discord_webhook_url,))

    if payload.webhook_enabled is not None:
        cursor.execute("UPDATE settings SET webhook_enabled = ? WHERE id = 1", (payload.webhook_enabled,))

    if payload.smtp_host is not None:
        cursor.execute("UPDATE settings SET smtp_host = ? WHERE id = 1", (payload.smtp_host,))

    if payload.smtp_port is not None:
        cursor.execute("UPDATE settings SET smtp_port = ? WHERE id = 1", (payload.smtp_port,))

    if payload.smtp_username is not None:
        cursor.execute("UPDATE settings SET smtp_username = ? WHERE id = 1", (payload.smtp_username,))

    if payload.smtp_password is not None:
        cursor.execute("UPDATE settings SET smtp_password = ? WHERE id = 1", (payload.smtp_password,))

    if payload.smtp_enabled is not None:
        cursor.execute("UPDATE settings SET smtp_enabled = ? WHERE id = 1", (payload.smtp_enabled,))

    if payload.weekly_budget is not None:
        cursor.execute("UPDATE settings SET weekly_budget = ? WHERE id = 1", (payload.weekly_budget,))

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

def send_discord_test(webhook_url):
    send_discord_message("Dette er en test melding!", webhook_url)

def send_email_test(smtp_settings: dict[str, str]):
    send_email("Dette er en test mail!", "Test", smtp_settings)

class TestNotificationRequest(BaseModel):
    channel: str  # "email" or "discord"


@router.post("/test-notification")
def test_notification(payload: TestNotificationRequest, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT discord_webhook_url, smtp_host, smtp_port, smtp_username, smtp_password, email_to "
        "FROM settings WHERE id = 1"
    )
    row = cursor.fetchone()
    smtp_settings = {"host": row["smtp_host"], "port": row["smtp_port"], "username": row["smtp_username"], "password": row["smtp_password"], "email_to": row["email_to"]}

    if payload.channel == "discord":
        if not row or not row["discord_webhook_url"]:
            raise HTTPException(status_code=400, detail="Discord-webhook er ikke konfigurert")
        try:
            send_discord_test(row["discord_webhook_url"])
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Klarte ikke å sende til Discord: {exc}") from exc

    elif payload.channel == "email":
        if not row or not row["smtp_host"] or not row["email_to"]:
            raise HTTPException(status_code=400, detail="SMTP eller mottaker-e-post er ikke konfigurert")
        try:
            send_email_test(smtp_settings)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Klarte ikke å sende e-post: {exc}") from exc

    else:
        raise HTTPException(status_code=400, detail="Ukjent kanal")

    return {"success": True}