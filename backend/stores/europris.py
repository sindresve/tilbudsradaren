from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import json
import re

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