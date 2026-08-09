import requests

from stores.coop import get_coop_url, get_coop_address
from stores.kiwi import get_kiwi_url, get_kiwi_address
from stores.rema import get_rema_url, get_rema_address
from stores.europris import get_europris_url, get_europris_address
from stores.joker import get_joker_url, get_joker_address
from stores.spar import get_spar_url, get_spar_address
from stores.bunnpris import get_bunnpris_url, get_bunnpris_address
from stores.meny import get_meny_url, get_meny_address

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

def get_address(store, postalcode, pos):
    if store in coop_chains:
        return get_coop_address(store, coop_chains[store], postalcode)
    elif store == "kiwi":
        return get_kiwi_address(store, pos)
    elif store == "joker":
        return get_joker_address(store, pos)
    elif store == "bunnpris":
        return get_bunnpris_address(store, pos)
    elif store == "rema":
        return get_rema_address(store, pos)
    elif store == "meny":
        return get_meny_address(store, pos)
    elif store == "europris":
        return get_europris_address(store, pos)
    elif store == "spar":
        return get_spar_address(store, pos)
    else:
        raise ValueError(f"Ukjent butikk: {store}")

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