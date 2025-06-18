from flask import Flask, request, jsonify
import boto3
import yaml
import re

app = Flask(__name__)

BUCKET_NAME = ""
INDEX_FILE_KEY = "index.yaml"
TAGS_FILE_KEY = "tags.yaml"

s3 = boto3.client("s3")


def load_yaml_from_s3(key):
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    content = obj["Body"].read().decode("utf-8")
    return yaml.safe_load(content)


def load_known_tags():
    return set(load_yaml_from_s3(TAGS_FILE_KEY))


def extract_tags(prompt: str, known_tags: set):
    words = re.findall(r"\b\w+\b", prompt.lower())
    return set(word for word in words if word in known_tags)


def list_files_in_prefix(prefix: str):
    paginator = s3.get_paginator("list_objects_v2")
    result = []
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
        contents = page.get("Contents", [])
        for obj in contents:
            result.append(obj["Key"])
    return result


@app.route("/resolve", methods=["POST"])
def resolve():
    payload = request.get_json()
    prompt = payload.get("prompt", "")

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    known_tags = load_known_tags()
    input_tags = extract_tags(prompt, known_tags)
    index = load_yaml_from_s3(INDEX_FILE_KEY)

    for entry in index:
        template_tags = set(entry.get("tags", []))
        if template_tags == input_tags:
            url = entry.get("url", "")
            if not url.endswith("/"):
                url += "/"
            files = list_files_in_prefix(url)
            return jsonify({"matched": entry, "files": files})

    return jsonify({"matched": None})


if __name__ == "__main__":
    app.run(debug=True)
