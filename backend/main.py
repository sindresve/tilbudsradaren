import shutil
from pathlib import Path

from tilbud_scraper import process_catalog
from utils import (get_pos, get_current_datetime, save_catalog)
from stores import get_url, get_address
from db import init_db, KNOWN_STORES
from db.database import get_connection
from api.utils.gemini_key import get_gemini_api_key
from api.utils.product_monitor import ProductMonitor


class TilbudsRadaren:
    def __init__(self, stores, postal_code, info):
        self.stores = stores
        self.pos = get_pos(postal_code)
        self.postal_code = postal_code
        self.info = info
        self.store_info = []

    def run(self):
        gemini_api_key = get_gemini_api_key()
        if gemini_api_key is None:
            raise RuntimeError("Ingen Gemini API nøkkel funnet, sett nøkkelen i innstillinger først")
        self.scan_stores(self.postal_code)
        return self.store_info

    def scan_stores(self, postal_code):
        print(f"Scanner {len(self.stores)} butikker")

        for store in self.stores:
            print( f"Scanner {store}")

            content = get_url(store,postal_code,self.pos)
            info = get_address(store, postal_code, self.pos)
            self.store_info.append(info)
            save_catalog(content, KNOWN_STORES[store], store, self.info)


def cleanup_data_dir(data_dir="data"):
    """Sletter alle nedlastede tilbudsaviser (bilder/PDF-er) etter at de er lagret i databasen."""
    base = Path(data_dir)
    if not base.exists():
        return

    for item in base.iterdir():
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            item.unlink(missing_ok=True)

    print(f"Ryddet opp i {data_dir}/")

def get_scan_settings(conn):
    """Henter postnummer og aktiverte butikker fra databasen."""
    cursor = conn.cursor()

    cursor.execute("SELECT store FROM store_toggles WHERE enabled = 1")
    enabled_stores = [row["store"] for row in cursor.fetchall()]

    cursor.execute("SELECT postal_code FROM settings WHERE id = 1")
    row = cursor.fetchone()
    postal_code = row["postal_code"] if row else None

    return enabled_stores, postal_code


def scan():
    init_db()
    info = get_current_datetime()

    conn = get_connection()
    enabled_stores, postal_code = get_scan_settings(conn)
    conn.close()

    if not enabled_stores:
        raise RuntimeError("Ingen butikker er aktivert i innstillinger")
    if not postal_code:
        raise RuntimeError("Ingen postnummer satt i innstillinger")

    radar = TilbudsRadaren(enabled_stores, postal_code, info)
    store_info = radar.run()

    process_catalog(info=info, stores_info=store_info)
    cleanup_data_dir()

    monitor = ProductMonitor()
    monitor.run()