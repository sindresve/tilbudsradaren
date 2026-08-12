import requests
import math
import urllib.parse
import re

def get_europris_address(store_name, pos):
    lat = pos.lat
    lon = pos.lon

    url = "https://www.europris.no/butikker/stores/get"
    response = requests.get(url, verify=False)
    response.raise_for_status()
    data = response.json()
    stores = data["stores"]

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))

    closest_store = None
    closest_distance = float("inf")

    for store in stores:
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
        closest_store.get("street", ""),
        closest_store.get("postcode", ""),
        closest_store.get("city", "")
    ]
    adresse_str = " ".join(d for d in deler if d).strip()

    destinasjon = urllib.parse.quote(adresse_str)

    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={destinasjon}&travelmode=walking"

    return {"store": store_name, "name": closest_store['name'], "maps_url": maps_url}

def get_image_urls(pub_id):
    info = requests.get(
        f"https://secure.viewer.zmags.com/services/publicationInfo/{pub_id}",
        params={
            "nocache": 0,      
            "recent": "true"
        }
    ).json()

    page_count = info["numberOfPages"]
    version = info["version"]
    base_url = f"https://secure.viewer.zmags.com/services/resource/pub/{pub_id}/pg470x600/{version}"


    return [f"{base_url}/{page}" for page in range(1, page_count + 1)]

def get_europris_url():
    url = "https://www.europris.no/kundeavis"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    match = re.search(r'publicationId\s*=\s*"([a-f0-9]+)"', resp.text)
    if match:
        publication_id = match.group(1)
        return get_image_urls(publication_id)
    else:
        raise ValueError("Fant ikke catalog_id for Europris")