import boto3
import yaml

BUCKET_NAME = "devlaunch-templates-bucket"
INDEX_OUTPUT_KEY = "index.yaml"
TAGS_OUTPUT_KEY = "tags.yaml"

s3 = boto3.client("s3")


def list_template_files():
    paginator = s3.get_paginator("list_objects_v2")
    result = []
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("template.yaml"):
                result.append(key)
    return result


def fetch_and_parse_template(key):
    response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    content = response["Body"].read()
    data = yaml.safe_load(content)

    if "tags" not in data:
        raise ValueError(f"Missing 'tags' in {key}")

    return {"tags": data["tags"], "url": key}


def upload_file(key, data):
    body = yaml.dump(data, sort_keys=False)
    s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=body.encode("utf-8"))


def main():
    template_keys = list_template_files()
    print(f"Found {len(template_keys)} template.yaml files.")

    templates = []
    tag_set = set()

    for key in template_keys:
        try:
            data = fetch_and_parse_template(key)
            templates.append(data)
            tag_set.update(data["tags"])
        except Exception as e:
            print(f"Error processing {key}: {e}")

    upload_file(INDEX_OUTPUT_KEY, templates)
    print(f"Uploaded index to s3://{BUCKET_NAME}/{INDEX_OUTPUT_KEY}")

    sorted_tags = sorted(tag_set)
    upload_file(TAGS_OUTPUT_KEY, sorted_tags)
    print(f"Uploaded tags to s3://{BUCKET_NAME}/{TAGS_OUTPUT_KEY}")


if __name__ == "__main__":
    main()
