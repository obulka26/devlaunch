import typer
import os
import subprocess
from devlaunch.generator import generate_file

app = typer.Typer()

TEMPLATES_DIR = os.path.join(os.getcwd(), "templates", "scaffolds")
PROJECTS_DIR = os.path.join(os.getcwd(), "projects")


@app.command()
def list(show: str = typer.Option("all", help="templates, projects, or all")):
    if show in ("all", "templates"):
        print("\n[📦] Available Templates:")
        for name in os.listdir(TEMPLATES_DIR):
            if os.path.isdir(os.path.join(TEMPLATES_DIR, name)):
                print(" -", name)

    if show in ("all", "projects"):
        print("\n[🛠️] Your Projects:")
        for name in os.listdir(PROJECTS_DIR):
            if os.path.isdir(os.path.join(PROJECTS_DIR, name)):
                print(" -", name)


@app.command()
def generate(template: str):
    generate_file(template)


@app.command()
def up(name: str):
    project_path = os.path.join(PROJECTS_DIR, name, "docker-compose.yml")
    if not os.path.exists(project_path):
        project_path = os.path.join(TEMPLATES_DIR, name, "docker-compose.yml")
        if not os.path.exists(project_path):
            print(f"[!] docker-compose.yml for '{name}' not found.")
            raise typer.Exit(1)

    subprocess.run(["docker-compose", "-f", project_path, "up", "-d"])


@app.command()
def stop(name: str):
    project_path = os.path.join(PROJECTS_DIR, name, "docker-compose.yml")
    if not os.path.exists(project_path):
        project_path = os.path.join(TEMPLATES_DIR, name, "docker-compose.yml")
        if not os.path.exists(project_path):
            print(f"[!] docker-compose.yml for '{name}' not found.")
            raise typer.Exit(1)

    subprocess.run(["docker-compose", "-f", project_path, "stop"])


if __name__ == "__main__":
    app()
