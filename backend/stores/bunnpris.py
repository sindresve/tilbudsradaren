import requests
import urllib3
import math
import urllib.parse
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_store_id(latitude, longitude):
    url = f"https://squid-api.tjek.com/v2/catalogs?dealer_id=5b11sm&order_by=-publication_date&offset=0&limit=24&types=paged%2Cincito&r_lat={latitude}&r_lng={longitude}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
    response = requests.get(url, headers)
    response.raise_for_status()
    data = response.json()

    return data[0]["id"]

def get_bunnpris_url(pos):
    store_id = get_store_id(pos.lat, pos.lon)

    url = f"https://squid-api.tjek.com/v2/catalogs/{store_id}/pages"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
    response = requests.get(url, headers)
    response.raise_for_status()
    data = response.json()

    data = response.json()
    return [image["view"] for image in data]


def get_bunnpris_address(store_name, pos):
    lat = pos.lat
    lon = pos.lon

    url = "https://www.bunnpris.no/alle-butikker"
    response = requests.get(url, verify=False)
    response.raise_for_status()
    data = response.json()

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))

    closest_store = None
    closest_distance = float("inf")

    for store in data:
        try:
            store_lat = float(store["latitude"])
            store_lon = float(store["longitude"])
        except (ValueError, TypeError, KeyError):
            continue

        distance = haversine(lat, lon, store_lat, store_lon)

        if distance < closest_distance:
            closest_distance = distance
            closest_store = store

    if not closest_store:
        print("Fant ingen butikker med gyldige koordinater.")
        return None

    deler = [
        closest_store.get("address", ""),
        closest_store.get("postal_code", ""),
        closest_store.get("town", "")
    ]
    adresse_str = " ".join(d for d in deler if d).strip()

    destinasjon = urllib.parse.quote(adresse_str)

    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={destinasjon}&travelmode=driving"

    return {"store": store_name, "name": closest_store['title'], "maps_url": maps_url}