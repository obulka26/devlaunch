import os
import yaml
import openai
from jinja2 import Template
from pathlib import Path


TEMPLATES_DIR = os.path.join(os.getcwd(), "templates", "scaffolds")
PROJECTS_DIR = os.path.join(os.getcwd(), "projects")


def load_template_config(template_dir):
    config_path = os.path.join(template_dir, "template.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def prompt_for_values(required_inputs):
    data = {}
    for field in required_inputs:
        value = input(f"{field}: ")
        data[field] = value
    return data


def generate_file(template: str):
    template_dir = os.path.join(TEMPLATES_DIR, template)

    if not os.path.exists(template_dir):
        print(f"[!] Template '{template}' not found.")
        return

    config = load_template_config(template_dir)
    required_inputs = config.get("required_inputs", [])
    variables = prompt_for_values(required_inputs)

    project_name = input("Project name: ").strip()
    output_dir = os.path.join(PROJECTS_DIR, project_name)
    os.makedirs(output_dir, exist_ok=True)

    j2_path = os.path.join(template_dir, "docker-compose.j2")
    with open(j2_path) as f:
        template_content = f.read()

    rendered = Template(template_content).render(**variables)

    output_path = os.path.join(output_dir, "docker-compose.yml")
    with open(output_path, "w") as f:
        f.write(rendered)

    print(f"[+] Generated docker-compose.yml at: {output_path}")


def query_llm_for_template(prompt: str) -> str:
    system_prompt = """You are a DevOps assistant that maps user requests to internal template names.
For example:
- 'I want a PostgreSQL database' => 'postgres'
- 'Simple nginx proxy server' => 'ngnix'
- 'I want to deploy Redis cluster' => 'redis'

Return ONLY the template folder name like 'postgres', 'ngnix', or 'redis'.
If unsure, return your best guess."""

    response = openai.ChatCompletion.create(
        model="gpt-4",  # або gpt-3.5-turbo
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    return response["choices"][0]["message"]["content"].strip()
