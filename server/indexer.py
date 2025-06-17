import boto3
import yaml

BUCKET_NAME = ""
OUTPUT_KEY = "index.yaml"
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

    required_keys = ["name", "description", "required_inputs", "tags"]
    for k in required_keys:
        if k not in data:
            raise ValueError(f"Missing {k} in {key}")

    data["url"] = key
    return data


def upload_index(templates):
    body = yaml.dump(templates, sort_keys=False)
    s3.put_object(Bucket=BUCKET_NAME, Key=OUTPUT_KEY,
                  Body=body.encode("utf-8"))


def main():
    template_keys = list_template_files()
    print(f"Found {len(template_keys)} template.yaml files.")

    templates = []
    for key in template_keys:
        try:
            data = fetch_and_parse_template(key)
            templates.append(data)
        except Exception as e:
            print(f"Error processing {key}: {e}")

    upload_index(templates)
    print(f"Uploaded index to s3://{BUCKET_NAME}/{OUTPUT_KEY}")


if __name__ == "__main__":
    main()
