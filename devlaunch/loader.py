import os
import requests
from urllib.parse import urljoin

API_URL = ""
TEMPLATES_DIR = os.path.join(os.getcwd(), "templates", "scaffolds")
BUCKET_NAME = "..."


def download_template_logic(prompt: str) -> str:
    response = requests.post(API_URL, json={"prompt": prompt})
    if response.status_code != 200:
        raise Exception(response.json().get("error", "Unknown error"))

    data = response.json()
    matched = data.get("matched")
    files = data.get("files", [])
    if not matched:
        raise Exception("No template matched your prompt.")

    template_name = matched.get("name") or matched.get(
        "url").rstrip("/").split("/")[-1]
    local_dir = os.path.join(TEMPLATES_DIR, template_name)
    os.makedirs(local_dir, exist_ok=True)

    url_prefix = matched.get("url", "")
    if not url_prefix.endswith("/"):
        url_prefix += "/"

    for file_key in files:
        relative_path = file_key[len(url_prefix):]
        local_path = os.path.join(local_dir, relative_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        file_url = urljoin(
            f"https://{BUCKET_NAME}.s3.amazonaws.com/", file_key)
        file_resp = requests.get(file_url)
        if file_resp.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(file_resp.content)
        else:
            raise Exception(f"Failed to download: {relative_path}")

    return local_dir
