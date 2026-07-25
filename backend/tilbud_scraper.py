import os
import json
import mimetypes
from pathlib import Path
from typing import Optional

from pathlib import Path
from db.models import (create_catalog, save_products)

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
                        "description": "Nåværende/tilbudspris i kr, f.eks. 19.90. Null hvis kun en generell rabatt (f.eks. '20% på alt') er oppgitt uten konkret kronepris."
                    },
                    "old_price": {
                        "type": "number",
                        "description": "Opprinnelig pris før tilbud (f.eks. 'FØR 74,90' -> 74.90). Null hvis ikke oppgitt."
                    },
                    "discount_percent": {
                        "type": "number",
                        "description": "Prosent rabatt NÅR det kun er oppgitt en generell rabatt uten konkret kronepris, f.eks. '20% på alt i denne kategorien' eller '-30%' uten current_price. Null hvis en faktisk kronepris (current_price) er oppgitt i stedet."
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
                    },
                    "search_terms": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Liste med generiske søkeord brukeren sannsynligvis vil søke etter. F.eks. 'Jasminris 1 kg' -> ['ris','jasminris'], 'Helmelk 1L' -> ['melk','helmelk'], 'Hvetemel' -> ['mel','hvetemel'], 'Crispisalat' -> ['salat','crispisalat']. IKKE legg til ord som bare er delstrenger."
                    }
                },
                "required": ["product_name", "category"]
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
- current_price: den store, fremhevede prisen (tilbudsprisen), HVIS en konkret kronepris er oppgitt
- old_price: prisen merket "FØR" hvis den finnes (den gamle/opprinnelige prisen)
- discount_percent: HVIS produktet kun har en generell prosentrabatt uten konkret kronepris
  (f.eks. "20% på alt i denne seksjonen", "-30%" uten noen kronebeløp), sett current_price og
  old_price til null og fyll inn discount_percent i stedet. Bruk ALDRI discount_percent hvis
  current_price allerede er kjent.
- price_per_kg: "pr. kg" eller "pr. l" eller "pr. stk" prisen som ofte står i mindre tekst
- unit_type: enheten for price_per_kg (kg, l, stk)
- package_size: pakningsstørrelse (f.eks. "400 g", "330 ml")

- search_terms:
  Lag 2-8 søkeord som beskriver produktet.

  Regler:
  - Bruk substantiver folk faktisk søker etter.
  - Ikke bruk delstrenger.
  - Ikke bruk tilfeldige ord fra produktnavnet.
  - Ta med både generelle og spesifikke navn.

  Eksempler:

  "Jasminris"
  -> ["ris","jasminris"]

  "Basmatiris"
  -> ["ris","basmatiris"]

  "Hvetemel"
  -> ["mel","hvetemel"]

  "Sammalt hvetemel"
  -> ["mel","hvetemel","sammalt"]

  "Helmelk"
  -> ["melk","helmelk"]

  "Lettmelk"
  -> ["melk","lettmelk"]

  "Crispisalat"
  -> ["salat","crispisalat"]

  "Isbergsalat"
  -> ["salat","isbergsalat"]

  "Spaghetti"
  -> ["pasta","spaghetti"]

  "Penne"
  -> ["pasta","penne"]

  "Potetgull"
  -> ["chips","potetgull"]

  "Toalettpapir"
  -> ["toalettpapir","dopapir"]

  "Oppvaskmiddel"
  -> ["oppvaskmiddel"]

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


def images_to_products(image_paths, api_key=None, model="gemini-3.1-flash-lite", store=None):
    all_products=[]

    for image_path in image_paths:
        print(f"Leser {image_path}")
        products = extract_products_from_image(image_path, api_key, model, store)
        all_products.extend(products)

    return all_products


def pdf_to_json(pdf_path: str, api_key: Optional[str] = None, model: str = "gemini-3.1-flash-lite", dpi: int = 200, store: Optional[str] = None, append: bool = False) -> list[dict]:
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

        result = images_to_products(
            image_paths,
            api_key=api_key,
            model=model,
            store=store
        )

    return result




def process_catalog(data_dir="data", info=None):
    base = Path(data_dir)
    all_products = []

    type_map = {
        "rema": "image",
        "kiwi": "pdf",
        "coopExtra": "pdf",
    }

    for store, file_type in type_map.items():
        if file_type == "image":
            catalog_folder = (base / f"{store}_{info['year']}_w{info['week']:02d}")

            if not catalog_folder.exists():
                continue

            images = list(catalog_folder.glob("*.jpg"))

            if not images:
                continue

            products = images_to_products(images, store=store)

        elif file_type == "pdf":
            pdf_path = (base / f"{store}_{info['year']}_w{info['week']:02d}.pdf")

            if not pdf_path.exists():
                continue

            products = pdf_to_json(str(pdf_path), store=store)

        else:
            continue

        catalog_id = create_catalog(store, info)
        save_products(products, catalog_id)
        all_products.extend(products)

    print(f"Lagret {len(all_products)} produkter i SQLite")

    return all_products

if __name__ == "__main__":
    process_catalog(data_dir="data")