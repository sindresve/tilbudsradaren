import requests

from stores.coop import get_coop_url
from stores.kiwi import get_kiwi_url
from stores.rema import get_rema_url
from stores.europris import get_europris_url
from stores.joker import get_joker_url
from stores.spar import get_spar_url
from stores.bunnpris import get_bunnpris_url
from stores.meny import get_meny_url

def get_coop_id(postalcode, pos, chain):
    url = "https://www.coop.no/api/client/stores/search"
    params = {
        "language": "nb-NO",
        "query": postalcode,
        "chain": chain,
        "latitude": pos.lat,
        "longitude": pos.lon,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    return data["stores"][0]["id"]

coop_chains = {
    "coopExtra": "extra",
    "coopPrix": "prix",
    "coopMega": "mega",
}

def get_url(store, postalcode, pos):
    if store in coop_chains:
        coop_id = get_coop_id(postalcode, pos, coop_chains[store])
        return get_coop_url(coop_id)
    elif store == "kiwi":
        return get_kiwi_url(postalcode)
    elif store == "joker":
        return get_joker_url(postalcode)
    elif store == "bunnpris":
        return get_bunnpris_url(pos)
    elif store == "rema":
        return get_rema_url()
    elif store == "meny":
        return get_meny_url()
    elif store == "europris":
        return get_europris_url()
    elif store == "spar":
        return get_spar_url()
    else:
        raise ValueError(f"Ukjent butikk: {store}")