import requests
from pathlib import Path
from urllib.parse import urlparse
import os

# Lagrer innholdet til katalogene
def save_catalog(content: any, type: str, name: str, info):
    if type == "image": 
        folder = Path(f"data/{name}_{info['year']}_w{info['week']:02d}")
        folder.mkdir(exist_ok=True)

        for index, item in enumerate(content):
            image_url = item["view"]

            response = requests.get(image_url)

            if response.status_code == 200:
                # Get file extension
                extension = os.path.splitext(urlparse(image_url).path)[1]

                if not extension:
                    extension = ".jpg"

                filename = folder / f"{index}{extension}"

                with open(filename, "wb") as file:
                    file.write(response.content)

                print(f"Saved: {filename}")

            else:
                print(f"Failed: {image_url}")
        return print("Images saved!")
    elif type == "pdf":
        folder = Path("data")
        folder.mkdir(exist_ok=True)

        response = requests.get(content)

        if response.status_code == 200:
            # Get file extension
            extension = os.path.splitext(urlparse(content).path)[1]

            filename = folder / f"{name}_{info['year']}_w{info['week']:02d}{extension}"

            with open(filename, "wb") as file:
                file.write(response.content)

            print(f"Saved: {filename}")

        else:
            print(f"Failed: {content}")
    else:
        return print(f"Unknown type: {type}")