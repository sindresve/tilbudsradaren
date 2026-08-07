"""
Tilbudsradar AI-chat – rettet matching mot produkt-spesifikke søkeord
"""
import itertools
import json
import re
import sys
import threading
import time
from pathlib import Path

import ollama

from db.database import get_connection, DB_PATH

MODEL_NAME = "qwen2.5:7b"
TEMPERATURE = 0.5

BASE_DIR = Path(__file__).parent
KATEGORIER_PATH = BASE_DIR / "categories.json"
SMAK_PATH = BASE_DIR / "combinations.json"
RECIPES_PATH = BASE_DIR / "recipes.json"

CALL_PATTERN = re.compile(r"CALL_HENT_TILBUD\((.*?)\)", re.DOTALL)

TENKE_MELDINGER = ["Tenker", "Jobber med svaret"]
DATABASE_MELDINGER = ["Sjekker databasen", "Henter tilbud", "Leter gjennom ukens varer"]


class Spinner:
    def __init__(self, meldinger: list[str], intervall: float = 0.4):
        self._meldinger = meldinger
        self._intervall = intervall
        self._stop_event = threading.Event()
        self._thread = None

    def _run(self):
        prikker_syklus = itertools.cycle([".", "..", "..."])
        meldings_syklus = itertools.cycle(self._meldinger)
        gjeldende_melding = next(meldings_syklus)
        forrige_lengde = 0
        skift_teller = 0
        BYTT_MELDING_HVER = 5
        while not self._stop_event.is_set():
            prikker = next(prikker_syklus)
            tekst = f"  {gjeldende_melding}{prikker}"
            utfylling = " " * max(0, forrige_lengde - len(tekst))
            print(f"\r{tekst}{utfylling}", end="", flush=True)
            forrige_lengde = len(tekst)
            skift_teller += 1
            if skift_teller >= BYTT_MELDING_HVER:
                skift_teller = 0
                gjeldende_melding = next(meldings_syklus)
            self._stop_event.wait(self._intervall)
        print(f"\r{' ' * forrige_lengde}\r", end="", flush=True)

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"ADVARSEL: Fant ikke '{path}'. Fortsetter uten denne dataen.")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


KATEGORIER: dict = load_json(KATEGORIER_PATH)
SMAK: dict = load_json(SMAK_PATH)

NØKKELORD_TIL_KATEGORI: dict[str, str] = {}
for kategori, nøkkelord_liste in KATEGORIER.items():
    for nøkkelord in nøkkelord_liste:
        NØKKELORD_TIL_KATEGORI[nøkkelord.lower()] = kategori


def kategoriser_terms(terms: list[str]) -> str | None:
    for term in terms:
        kat = NØKKELORD_TIL_KATEGORI.get(term.lower())
        if kat:
            return kat
    return None


def load_recipes(path: Path) -> list[dict]:
    data = load_json(path)
    return data.get("recipes", [])

def match_recipe_to_offers(
    recipes: list[dict],
    offers: list[dict],
    categories: dict[str, list[str]]   
) -> list[tuple[int, dict, dict[str, str]]]:
    """
    Matcher oppskrifter mot tilbudsvarer KUN basert på produktets egne søkeord.
    """
    offer_pool = []
    for offer in offers:
        terms = set(t.lower() for t in offer.get("terms", []))
        if terms:
            offer_pool.append((offer["product_name"], terms))

    scored = []

    for recipe in recipes:
        required = [r.lower() for r in recipe.get("required", [])]
        optional = [o.lower() for o in recipe.get("optional", [])]
        proteins = [p.lower() for p in recipe.get("proteins", [])]

        used = set()
        required_matched = 0
        all_required = True

        for req in required:
            found = False
            for idx, (_, keywords) in enumerate(offer_pool):
                if idx in used:
                    continue
                if req in keywords:          
                    used.add(idx)
                    required_matched += 1
                    found = True
                    break
            if not found:
                all_required = False
                break

        if not all_required:
            continue

        optional_matched = 0
        for opt in optional:
            if any(opt in kw for _, kw in offer_pool):
                optional_matched += 1

        protein_found = any(
            any(prot in kw for prot in proteins)
            for _, kw in offer_pool
        )

        score = required_matched * 10 + optional_matched * 3 + (5 if protein_found else 0)

        mapping = {}
        for req in required:
            for name, kw in offer_pool:
                if req in kw and req not in mapping:
                    mapping[req] = name
                    break
        for opt in optional:
            for name, kw in offer_pool:
                if opt in kw and opt not in mapping:
                    mapping[opt] = name
                    break

        scored.append((score, recipe, mapping))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def format_top_recipes_as_template(scored_recipes: list, top_n: int = 5) -> str:
    lines = []
    for i, (score, recipe, mapping) in enumerate(scored_recipes[:top_n], 1):
        produktnavn = [v for _, v in sorted(mapping.items())]
        navn_str = " + ".join(produktnavn)
        lines.append(f"{i}. **{recipe['name']}** - Brukes: {navn_str}. [beskrivelse]")
    return "\n".join(lines)


SYSTEM_PROMPT_TEMPLATE = """\
Du er en hjelpsom norsk assistent i appen "Tilbudsradar".
Du hjelper brukeren med å finne mat-ideer basert på hva som er på tilbud.

Når du mottar en liste med ferdige oppskrifter, skal du:
- Presentere ALLE oppskriftene nøyaktig som de står.
- Kun erstatte [beskrivelse] med en egen kort, fristende setning (maks 20 ord).
- IKKE endre oppskriftsnavn, produktnavn eller format.
- IKKE finne på nye retter eller ingredienser.
- Hvis listen er tom, si ifra uten å dikte opp noe selv.

Du har tilgang til funksjonen hent_tilbud via CALL_HENT_TILBUD(...) på egen linje.
Vær vennlig og kortfattet."""


def bygg_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE


OPENING_MESSAGE = (
    "Hei! Jeg er assistenten din i Tilbudsradar. Jeg kan hjelpe deg med mat-ideer "
    "basert på det som er på tilbud i butikkene denne uka - bare spør! "
    "F.eks. \"hva bør jeg lage til middag i kveld?\" eller \"gi meg noen ideer for uka\"."
)

def hent_tilbud(search_term: str = "", store: str = "") -> list[dict]:
    if not DB_PATH.exists():
        return [{"error": f"Fant ikke databasefil: {DB_PATH.resolve()}"}]

    conn = get_connection()
    cur = conn.cursor()

    where_clauses = [
        "p.category = 'mat'",
        "NOT (p.current_price IS NOT NULL AND p.current_price != 0.0 "
        "     AND p.old_price IS NOT NULL AND p.old_price != 0.0 "
        "     AND p.current_price = p.old_price)",
        "NOT (p.current_price IS NOT NULL AND p.current_price != 0.0 "
        "     AND (p.old_price IS NULL OR p.old_price = 0.0) "
        "     AND (p.discount_percent IS NULL OR p.discount_percent = 0.0))",
        "NOT ((p.current_price IS NULL OR p.current_price = 0.0) "
        "     AND (p.old_price IS NULL OR p.old_price = 0.0) "
        "     AND (p.discount_percent IS NULL OR p.discount_percent = 0.0))",
    ]
    params: list = []

    if store:
        where_clauses.append("c.store = ?")
        params.append(store)

    if search_term:
        where_clauses.append(
            "(p.product_name LIKE ? OR EXISTS ("
            "  SELECT 1 FROM product_search_terms st "
            "  WHERE st.product_id = p.id AND st.term LIKE ?"
            "))"
        )
        params.append(f"%{search_term}%")
        params.append(f"%{search_term}%")

    where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
        WITH latest_catalog AS (
            SELECT store, MAX(year * 100 + week) AS max_yw
            FROM catalogs
            GROUP BY store
        )
        SELECT
            p.id AS product_id,
            p.product_name,
            CASE
                WHEN p.discount_percent IS NOT NULL AND p.discount_percent != 0.0
                    THEN p.discount_percent
                WHEN p.old_price IS NOT NULL AND p.old_price != 0.0
                     AND p.current_price IS NOT NULL
                    THEN ROUND(
                        (p.old_price - p.current_price) * 100.0 / p.old_price, 1
                    )
                ELSE NULL
            END AS final_discount_percent
        FROM products p
        JOIN catalogs c ON c.id = p.catalog_id
        JOIN latest_catalog lc
            ON lc.store = c.store AND lc.max_yw = (c.year * 100 + c.week)
        {where_sql}
        ORDER BY final_discount_percent DESC
    """

    cur.execute(query, params)
    rows = [dict(row) for row in cur.fetchall()]

    if not rows:
        conn.close()
        return [{"info": "Ingen produkter funnet for dette søket."}]

    product_ids = [r["product_id"] for r in rows]
    placeholders = ",".join("?" for _ in product_ids)
    cur.execute(
        f"SELECT product_id, term FROM product_search_terms WHERE product_id IN ({placeholders})",
        product_ids,
    )
    terms_per_produkt: dict[int, list[str]] = {}
    for row in cur.fetchall():
        terms_per_produkt.setdefault(row["product_id"], []).append(row["term"])

    conn.close()

    resultat = []
    for r in rows:
        terms = terms_per_produkt.get(r["product_id"], [])
        kategori = kategoriser_terms(terms)
        resultat.append({
            "product_name": r["product_name"],
            "final_discount_percent": r["final_discount_percent"],
            "category": kategori or "ukategorisert",
            "terms": terms,                    
        })

    return resultat


AVAILABLE_FUNCTIONS = {"hent_tilbud": hent_tilbud}


def parse_call_args(raw_args: str) -> dict:
    args = {}
    if not raw_args.strip():
        return args
    for match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', raw_args):
        key, value = match.group(1), match.group(2)
        args[key] = value
    return args


def strip_call_from_text(text: str) -> str:
    return CALL_PATTERN.sub("", text).strip()


def extract_call(text: str):
    match = CALL_PATTERN.search(text)
    if not match:
        return None
    return "hent_tilbud", parse_call_args(match.group(1))


def stream_model_response(messages: list, print_prefix: str = "AI: ") -> str:
    full_text = ""
    buffer = ""
    printed_prefix = False
    call_started = False

    spinner = Spinner(TENKE_MELDINGER)
    spinner.start()
    spinner_stoppet = False

    def stopp_spinner_ved_behov():
        nonlocal spinner_stoppet
        if not spinner_stoppet:
            spinner.stop()
            spinner_stoppet = True

    stream = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        options={"num_ctx": 4096, "temperature": TEMPERATURE},
        stream=True,
    )

    try:
        for chunk in stream:
            piece = chunk["message"]["content"]
            if not piece:
                continue
            stopp_spinner_ved_behov()
            full_text += piece
            if call_started:
                continue
            buffer += piece
            call_idx = buffer.find("CALL_HENT_TILBUD(")
            if call_idx != -1:
                visible_part = buffer[:call_idx]
                if visible_part:
                    if not printed_prefix:
                        print(print_prefix, end="", flush=True)
                        printed_prefix = True
                    for ch in visible_part:
                        print(ch, end="", flush=True)
                        time.sleep(0.008)
                call_started = True
                buffer = ""
                continue
            safe_len = max(0, len(buffer) - 20)
            if safe_len > 0:
                safe_part = buffer[:safe_len]
                buffer = buffer[safe_len:]
                if not printed_prefix:
                    print(print_prefix, end="", flush=True)
                    printed_prefix = True
                for ch in safe_part:
                    print(ch, end="", flush=True)
                    time.sleep(0.008)
        if buffer and not call_started:
            if not printed_prefix:
                print(print_prefix, end="", flush=True)
                printed_prefix = True
            for ch in buffer:
                print(ch, end="", flush=True)
                time.sleep(0.008)
    finally:
        stopp_spinner_ved_behov()

    if printed_prefix:
        print()
    return full_text


def main():
    print("=" * 60)
    print("  Tilbudsradar AI-chat")
    print(f"  Modell: {MODEL_NAME}")
    print("  Skriv 'exit' eller 'quit' for å avslutte.")
    print("=" * 60)

    system_prompt = bygg_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": OPENING_MESSAGE},
    ]
    print(f"\nAI: {OPENING_MESSAGE}")

    while True:
        try:
            user_input = input("\nDu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nHa det!")
            break

        if user_input.lower() in ("exit", "quit", "avslutt"):
            print("Ha det!")
            break

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        print()
        raw_reply = stream_model_response(messages)
        messages.append({"role": "assistant", "content": raw_reply})

        call = extract_call(raw_reply)
        if call:
            func_name, func_args = call
            func = AVAILABLE_FUNCTIONS.get(func_name)

            with Spinner(DATABASE_MELDINGER):
                if func is None:
                    result = {"error": f"Ukjent funksjon: {func_name}"}
                else:
                    try:
                        result = func(**func_args)
                    except Exception as e:
                        result = {"error": str(e)}

            if isinstance(result, list) and len(result) > 0 and "product_name" in result[0]:
                recipes = load_recipes(RECIPES_PATH)
                scored = match_recipe_to_offers(recipes, result, KATEGORIER)
                top_matches = scored[:5]

                if not top_matches:
                    recipe_info = "Beklager, jeg fant ingen oppskrifter som passer med ukens tilbud akkurat nå."
                else:
                    template = format_top_recipes_as_template(top_matches, top_n=5)
                    recipe_info = (
                        "Her er ferdig sammensatte middagsoppskrifter basert på ukens tilbud.\n"
                        "For hver oppskrift under skal du KUN erstatte ordet [beskrivelse] "
                        "med en kort, fristende setning (maks 20 ord). Alt annet – navn og "
                        "produktnavn – skal være HELT uendret.\n\n"
                        + template
                        + "\n\n"
                        "Gjør dette for alle oppskriftene. Ikke legg til egne retter."
                    )
            else:
                recipe_info = f"Systemet returnerte: {json.dumps(result, ensure_ascii=False)}\n\n" \
                              "Bruk denne informasjonen til å hjelpe brukeren."

            messages.append({
                "role": "user",
                "content": recipe_info,
            })

            print()
            followup_raw = stream_model_response(messages)
            messages.append({"role": "assistant", "content": followup_raw})


if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"ADVARSEL: Fant ikke '{DB_PATH}' i denne mappa.")
        print("Legg scriptet i samme mappe som tilbudsradar.db, eller endre DB_PATH.\n")
    main()