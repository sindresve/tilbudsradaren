import os
from dotenv import load_dotenv

from tilbud_scraper import process_catalog
from utils import (get_pos, get_current_datetime, save_catalog)
from stores import get_url
from db import init_db, KNOWN_STORES
from db.database import get_connection

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

class TilbudsRadaren:
    def __init__(self, stores, postalcode, info):
        self.stores = stores
        self.pos = get_pos()
        self.postalcode = postalcode
        self.info = info

        init_db()
        self.scan_stores(postalcode)

    def scan_stores(self, postalcode):
        print(f"Scanner {len(self.stores)} butikker")

        for store in self.stores:
            print( f"Scanner {store}")

            content = get_url(store,postalcode,self.pos)

            save_catalog(content, KNOWN_STORES[store], store, self.info)

def main():
    info = get_current_datetime()

    # Hent kun aktiverte butikker fra databasen
    conn = get_connection()
    enabled_stores = [
        row["store"] for row in
        conn.execute("SELECT store FROM store_toggles WHERE enabled = 1")
    ]
    conn.close()

    TilbudsRadaren(
        enabled_stores,
        "1654",
        info
    )

    process_catalog(info=info)

if __name__=="__main__":
    main()