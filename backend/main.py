import os
from dotenv import load_dotenv

from tilbud_scraper import process_catalog
from utils import get_pos, get_current_datetime
from storage import save_catalog
from stores import get_url

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

class TilbudsRadaren:
    def __init__(self, stores: list[str], postalcode: str, info):
        self.stores = stores
        self.pos = get_pos()
        self.postalcode = postalcode
        self.info = info
        
        self.scan_stores(self.postalcode)
    
    def scan_stores(self, postalcode):
        print(f"Scanning {len(self.stores)} stores: {', '.join(self.stores)}")

        for store in self.stores:
            print(f"Scanning {store}...")
            content = get_url(store, postalcode, self.pos)
            type_map = {
                "rema": "image", 
                "kiwi": "pdf", 
                "coopExtra": "pdf"
            }
            save_catalog(content, type_map[store], store, self.info)
    
def main():
    info = get_current_datetime()
    postalcode = "1654"
    #stores = ["rema", "kiwi", "coopExtra"]
    stores = ["kiwi", "coopExtra"]
    
    TilbudsRadaren(stores, postalcode, info)

    process_catalog(data_dir="data", output_path=f"tilbud_{info['year']}_w{info['week']:02d}.json", info=info)

if __name__ == "__main__":
    main()