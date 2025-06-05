import typer
import os
import subprocess

app = typer.Typer()

DEFAULT_SCAFFOLDS_DIR = os.path.join(os.getcwd(), "templates", "scaffolds")


@app.command()
def list(path: str = DEFAULT_SCAFFOLDS_DIR):
    if not os.path.isdir(path):
        print(f"No such directory: {path}")
        return

    for name in os.listdir(DEFAULT_SCAFFOLDS_DIR):
        full_path = os.path.join(DEFAULT_SCAFFOLDS_DIR, name)
        if os.path.isdir(full_path):
            print("-", name)


@app.command()
def up(name: str):
    """Підняти шаблон"""
    compose_path = os.path.join(
        DEFAULT_SCAFFOLDS_DIR, name, "docker-compose.yml")
    if not os.path.exists(compose_path):
        print(f"[!] Template '{name}' doesn't have docker-compose.yml")
        raise typer.Exit(code=1)

    subprocess.run(["docker-compose", "-f", compose_path, "up", "-d"])


if __name__ == "__main__":
    app()
