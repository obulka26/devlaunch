# llm.py
import yaml
from pathlib import Path
import openai
import requests
import subprocess

# CONFIG_PATH = Path.home() / ".llm_config.yaml"


SYSTEM_PROMPT = """You are a DevOps assistant. 
Your task is to return infrastructure templates based on user requests.

For each request, you must return the following two things:

1. A docker-compose.yaml Jinja2 template
2. A metadata YAML block describing the service

The metadata format:
description: <short description>
required_inputs:
  - VAR1
  - VAR2
  - ...

Return the two parts **separated by a special marker** like: "---END_METADATA---"

Only return these two things. Do not explain anything. Do not include extra text.
Do NOT use Markdown formatting. Do NOT use ```yaml or ``` or horizontal lines (---).
Return plain text only."""


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    return {}


def query_openai(prompt: str, api_key) -> str:
    if not api_key:
        raise ValueError("No OpenAI API key provided")

    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response["choices"][0]["message"]["content"].strip()


def check_ollama_installed():
    try:
        subprocess.run(["ollama", "-v"], check=True, stdout=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def query_local(prompt: str, model: str, url: str) -> str:
    full_prompt = f"{SYSTEM_PROMPT}\nUser: {prompt}"

    payload = {"model": model, "prompt": full_prompt, "stream": False}

    response = requests.post(url, json=payload)
    data = response.json()
    return data.get("response", "").strip()


def query_llm(prompt: str) -> str:
    config = load_config()
    provider = config.get("llm_config")

    if not provider:
        raise Exception(
            "❌ No LLM provider specified in config (.llm_config.yaml)")

    if provider == "openai":
        api_key = config.get("open_ai_key")
        if not api_key:
            raise Exception("❌ No OpenAI API key found in config.")
        return query_openai(prompt, api_key)

    elif provider == "local":
        model = config.get("local_model")
        if not model:
            raise Exception(
                "❌ No local model specified in config (local_model).")
        url = config.get("ollama_url")
        if not url:
            raise Exception("❌ No local url specified in config (ollama_url).")
        if not check_ollama_installed():
            raise Exception(
                "❌ Ollama is not installed. Please install it first.")
        return query_local(prompt, model, url)

    else:
        raise Exception(f"❌ Unknown LLM provider: {provider}")
