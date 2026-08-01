import requests

from stores.coop import get_coop_url
from stores.kiwi import get_kiwi_url
from stores.rema import get_rema_url
from stores.europris import get_europris_url
from stores.joker import get_joker_url

# Convert postalcode to unique id-codes for the current store
def convert_postalcode(postalcode, pos, store):
    url = f"https://www.coop.no/api/client/stores/search?language=nb-NO&query={postalcode}&chain={store}&latitude={pos.lat}&longitude={pos.lon}"
    response = requests.get(url)
    
    data = response.json()

    return data["stores"][0]["id"]

def get_url(store, postalcode, pos):
    if store == "coopExtra":
        postal_id = convert_postalcode(postalcode, pos, "extra")
        return get_coop_url(postal_id)
    if store == "coopPrix":
        postal_id = convert_postalcode(postalcode, pos, "prix")
        return get_coop_url(postal_id)
    elif store == "kiwi":
        return get_kiwi_url(postalcode)
    elif store == "rema":
        return get_rema_url()
    elif store == "meny":
        return "https://kundeavis.meny.no/GetPDF.ashx"
    elif store == "europris":
        return get_europris_url()
    elif store == "joker":
        return get_joker_url(postalcode)
    else:
        raise ValueError(f"Ukjent butikk: {store}")