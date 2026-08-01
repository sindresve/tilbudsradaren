import requests

def get_spar_url():
    url = "https://spar.no/api/kundeavis?postCode=1"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    return data["url"]