def find_template(query: str):
    fake_templates = {
        "postgres": "postgres",
        "nginx": "ngnix",
    }
    for key in fake_templates:
        if key in query.lower():
            return fake_templates[key]
    return None
