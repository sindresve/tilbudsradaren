import requests
import json

def get_kiwi_url(postalcode):
    url = f"https://kiwi.no/api/kundeavis?postCode={postalcode}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    return data["url"]