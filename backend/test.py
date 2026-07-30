import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1532111359448453141/vbLl4VwC27KPCjWI5XRhLilugqkJg6qq9tBom5XE5P3iSz7W2PUEJDPtWraTDCkgkCwT"


def send_discord_message(content: str, webhook_url: Optional[str] = None) -> None:
    """Sender en enkel tekstmelding til en Discord-webhook."""
    url = webhook_url or DISCORD_WEBHOOK_URL
    if not url:
        raise ValueError(
            "Mangler DISCORD_WEBHOOK_URL. Sett den i .env eller send inn webhook_url=..."
        )

    # Discord har en hard grense på 2000 tegn per melding
    if len(content) > 2000:
        content = content[:1990] + "\n…(kuttet)"

    response = requests.post(url, json={"content": content})
    response.raise_for_status()


def send_discord_embed(title: str, description: str, fields: list[dict], webhook_url: Optional[str] = None) -> None:
    """
    Sender en rikere melding som et Discord "embed" (pen boks med tittel/felter),
    i stedet for ren tekst. fields er en liste av {"name": ..., "value": ..., "inline": bool}.
    """
    url = webhook_url or DISCORD_WEBHOOK_URL
    if not url:
        raise ValueError(
            "Mangler DISCORD_WEBHOOK_URL. Sett den i .env eller send inn webhook_url=..."
        )

    # Discord embeds har egne grenser: 25 felter maks, 1024 tegn per felt-verdi.
    # Discord avviser også felter med tom name eller value, så vi sikrer en fallback.
    trimmed_fields = []
    for f in fields[:25]:
        name = (f.get("name") or "Ukjent").strip() or "Ukjent"
        value = (f.get("value") or "").strip() or "—"
        if len(value) > 1024:
            value = value[:1000] + "\n…(kuttet)"
        trimmed_fields.append({
            "name": name,
            "value": value,
            "inline": f.get("inline", False),
        })

    payload = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": 0x8A5A3D,  # samme rustfarge som frontend-aksenten
                "fields": trimmed_fields,
            }
        ]
    }

    response = requests.post(url, json=payload)
    if not response.ok:
        # Discord returnerer ofte en nyttig feilmelding i body ved 400
        print(f"Discord avviste embed ({response.status_code}): {response.text}")
    response.raise_for_status()


def format_price(value: Optional[float]) -> str:
    if value is None:
        return "Ingen pris oppgitt"
    return f"{value:.2f} kr"


def notify_matching_products(products: list[dict], watch_term: str) -> None:
    """
    Sender et varsel om produkter som matcher et overvåket søkeord (f.eks. "ris", "mel").
    Hvert element i products forventes å ha: product_name, store, current_price,
    old_price, discount_percent, package_size.
    """
    if not products:
        return

    fields = []
    for p in products:
        price_line = format_price(p.get("current_price"))
        if p.get("old_price"):
            price_line += f" ~~{format_price(p['old_price'])}~~"
        elif p.get("discount_percent"):
            price_line += f" (-{p['discount_percent']:.0f}%)"

        fields.append({
            "name": f"{p.get('product_name', 'Ukjent')} · {p.get('store', '')}",
            "value": f"{price_line}\n{p.get('package_size') or ''}".strip(),
            "inline": True,
        })

    send_discord_embed(
        title=f"🔔 Tilbud på \"{watch_term}\"",
        description=f"Fant {len(products)} treff denne uken:",
        fields=fields,
    )


if __name__ == "__main__":
    # --- Dummy data for testing all functions in this file ---

    dummy_products = [
        {
            "product_name": "BASMATIRIS",
            "store": "kiwi",
            "current_price": 24.90,
            "old_price": 34.90,
            "discount_percent": None,
            "package_size": "1 kg",
        },
        {
            "product_name": "RISGRYN",
            "store": "coopExtra",
            "current_price": None,
            "old_price": None,
            "discount_percent": 20,
            "package_size": "500 g",
        },
        {
            "product_name": "HVETEMEL",
            "store": "rema",
            "current_price": 15.90,
            "old_price": None,
            "discount_percent": None,
            "package_size": "2 kg",
        },
    ]

    print("1) Tester send_discord_message …")
    try:
        send_discord_message("✅ Tilbudsradaren er koblet til Discord! (testmelding fra send_discord_message)")
        print("   OK")
    except Exception as e:
        print(f"   FEILET: {e}")

    print("2) Tester send_discord_embed …")
    try:
        send_discord_embed(
            title="🧪 Testvarsel",
            description="Dette er en testmelding fra send_discord_embed.",
            fields=[
                {"name": "Testfelt 1", "value": "Verdi 1", "inline": True},
                {"name": "Testfelt 2", "value": "Verdi 2", "inline": True},
            ],
        )
        print("   OK")
    except Exception as e:
        print(f"   FEILET: {e}")

    print("3) Tester format_price …")
    print("   format_price(24.9)  ->", format_price(24.9))
    print("   format_price(None)  ->", format_price(None))

    print("4) Tester notify_matching_products (ris) …")
    try:
        notify_matching_products(dummy_products[:2], watch_term="ris")
        print("   OK")
    except Exception as e:
        print(f"   FEILET: {e}")

    print("5) Tester notify_matching_products (mel) …")
    try:
        notify_matching_products(dummy_products[2:], watch_term="mel")
        print("   OK")
    except Exception as e:
        print(f"   FEILET: {e}")

    print("Alle funksjoner kjørt. Sjekk Discord-kanalen din.")