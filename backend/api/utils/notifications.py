from typing import Optional
import requests

def send_discord_message(content: str, webhook_url: Optional[str] = None) -> None:
    """Sends a simple text message to a discord webhook"""

    if not webhook_url:
        raise ValueError(
            "Missing discord webhook url"
        )

    if len(content) > 2000:
        content = content[:1985] + "\n…(kuttet)"

    response = requests.post(url, json={"content": content})
    response.raise_for_status()
    
def send_discord_embed(title: str, description: str, fields: list[dict], webhook_url: Optional[str] = None) -> None:
    """
    Sends a richer message as a Discord "embed" (pretty box with title/fields),
    instead of clean text. Fields are a liste of {"name": ..., "value": ..., "inline": bool}.
    """

    if not webhook_url:
        raise ValueError(
            "Missing discord webhook url"
        )

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
                "color": 0x8A5A3D,
                "fields": trimmed_fields,
            }
        ]
    }

    response = requests.post(webhook_url, json=payload)
    if not response.ok:
        print(f"Discord rejected embed ({response.status_code}): {response.text}")
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