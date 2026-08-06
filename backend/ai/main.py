"""
Tilbudsradar AI-chat
---------------------
Terminalbasert chat mot en lokal Ollama-modell (qwen2.5:7b) med tilgang
til tilbudsdatabasen (tilbudsradar.db).

Enkel "manuell" function-calling: modellen svarer normalt til brukeren,
og kan deretter (i samme svar, på en egen linje) skrive
CALL_HENT_TILBUD(...) for å be om at vi henter tilbudsdata. Den linjen
vises ALDRI til brukeren - i stedet vises "(henter data fra databasen)"
mens vi kjører spørringen, og modellen får så sjansen til å svare på nytt
med dataen tilgjengelig.

NYTT i denne versjonen:
- Produkter kategoriseres (protein/grønnsak/karbo/meieri/krydder/...) ved
  hjelp av product_search_terms-tabellen + data/kategorier.json, slik at
  modellen slipper å gjette hva ting er og kan bruke kapasiteten sin på
  selve rettforslagene.
- Smakskombinasjoner (gode og dårlige par) hentes fra
  data/smakskombinasjoner.json, filtreres til det som faktisk er relevant
  for ukens tilbud, og limes inn i system-prompten.
- Few-shot-eksempel i system-prompten viser modellen nøyaktig hvilket
  format vi vil ha på svaret.
- Ollama-kallet bruker nå temperature=0.5 for mer konsistente forslag.
- Mens vi venter på svar (modellen "tenker", eller vi spør databasen) roterer
  vi nå en liten venteanimasjon i terminalen ("Tenker...", "Sjekker
  tilbudene...", osv.), i stedet for at det bare er stille i 20-30 sekunder.

Krav:
    pip install ollama

Kjør:
    python tilbudsradar_chat.py

Ollama må kjøre lokalt (ollama serve) og modellen må være hentet:
    ollama pull modell_navn

    Anbefalte modeller: qwen2.5:14b eller qwen2.5:7b (i værstefall qwen2.5:3b, men dette gir dårlige resultater)
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

DATA_DIR = Path(__file__).parent / "ai"
KATEGORIER_PATH = DATA_DIR / "categories.json"
SMAK_PATH = DATA_DIR / "combinations.json"

CALL_PATTERN = re.compile(r"CALL_HENT_TILBUD\((.*?)\)", re.DOTALL)


TENKE_MELDINGER = [
    "Tenker",
    "Vurderer tilbudene",
    "Fundérer på middagsforslag",
    "Kombinerer ingredienser",
]

DATABASE_MELDINGER = [
    "Sjekker databasen",
    "Henter tilbud",
    "Leter gjennom ukens varer",
]


class Spinner:
    """
    Enkel terminal-spinner som roterer gjennom en liste med meldinger
    (med "..." som animeres) i en bakgrunnstråd, helt til .stop() kalles.

    Brukes som context manager:
        with Spinner(TENKE_MELDINGER):
            ... noe som tar tid ...

    Når spinneren stoppes, viskes linjen ut igjen (\r + mellomrom + \r),
    slik at den ikke blir stående i terminalen sammen med det ekte svaret.
    """

    def __init__(self, meldinger: list[str], intervall: float = 0.4):
        self._meldinger = meldinger
        self._intervall = intervall
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

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
    """Gitt en liste med search_terms for et produkt, finn beste kategori-match."""
    for term in terms:
        kategori = NØKKELORD_TIL_KATEGORI.get(term.lower())
        if kategori:
            return kategori
    return None


SYSTEM_PROMPT_TEMPLATE = """Du er en hjelpsom norsk assistent i appen "Tilbudsradar".
Du hjelper brukeren med å finne mat-ideer basert på hva som er på tilbud i norske
dagligvarebutikker denne uka.

VIKTIG - din faktiske oppgave:
Når du får en liste med tilbudsvarer, skal du IKKE oppsummere eller beskrive dataen.
Din jobb er å FORESLÅ 3-5 KONKRETE MIDDAGSRETTER som bruker noen av ingrediensene
som er på tilbud. Tenk som en kokk: se på ingrediensene (og kategoriene deres -
protein, grønnsak, karbo osv.), og finn på ekte retter du kan lage med dem.

Regler for hvordan du skal oppføre deg:
- Svar alltid på norsk (bokmål), naturlig og uformelt, som en kompis som er flink på mat.
- Foreslå ALLTID konkrete rettnavn, aldri en oppsummering av rådata eller priser.
- Hold svarene relativt korte og lesbare i en chat.
- Ikke foreslå matretter med ingredienser du vet brukeren er allergisk mot, hvis dette er oppgitt.
- Du har IKKE tilgang til fullstendige oppskrifter ennå i denne versjonen.
- Ikke nevn priser, prosenter, butikknavn eller "rammepriser" med mindre brukeren spør
  spesifikt om pris - fokuser på selve matideen.
- VIKTIG: Når du nevner en tilbudsvare (i "Brukes"-linjen), skriv produktnavnet
  NØYAKTIG slik det står i tilbudsdataen (product_name), bokstav for bokstav,
  inkludert eventuelle store bokstaver. Ikke omskriv, forkort eller "fikse"
  navnet - brukeren skal kunne kjenne det igjen når de handler. Ingrediensene
  du finner på SELV utover dette (krydder, tilbehør du legger til for å gjøre
  retten god) trenger ikke være eksakte produktnavn - de skriver du naturlig.
- VARIASJON: Ikke gjenbruk samme krydder, saus eller tilbehør (f.eks. fiskesaus,
  rødbet) i mer enn én av rettene i samme svar. Hver rett skal ha sin egen,
  distinkte smaksprofil. Ikke tving inn ingredienser eller sauser som ikke
  faktisk passer sammen med hovedvaren, bare for å bruke dem opp.
- Ikke finn på en egen "meny"-beskrivelse med ekstra retter/tilbehør utover det
  som står i FORMAT-linjen under. Hele forslaget skal være ÉN linje per rett.

FORMAT på hvert rettforslag (følg dette NØYAKTIG, én rett per punkt, ingen
underpunkter, ingen ekstra "Brukes:"-linjer eller "Foreslått meny:"-avsnitt):
- **[Rettnavn]** - Brukes: [eksakt product_name fra tilbudsdata, evt. flere
  atskilt med " + "]. [Én kort, fristende setning om hvordan retten lages -
  maks 15-20 ord, kun ingredienser som faktisk passer med hovedvaren.]

Smakskunnskap du kan bruke (gode kombinasjoner du kjenner til):
{gode_kombinasjoner}

Kombinasjoner du bør UNNGÅ å foreslå:
{unngå_kombinasjoner}

Eksempel på hvordan du skal svare (legg merke til at produktnavnet er skrevet
EKSAKT som i tilbudsdataen, mens krydder/tilbehør er skrevet naturlig, og at
ingen av rettene deler samme krydder/saus):
Bruker: "Hva bør jeg lage denne uka?"
Tilbudsdata inneholder: KYLLINGFILET NATURELL (protein_kjott), JASMINRIS (karbo_stivelse), BROKKOLI (grønnsaker), LAKSEFILET (protein_fisk_sjomat)
Ditt svar:
- **Kremet kyllinggryte med ris** - Brukes: KYLLINGFILET NATURELL + JASMINRIS. Surres i karri og kokosmelk til en rask, mettende hverdagsmiddag.
- **Ovnsbakt laks med brokkoli** - Brukes: LAKSEFILET + BROKKOLI. Bakes i ovnen med sitron og hvitløk, klar på 25 minutter.

Etter at du har foreslått rettene, kan du gjerne avslutte med ett kort
oppfølgingsspørsmål til brukeren (f.eks. om de vil ha flere forslag, eller om
noe av dette ikke passer) - men hold det til maks én setning.

Du har tilgang til én funksjon for å hente tilbudsdata: hent_tilbud.
Hvis du trenger denne dataen for å svare godt (f.eks. brukeren spør om mat-ideer,
hva som er på tilbud, eller hva som er billig denne uka), skal du IKKE finne på
tilbud selv. Skriv i stedet et kall til funksjonen på EGEN LINJE, helt til slutt
i svaret ditt, på nøyaktig dette formatet:

CALL_HENT_TILBUD(search_term="...", store="...")

Begge argumenter er valgfrie - utelat det du ikke trenger, f.eks:
CALL_HENT_TILBUD()
CALL_HENT_TILBUD(search_term="kylling")

Regler for kallet:
- Bruk KUN dette formatet, ingen andre funksjonsnavn.
- Skriv kallet på en egen linje, ikke inni en setning.
- Ikke forklar til brukeren at du kommer til å gjøre et kall - det håndteres automatisk.
- Hvis du allerede har fått tilbudsdata i denne samtalen og den fortsatt er relevant,
  ikke gjør et nytt kall - bruk dataen du allerede har.
"""


def bygg_system_prompt() -> str:
    """
    Bygger system-prompten med smakskombinasjonene limt inn som lesbar tekst.
    Vi limer inn ALT vi har lastet fra JSON her (ved oppstart) - filtrering til
    kun det som er relevant for konkrete tilbud gjøres i format_tilbud_for_modell()
    når vi faktisk har tilbudsdata å matche mot.
    """
    gode = SMAK.get("gode_kombinasjoner", {})
    gode_tekst = "\n".join(
        f"- {ingrediens}: passer godt med {', '.join(partnere)}"
        for ingrediens, partnere in gode.items()
    ) or "(ingen data lastet)"

    unngå = SMAK.get("unngå_kombinasjoner", [])
    unngå_tekst = "\n".join(f"- {a} + {b}" for a, b in unngå) or "(ingen data lastet)"

    return SYSTEM_PROMPT_TEMPLATE.format(
        gode_kombinasjoner=gode_tekst,
        unngå_kombinasjoner=unngå_tekst,
    )


OPENING_MESSAGE = (
    "Hei! Jeg er assistenten din i Tilbudsradar. Jeg kan hjelpe deg med mat-ideer "
    "basert på det som er på tilbud i butikkene denne uka - bare spør! "
    "F.eks. \"hva bør jeg lage til middag i kveld?\" eller \"gi meg noen ideer for uka\"."
)

def hent_tilbud(search_term: str = "", store: str = "") -> list[dict]:
    """
    Henter produkter i kategorien "mat" som FAKTISK er på tilbud, fra nyeste
    katalog (høyeste year/week per butikk).

    Filtrerer bort rader som ikke er reelle tilbud (bruker NULL/0.0 som "ingen verdi"):
      1. current_price == old_price (begge har verdi, men ingen faktisk rabatt)
      2. current_price har verdi, men verken old_price eller discount_percent har det
      3. current_price, old_price OG discount_percent mangler alle verdi

    NYTT: henter også alle search_terms for hvert produkt og bruker dem til å
    tagge produktet med en kategori (protein/grønnsak/karbo/...) via
    data/kategorier.json - dette gjøres i Python etter spørringen, siden det
    er enklere å vedlikeholde enn en kjempe-SQL CASE-setning.

    Returnerer product_name, final_discount_percent og category - kompakt nok
    til at en 7b-modell klarer å bruke dataen effektivt.

    Args:
        search_term: valgfritt søkeord (matches mot product_search_terms og product_name)
        store: valgfritt butikknavn for å filtrere (f.eks. "Kiwi")

    Returns:
        Liste med dicts: product_name, final_discount_percent, category
    """
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
        })

    return resultat


AVAILABLE_FUNCTIONS = {
    "hent_tilbud": hent_tilbud,
}

def parse_call_args(raw_args: str) -> dict:
    """
    Parser argumentstrengen fra CALL_HENT_TILBUD(search_term="kylling", store="Kiwi")
    til en dict. Enkel og robust nok for dette formatet - ikke en generell parser.
    """
    args = {}
    if not raw_args.strip():
        return args

    for match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', raw_args):
        key, value = match.group(1), match.group(2)
        args[key] = value

    return args


def strip_call_from_text(text: str) -> str:
    """Fjerner CALL_HENT_TILBUD(...)-linjen fra teksten som vises til brukeren."""
    return CALL_PATTERN.sub("", text).strip()


def extract_call(text: str):
    """Returnerer (func_name, args_dict) hvis teksten inneholder et kall, ellers None."""
    match = CALL_PATTERN.search(text)
    if not match:
        return None
    return "hent_tilbud", parse_call_args(match.group(1))

def stream_model_response(messages: list, print_prefix: str = "AI: ") -> str:
    """
    Streamer modellens svar ord for ord til terminalen, akkurat som `ollama run`.
    Returnerer det FULLE rå-svaret (inkl. en eventuell CALL_HENT_TILBUD(...)-linje),
    slik at resten av koden kan parse den.

    Vi holder alltid tilbake litt tekst i en buffer, i tilfelle "CALL_HENT_TILBUD("
    er i ferd med å skrives - da skal ingenting av det vises til brukeren.
    """
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

            messages.append({
                "role": "user",
                "content": (
                    "Her er resultatet fra hent_tilbud - en liste med produktnavn "
                    "(product_name), rabattprosent (final_discount_percent) og kategori "
                    "(category) for varer som faktisk er på tilbud (dette er ikke noe "
                    "brukeren har skrevet, det er data du ba om):\n"
                    f"{json.dumps(result, ensure_ascii=False)}\n\n"
                    "Foreslå nå 3-5 KONKRETE MIDDAGSRETTER som bruker noen av disse "
                    "tilbudsvarene, i formatet du fikk beskrevet i systemmeldingen. "
                    "Husk: skriv product_name EKSAKT som det står i dataen over i "
                    "Brukes-linjen, og ikke gjenbruk samme krydder/tilbehør i flere retter. "
                    "Ikke oppsummer dataen eller list opp varene rått. "
                    "Ikke gjør et nytt kall med mindre du virkelig trenger mer data."
                ),
            })

            print()
            followup_raw = stream_model_response(messages)
            messages.append({"role": "assistant", "content": followup_raw})


if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"ADVARSEL: Fant ikke '{DB_PATH}' i denne mappa.")
        print("Legg scriptet i samme mappe som tilbudsradar.db, eller endre DB_PATH.\n")
    main()