import os
import json
import mimetypes
from pathlib import Path
from typing import Optional

from utils import get_current_datetime

from google import genai
from google.genai import types


PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Produktets navn slik det står skrevet, f.eks. 'BROKKOLI'"
                    },
                    "brand": {
                        "type": "string",
                        "description": "Merkevare/produsent, f.eks. 'BAMA', 'REMA 1000', 'Barilla', 'Zalo', 'Colgate'. Tom streng hvis ukjent."
                    },
                    "category": {
                        "type": "string",
                        "enum": ["mat", "drikke", "hygiene", "husholdning", "annet"],
                        "description": "Overordnet kategori. 'mat' = matvarer/ferskvarer, 'drikke' = drikkevarer, 'hygiene' = personlig pleie (tannkrem, såpe, papir), 'husholdning' = rengjøring/vaskemidler/oppbevaring/batterier/lyspærer, 'annet' = passer ikke i de andre."
                    },
                    "current_price": {
                        "type": "number",
                        "description": "Nåværende/tilbudspris i kr, f.eks. 19.90"
                    },
                    "old_price": {
                        "type": "number",
                        "description": "Opprinnelig pris før tilbud (f.eks. 'FØR 74,90' -> 74.90). Null hvis ikke oppgitt."
                    },
                    "price_per_kg": {
                        "type": "number",
                        "description": "Pris per kg eller liter hvis oppgitt, f.eks. 174.75. Null hvis ikke oppgitt."
                    },
                    "unit_type": {
                        "type": "string",
                        "description": "Enhet for price_per_kg/pris, f.eks. 'kg', 'l', 'stk'. Tom streng hvis ikke relevant."
                    },
                    "package_size": {
                        "type": "string",
                        "description": "Pakningsstørrelse, f.eks. '400 g', '330 ml', '8 stk'. Tom streng hvis ikke oppgitt."
                    }
                },
                "required": ["product_name", "current_price", "category"]
            }
        }
    },
    "required": ["products"]
}


SYSTEM_PROMPT = """Du analyserer bilder fra norske tilbudsaviser (f.eks. REMA 1000, Kiwi, Coop Extra, Europris).

Din oppgave er å hente ut ALLE produkter som er relevante for en student sin husholdning, og
strukturere dem som JSON. Dette er BREDERE enn bare matvarer - inkluder også hygiene- og
husholdningsprodukter, men IKKE alt en butikk som Europris selger.

TA MED som produkter (relevant for studenthusholdning):
- Mat og ferskvarer: kjøtt, fisk, ost, grønt, frukt, brød, pasta, hermetikk, frossenmat
- Drikke: brus, juice, kaffe, te, vann
- Hygiene/personlig pleie: tannkrem, såpe, shampoo, dopapir, bind/tamponger, barberhøvler
- Husholdning: vaskemidler, oppvaskmiddel, søppelposer, kjøkkenpapir, lyspærer, batterier,
  enkel oppbevaring (bokser, permer for kjøkken/bad)

IKKE ta med (selv om det har en pris i annonsen):
- Klær, sko, sesongvarer (hagemøbler, grillutstyr, julepynt, campingutstyr)
- Elektronikk, verktøy, bilrekvisita
- Leker, bøker, interiør/dekorasjon, gaveartikler
- Overskrifter/kampanjenavn som "Familiemiddag under 200 lappen", "Smaken av sommeridyll"
- "Sluttsummen" / "Makspris" (dette er summen av alle produktene i en oppskrift, ikke et eget produkt)
- "Skann for oppskrift" / QR-kode-tekst
- "TIPS!" bokser med matlagingstips
- "Raskt & enkelt", "Porsjoner", ikoner/badges
- "Med forbehold om prisendringer" / disclaimer-tekst
- "Nyt Norge"-merker og lignende badges (dette er IKKE et produkt)
- Rene dekor-elementer

Hvis du er usikker på om noe er relevant for en studenthusholdning (f.eks. et grensetilfelle
som lommelykt eller tape), ta det heller MED og kategoriser det som "annet" enn å utelate det.

For hvert produkt, hent ut:
- product_name: navnet på produktet (store bokstaver som i annonsen er ok)
- brand: merkevare hvis synlig (f.eks. BAMA, REMA 1000, Barilla, Tine, Zalo, Colgate)
- category: "mat", "drikke", "hygiene", "husholdning", eller "annet"
- current_price: den store, fremhevede prisen (tilbudsprisen)
- old_price: prisen merket "FØR" hvis den finnes (den gamle/opprinnelige prisen)
- price_per_kg: "pr. kg" eller "pr. l" eller "pr. stk" prisen som ofte står i mindre tekst
- unit_type: enheten for price_per_kg (kg, l, stk)
- package_size: pakningsstørrelse (f.eks. "400 g", "330 ml")

Vær nøyaktig med tall - se godt etter komma/desimaler (norsk format bruker komma som desimaltegn,
konverter til punktum i JSON, f.eks. "19,90" -> 19.90).

Returner KUN gyldig JSON i henhold til det oppgitte skjemaet, ingen annen tekst."""


def _load_image_bytes(image_path: str) -> tuple[bytes, str]:
    """Leser en bildefil og returnerer (bytes, mime_type)."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Fant ikke bildet: {image_path}")

    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        mime_type = "image/jpeg"

    with open(path, "rb") as f:
        data = f.read()

    return data, mime_type


def extract_products_from_image(image_path: str, api_key: Optional[str] = None, model: str = "gemini-3.1-flash-lite", store: Optional[str] = None) -> list[dict]:

    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Mangler API-nøkkel. Sett miljøvariabelen GEMINI_API_KEY eller send inn api_key=..."
        )

    client = genai.Client(api_key=key)

    image_bytes, mime_type = _load_image_bytes(image_path)

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    types.Part.from_text(text="Hent ut alle relevante produkter fra dette tilbudsbildet."),
                ],
            )
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=PRODUCT_SCHEMA,
            temperature=0.1,  # lav temperatur = mer konsistent/faktabasert
        ),
    )

    result = json.loads(response.text)
    products = result.get("products", [])

    # Legg til hvilket bilde produktet kom fra (nyttig for feilsøking/sporing)
    for p in products:
        p["source_image"] = Path(image_path).name
        if store:
            p["store"] = store

    return products


def images_to_json(image_paths: list[str], output_path: str = "tilbud.json", api_key: Optional[str] = None, model: str = "gemini-3.1-flash-lite", store: Optional[str] = None, append: bool = False) -> list[dict]:
    all_products = []

    if append and Path(output_path).exists():
        with open(output_path, "r", encoding="utf-8") as f:
            all_products = json.load(f)

    for image_path in image_paths:
        print(f"Leser {image_path} ...")
        try:
            products = extract_products_from_image(
                image_path, api_key=api_key, model=model, store=store
            )
            print(f"  -> fant {len(products)} produkter")
            all_products.extend(products)
        except Exception as e:
            print(f"  FEIL ved lesing av {image_path}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"\nLagret {len(all_products)} produkter totalt til {output_path}")
    return all_products


def pdf_to_json(pdf_path: str, output_path: str = "tilbud.json", api_key: Optional[str] = None, model: str = "gemini-3.1-flash-lite", dpi: int = 200, store: Optional[str] = None, append: bool = False) -> list[dict]:
    import fitz  # PyMuPDF
    import tempfile

    doc = fitz.open(pdf_path)
    zoom = dpi / 72  # PyMuPDF regner i punkter (72 dpi som standard)
    matrix = fitz.Matrix(zoom, zoom)

    with tempfile.TemporaryDirectory() as tmp_dir:
        image_paths = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=matrix)
            img_path = Path(tmp_dir) / f"side_{i + 1}.jpg"
            pix.save(str(img_path))
            image_paths.append(str(img_path))

        doc.close()

        result = images_to_json(
            image_paths,
            output_path=output_path,
            api_key=api_key,
            model=model,
            store=store,
            append=append,
        )

    return result


def process_catalog(data_dir: str = "data", output_path: str = "tilbud.json", api_key: Optional[str] = None, model: str = "gemini-3.1-flash-lite", info: dict[str] = get_current_datetime()) -> list[dict]:
    base = Path(data_dir)
    all_products = []

    # --- REMA: mappe med bilder ---
    rema_dir = base / f"rema_{info['year']}_w{info['week']:02d}"
    if rema_dir.exists():
        rema_images = sorted(
            [str(p) for p in rema_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
        )
        if rema_images:
            print(f"--- REMA: {len(rema_images)} bilder ---")
            products = images_to_json(
                rema_images, output_path=output_path, api_key=api_key, model=model,
                store="rema", append=False,
            )
            all_products.extend(products)
    else:
        print(f"Ingen REMA-mappe funnet: {rema_dir}")

    # --- KIWI: én PDF ---
    kiwi_pdf = base / f"kiwi_{info['year']}_w{info['week']:02d}.pdf"
    if kiwi_pdf.exists():
        print(f"--- Kiwi: {kiwi_pdf} ---")
        products = pdf_to_json(
            str(kiwi_pdf), output_path=output_path, api_key=api_key, model=model,
            store="kiwi", append=True,
        )
        all_products = products  # append=True already merged inside the file
    else:
        print(f"Ingen Kiwi-PDF funnet: {kiwi_pdf}")

    # --- COOP EXTRA: én PDF ---
    coop_pdf = base / f"coopExtra_{info['year']}_w{info['week']:02d}.pdf"
    if coop_pdf.exists():
        print(f"--- Coop Extra: {coop_pdf} ---")
        products = pdf_to_json(
            str(coop_pdf), output_path=output_path, api_key=api_key, model=model,
            store="coopExtra", append=True,
        )
        all_products = products
    else:
        print(f"Ingen Coop-Extra-PDF funnet: {coop_pdf}")

    print(f"\nFerdig! Totalt {len(all_products)} produkter fra alle kjeder lagret i {output_path}")
    return all_products


if __name__ == "__main__":
    process_catalog(data_dir="data", output_path="tilbud.json")