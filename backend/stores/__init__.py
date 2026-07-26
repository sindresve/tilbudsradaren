import requests

from stores.coop_extra import get_coop_extra_url
from stores.kiwi import get_kiwi_url
from stores.rema import get_rema_url

# Konverterer postnummerne til unike id-koder for den nåværende butikken
def convert_postalcode(postalcode, pos):
    url = f"https://www.coop.no/api/client/stores/search?language=nb-NO&query={postalcode}&chain=extra&latitude={pos.lat}&longitude={pos.lon}"
    response = requests.get(url)
    
    data = response.json()

    return data["stores"][0]["id"]

def get_url(store, postalcode, pos):
    if store == "coopExtra":
        postal_id = convert_postalcode(postalcode, pos)
        return get_coop_extra_url(postal_id)
    elif store == "kiwi":
        return get_kiwi_url(postalcode)
    elif store == "rema":
        return get_rema_url()
    elif store == "meny":
        return "https://kundeavis.meny.no/GetPDF.ashx"
    else:
        raise ValueError(f"Ukjent butikk: {store}")