from dataclasses import dataclass
from datetime import datetime
import requests


@dataclass
class Pos:
    lat: float
    lon: float

# Få nåværende posisjon for å finne nærmeste butikk
def get_pos() -> Pos:
    response = requests.get("https://ipinfo.io/json")
    response.raise_for_status()
    data = response.json()

    lat_str, lon_str = data["loc"].split(",")
    return Pos(lat=float(lat_str), lon=float(lon_str))

def get_current_datetime():
    now = datetime.now()

    return {
        "date": now.strftime("%Y-%m-%d"),      # 2026-07-18
        "week": now.isocalendar().week,        # 29
        "time": now.strftime("%H:%M:%S"),      # 23:15:42
        "weekday": now.strftime("%A"),         # Saturday
        "year": now.year                       # 2026
    }