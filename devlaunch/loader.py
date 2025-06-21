import os
import requests
from urllib.parse import urljoin

API_URL = "http://ip-adress-of-ec2:5000/resolve"
TEMPLATES_DIR = os.path.join(os.getcwd(), "templates", "scaffolds")
BUCKET_NAME = "devlaunch-templates-bucket"


def download_template_logic(prompt: str) -> str:
    response = requests.post(API_URL, json={"prompt": prompt})
    if response.status_code != 200:
        raise Exception(response.json().get("error", "Unknown error"))

    data = response.json()
    matched = data.get("matched")
    files = data.get("files", [])
    if not matched:
        raise Exception("No template matched your prompt.")

    template_url = matched.get("url", "")
    template_name = matched.get("name")
    if not template_name:
        template_name = os.path.dirname(template_url.rstrip("/"))
        if not template_name:
            template_name = template_url.rstrip("/")

    local_dir = os.path.join(TEMPLATES_DIR, template_name)
    os.makedirs(local_dir, exist_ok=True)

    prefix = os.path.dirname(template_url)
    if not prefix.endswith("/"):
        prefix += "/"

    for file_key in files:
        if not file_key.startswith(prefix):
            raise Exception(f"Unexpected file key format: {file_key}")
        relative_path = file_key[len(prefix):]
        local_path = os.path.join(local_dir, relative_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        file_url = f"{API_URL.replace('/resolve', '')}/download?key={file_key}"

        file_resp = requests.get(file_url)
        if file_resp.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(file_resp.content)
        else:
            raise Exception(f"Failed to download: {relative_path}")

    return local_dir
