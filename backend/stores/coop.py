import re
import requests
import chompjs
from bs4 import BeautifulSoup

def get_coop_url(coop_id):
    url = f"https://kundeavis.coop.no/aviser/?id={coop_id}#popup-index"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    script_content = None
    for script in soup.find_all("script"):
        if script.string and "var g_cfg" in script.string:
            script_content = script.string
            break

    if script_content is None:
        raise ValueError("Fant ikke g_cfg script på siden")

    match = re.search(r"var\s+g_cfg\s*=\s*(\{.*?\});", script_content, re.DOTALL)

    if match is None:
        raise ValueError("Klarte ikke å parse g_cfg")

    g_cfg = match.group(1)
    data = chompjs.parse_js_object(g_cfg)

    return "https://kundeavis.coop.no/aviser/" + data["pdf"]