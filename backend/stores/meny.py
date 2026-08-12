import requests
import math
import urllib.parse

def get_meny_address(store_name, pos):
    lat = pos.lat
    lon = pos.lon

    url = "https://api.ngdata.no/sylinder/stores/v1/basic-info?chainId=1300"
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
            store = store["storeDetails"]
            store_lat = float(store["position"]["lat"])
            store_lon = float(store["position"]["lng"])
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
        closest_store.get("storeName", ""),
        closest_store["organization"].get("address", ""),
        closest_store["organization"].get("postalCode", ""),
        closest_store["organization"].get("city", "")
    ]
    adresse_str = " ".join(d for d in deler if d).strip()

    destinasjon = urllib.parse.quote(adresse_str)

    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={destinasjon}&travelmode=walking"

    return {"store": store_name, "name": closest_store['storeName'], "maps_url": maps_url}

def get_meny_url():
    return "https://kundeavis.meny.no/GetPDF.ashx"
