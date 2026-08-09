from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import pgeocode
import math
import requests

DATA_FOLDER = Path("data")

@dataclass
class Pos:
    lat: float
    lon: float

_nomi = pgeocode.Nominatim("no")  # initialiseres én gang, gjenbrukes

def get_pos(postal_code) -> Pos:
    result = _nomi.query_postal_code(postal_code)

    if math.isnan(result.latitude) or math.isnan(result.longitude):
        raise ValueError(f"Ukjent postnummer: {postal_code!r}")

    return Pos(lat=result.latitude, lon=result.longitude)

def get_current_datetime():
    now = datetime.now()

    return {
        "date": now.strftime("%Y-%m-%d"),      # 2026-07-18
        "week": now.isocalendar().week,        # 29
        "time": now.strftime("%H:%M:%S"),      # 23:15:42
        "weekday": now.strftime("%A"),         # Saturday
        "year": now.year                       # 2026
    }

def save_catalog(content, file_type, store, info):
    DATA_FOLDER.mkdir(exist_ok=True)

    if file_type == "image":
        store_folder = (DATA_FOLDER / f"{store}_{info['year']}_w{info['week']:02d}")
        store_folder.mkdir(exist_ok=True)

        for i, img in enumerate(content):
            img_data = requests.get(img).content
            
            with open(store_folder / f"{i}.jpg", "wb") as f:
                f.write(img_data)

    elif file_type == "pdf":
        filename = (DATA_FOLDER / f"{store}_{info['year']}_w{info['week']:02d}.pdf")
        pdf_bytes = requests.get(content).content

        with open(filename, "wb") as f:
            f.write(pdf_bytes)