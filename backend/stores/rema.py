from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import requests
import json
import math
import urllib.parse

def get_rema_address(store_name, pos):
    lat = pos.lat
    lon = pos.lon

    try:
        url = "https://www.rema.no/wp-json/rema-stores/v1/get-stores-data"
        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()
        stores = data["stores"]
    except Exception as e:
        print(f"Advarsel: klarte ikke å hente Rema-butikker ({e})")
        return None

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
        print("Advarsel: fant ingen Rema-butikker med gyldige koordinater.")
        return None

    deler = [
        closest_store.get("visitAddress", ""),
        closest_store.get("visitPostCode", ""),
        closest_store.get("countyName", "")
    ]
    adresse_str = " ".join(d for d in deler if d).strip()

    destinasjon = urllib.parse.quote(adresse_str)

    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={destinasjon}&travelmode=driving"

    return {"store": store_name, "name": closest_store['name'], "maps_url": maps_url}

def get_rema_catalog_id(scripts):
    for script in scripts:
        try:
            data = json.loads(script.string)
        except (TypeError, json.JSONDecodeError) as e:
            print(f"Advarsel: klarte ikke å parse script-tag som JSON ({e})")
            continue

        graph = data.get("@graph", [])

        for item in graph:
            if item.get("@type") == "ItemList":

                for element in item.get("itemListElement", []):

                    item_data = element.get("item")
                    if not item_data:
                        continue

                    publication_url = item_data.get("url")

                    if publication_url and "publication=" in publication_url:

                        query = urlparse(publication_url).query
                        publication_ids = parse_qs(query).get("publication")

                        if publication_ids:
                            return publication_ids[0]

    print("Advarsel: fant ingen catalog_id for Rema i script-tagene.")
    return None

def get_rema_url():
    try:
        url = "https://etilbudsavis.no/REMA-1000"
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Advarsel: klarte ikke å hente Rema-siden ({e})")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")

    catalog_id = get_rema_catalog_id(scripts)
    if catalog_id is None:
        print("Advarsel: fortsetter uten Rema-katalog siden catalog_id mangler.")
        return []

    try:
        final_url = f"https://api.etilbudsavis.dk/v2/catalogs/{catalog_id}/pages?r_locale=en_US"
        response = requests.get(final_url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Advarsel: klarte ikke å hente Rema-katalogsider ({e})")
        return []

    return [image["view"] for image in data]