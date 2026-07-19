import os
from dotenv import load_dotenv

from tilbud_scraper import process_catalog
from utils import (get_pos, get_current_datetime, save_catalog)
from stores import get_url
from db import init_db

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

            type_map={
                "rema":"image",
                "kiwi":"pdf",
                "coopExtra":"pdf"
            }

            save_catalog(content, type_map[store], store, self.info)

def main():
    info = get_current_datetime()

    stores=[
        "kiwi",
        "coopExtra"
    ]

    TilbudsRadaren(stores, "1654", info)

    process_catalog(info=info)

if __name__=="__main__":
    main()