from typing import Optional
import requests
import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from html import escape


def send_email(content: str, title: str, smtp_settings: dict[str, str]):
    try:
        SMTP_HOST = smtp_settings["host"]
        SMTP_PORT = smtp_settings["port"]

        USERNAME = smtp_settings["username"]
        PASSWORD = smtp_settings["password"]

        msg = EmailMessage()
        msg["Subject"] = title
        msg["From"] = "Tilbuds Radaren"
        msg["To"] = smtp_settings["email_to"]
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        msg.set_content(content)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(USERNAME, PASSWORD)
            smtp.send_message(msg)

    except KeyError as e:
        raise RuntimeError(f"Missing SMTP setting: {e.args[0]}") from e

    except smtplib.SMTPException as e:
        raise RuntimeError(f"Failed to send email: {e}") from e

    except OSError as e:
        raise RuntimeError(f"Failed to connect to SMTP server: {e}") from e

    except Exception as e:
        raise RuntimeError(f"Unexpected error while sending email: {e}") from e


def send_discord_message(content: str, webhook_url: Optional[str] = None) -> None:
    """Sends a simple text message to a Discord webhook."""

    if not webhook_url:
        raise ValueError(
            "Missing discord webhook url"
        )

    if len(content) > 2000:
        content = content[:1985] + "\n…(forkortet)"

    response = requests.post(webhook_url, json={"content": content})
    response.raise_for_status()


def send_discord_embed(title: str, description: str, fields: list[dict], webhook_url: Optional[str] = None) -> None:
    """
    Sends a richer message as a Discord "embed" (a styled box with title/fields)
    instead of plain text. Each field is a dict of {"name": ..., "value": ..., "inline": bool}.
    """

    if not webhook_url:
        raise ValueError(
            "Missing discord webhook url"
        )

    trimmed_fields = []
    for f in fields[:25]:  # Discord allows max 25 fields per embed
        name = (f.get("name") or "Ukjent").strip() or "Ukjent"
        value = (f.get("value") or "").strip() or "—"
        if len(value) > 1024:  # Discord field value cap
            value = value[:1000] + "\n…(forkortet)"
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


def notify_matching_products(products: list[dict], watch_term: str, webhook_url: str) -> None:
    """
    Sends a notification about products matching a watched search term (e.g. "rice", "flour").
    Each element in `products` is expected to have: name, store, current_price,
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
            "name": f"{p.get('name', 'Ukjent')} · {p.get('store', '')}",
            "value": f"{price_line}\n{p.get('package_size') or ''}".strip(),
            "inline": True,
        })

    send_discord_embed(
        title=f"🔔 Tilbud på \"{watch_term}\"",
        description=f"Fant {len(products)} treff denne uken:",
        fields=fields,
        webhook_url=webhook_url
    )

def _has_price(value: Optional[float]) -> bool:
    """True if a real, usable price was provided. Treats None AND 0.0 as
    'no price' — some feeds send 0.0 as a placeholder rather than an actual
    free price, and showing "0.00 kr" is more confusing than helpful."""
    return bool(value)


def group_products_by_keyword(products: list[dict]) -> dict[str, list[dict]]:
    """
    Groups a flat list of product dicts (each with a 'keyword' field) into
    {keyword: [products...]}, preserving first-seen keyword order.
    """
    grouped: dict[str, list[dict]] = {}
    for p in products:
        key = p.get("keyword", "Ukjent")
        grouped.setdefault(key, []).append(p)
    return grouped


def _product_row_html(p: dict) -> str:
    """Renders a single product as an HTML table row."""
    name = escape(str(p.get("name", "Ukjent")))
    category = escape(str(p.get("category", "")))

    current = p.get("current_price")
    old = p.get("old_price")
    discount = p.get("discount_percent")

    if _has_price(current):
        price_html = escape(format_price(current))
        if _has_price(old) and old != current:
            price_html += f' <span style="color:#9a9a9a;text-decoration:line-through;font-size:13px;">{escape(format_price(old))}</span>'
        if discount:
            price_html += (
                f' <span style="color:#ffffff;background:#c0392b;border-radius:4px;'
                f'padding:1px 6px;font-size:12px;font-weight:600;margin-left:4px;">-{discount:.0f}%</span>'
            )
    elif discount:
        # No prices given at all, only a discount percentage
        price_html = (
            f'<span style="color:#ffffff;background:#c0392b;border-radius:4px;'
            f'padding:2px 8px;font-size:13px;font-weight:600;">-{discount:.0f}%</span>'
        )
    else:
        price_html = escape(format_price(None))

    return f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;">
            <div style="font-weight:600;color:#2b2b2b;font-size:14px;">{name}</div>
            {f'<div style="color:#8a8a8a;font-size:12px;margin-top:2px;">{category}</div>' if category else ""}
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap;font-size:14px;color:#2b2b2b;">
            {price_html}
          </td>
        </tr>"""


def _watch_term_section_html(watch_term: str, products: list[dict]) -> str:
    """Renders one categorized section (a watch term + its matching products)."""
    term = escape(watch_term)
    rows = "".join(_product_row_html(p) for p in products)

    return f"""
    <tr>
      <td style="padding:24px 0 8px 0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="font-size:16px;font-weight:700;color:#8A5A3D;">
              🔔 {term}
            </td>
            <td style="text-align:right;font-size:12px;color:#9a9a9a;">
              {len(products)} treff
            </td>
          </tr>
        </table>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
               style="margin-top:8px;background:#ffffff;border:1px solid #eee;border-radius:8px;overflow:hidden;">
          {rows}
        </table>
      </td>
    </tr>"""


def build_deals_email_html(products_by_term: dict[str, list[dict]]) -> str:
    """
    Builds a full HTML email body summarizing deals across ALL watch terms,
    with one categorized section per term. Terms with no matching products
    are skipped.

    products_by_term: {watch_term: [product_dict, ...], ...}
    Accepts the 'keyword'-based product schema (name, category, current_price,
    old_price, discount_percent, keyword). If you have a flat list instead,
    call group_products_by_keyword() first.
    """
    sections = "".join(
        _watch_term_section_html(term, products)
        for term, products in products_by_term.items()
        if products
    )

    total_matches = sum(len(v) for v in products_by_term.values())
    total_terms = sum(1 for v in products_by_term.values() if v)

    if not sections:
        sections = """
    <tr>
      <td style="padding:24px 0;color:#8a8a8a;font-size:14px;">
        Ingen matchende tilbud funnet denne uken.
      </td>
    </tr>"""

    return f"""\
<html>
  <body style="margin:0;padding:0;background:#f4f2ef;font-family:Segoe UI, Arial, sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f2ef;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="600" cellpadding="0" cellspacing="0"
                 style="background:#faf9f7;border-radius:10px;overflow:hidden;">
            <tr>
              <td style="background:#8A5A3D;padding:20px 24px;">
                <div style="color:#ffffff;font-size:20px;font-weight:700;">TilbudsRadaren</div>
                <div style="color:#f0e2d8;font-size:13px;margin-top:2px;">
                  {total_matches} tilbud på tvers av {total_terms} overvåkede søkeord
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 24px 24px 24px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                  {sections}
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def send_deals_email(products, smtp_settings: dict[str, str]) -> None:
    """
    Sends ONE email covering all watch terms, each rendered as its own
    categorized section, instead of one message per term (as the Discord
    version does).

    `products` can be either:
      - a flat list of product dicts, each with a 'keyword' field, or
      - an already-grouped dict of {watch_term: [product_dict, ...]}
    """
    if isinstance(products, list):
        products_by_term = group_products_by_keyword(products)
    else:
        products_by_term = products

    total_matches = sum(len(v) for v in products_by_term.values())
    if total_matches == 0:
        return  # nothing to report

    html_body = build_deals_email_html(products_by_term)

    try:
        SMTP_HOST = smtp_settings["host"]
        SMTP_PORT = smtp_settings["port"]
        USERNAME = smtp_settings["username"]
        PASSWORD = smtp_settings["password"]

        msg = EmailMessage()
        msg["Subject"] = f"🔔 {total_matches} nye tilbud funnet"
        msg["From"] = "Tilbuds Radaren"
        msg["To"] = smtp_settings["email_to"]
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        plain_lines = []
        for term, products in products_by_term.items():
            if not products:
                continue
            plain_lines.append(f"\n{term} ({len(products)} treff):")
            for p in products:
                current = p.get("current_price")
                if current is not None:
                    price_str = format_price(current)
                elif p.get("discount_percent"):
                    price_str = f"-{p['discount_percent']:.0f}%"
                else:
                    price_str = format_price(None)
                plain_lines.append(f"  - {p.get('name', 'Ukjent')}: {price_str}")
        msg.set_content("\n".join(plain_lines) if plain_lines else "Ingen matchende tilbud funnet denne uken.")

        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(USERNAME, PASSWORD)
            smtp.send_message(msg)

    except KeyError as e:
        raise RuntimeError(f"Missing SMTP setting: {e.args[0]}") from e

    except smtplib.SMTPException as e:
        raise RuntimeError(f"Failed to send email: {e}") from e

    except OSError as e:
        raise RuntimeError(f"Failed to connect to SMTP server: {e}") from e

    except Exception as e:
        raise RuntimeError(f"Unexpected error while sending email: {e}") from e