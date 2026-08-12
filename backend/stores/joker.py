import base64
import re
import requests
import math
import urllib.parse

def get_joker_address(store_name, pos):
    lat = pos.lat
    lon = pos.lon

    url = "https://api.ngdata.no/sylinder/stores/v1/basic-info?chainId=1220"
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
        closest_store["organization"].get("address", ""),
        closest_store["organization"].get("postalCode", ""),
        closest_store["organization"].get("city", "")
    ]
    adresse_str = " ".join(d for d in deler if d).strip()

    destinasjon = urllib.parse.quote(adresse_str)

    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={destinasjon}&travelmode=walking"

    return {"store": store_name, "name": closest_store['storeName'], "maps_url": maps_url}

def get_catalog_and_collection(page_url):
    resp = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    html = resp.text

    match = re.search(r'cloudfront\.net/([A-Za-z0-9]+)/collections/([A-Za-z0-9]+)/', html)
    if not match:
        raise ValueError("Could not find catalog/collection IDs in page")
    catalog_id, collection_id = match.groups()
    return catalog_id, collection_id

def get_json(page_url, catalog_id, collection_id):
    raw_hash = f"{catalog_id}+{collection_id}"
    hash_b64 = base64.b64encode(raw_hash.encode()).decode()

    domain = page_url.split("/")[2]

    auth_resp = requests.get(
        "https://content-private.flipsnack.com/authorization",
        params={"hash": hash_b64, "domain": domain},
    )
    auth_resp.raise_for_status()
    auth = auth_resp.json()

    sig = auth["signature"][collection_id]
    url = (
        f"https://d3u72tnj701eui.cloudfront.net/{catalog_id}/"
        f"collections/{collection_id}/data.json?{sig}"
    )

    r = requests.get(url)
    r.raise_for_status()
    data = r.json()

    return data, sig

def create_links(json_data, catalog_id, collection_id, sig):
    pages_data = json_data["pages"]["data"]
    image_links = []

    for key in pages_data:
      url = f"https://d3u72tnj701eui.cloudfront.net/{catalog_id}/collections/{collection_id}/covers/{key}/original?{sig}"
      image_links.append(url)
        
    return image_links

def get_joker_url(postalcode):
    url = f"https://joker.no/api/kundeavis?postCode={postalcode}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    
    catalog_id, collection_id = get_catalog_and_collection(data['url'])
    json_data, sig = get_json(data['url'], catalog_id, collection_id)
    image_links = create_links(json_data, catalog_id, collection_id, sig)

    return image_links