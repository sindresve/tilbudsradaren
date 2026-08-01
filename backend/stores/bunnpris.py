import requests
import urllib3
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