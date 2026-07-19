from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import requests
import json

def get_rema_catalog_id(scripts):
    for script in scripts:
        data = json.loads(script.string)

        graph = data.get("@graph", [])

        for item in graph:
            if item.get("@type") == "ItemList":

                for element in item.get("itemListElement", []):

                    item_data = element["item"]

                    publication_url = item_data.get("url")

                    if publication_url and "publication=" in publication_url:

                        query = urlparse(publication_url).query

                        publication_id = parse_qs(query)["publication"][0]

                        return publication_id

def get_rema_url():
    url = "https://etilbudsavis.no/REMA-1000"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")

    catalog_id = get_rema_catalog_id(scripts)
    if catalog_id is None:
        raise ValueError("Fant ikke catalog_id for Rema")

    final_url = f"https://api.etilbudsavis.dk/v2/catalogs/{catalog_id}/pages?r_locale=en_US"
    response = requests.get(final_url)
    response.raise_for_status()

    data = response.json()
    return [{"view": image["view"]} for image in data]