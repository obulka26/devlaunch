from flask import Flask, request, jsonify, send_file
from io import BytesIO
import boto3
import yaml
import re
import os

app = Flask(__name__)

BUCKET_NAME = "devlaunch-templates-bucket"
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
            prefix = os.path.dirname(url)
            if prefix and not prefix.endswith("/"):
                prefix += "/"
            files = list_files_in_prefix(prefix)
            return jsonify({"matched": entry, "files": files})

    return jsonify({"matched": None})


@app.route("/download", methods=["GET"])
def download_file():
    key = request.args.get("key")
    if not key:
        return jsonify({"error": "No key provided"}), 400

    try:
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        file_stream = BytesIO(obj["Body"].read())
        file_stream.seek(0)
        return send_file(
            file_stream, as_attachment=True, download_name=os.path.basename(key)
        )
    except s3.exceptions.NoSuchKey:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
