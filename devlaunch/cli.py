import typer
import os
import subprocess
import yaml
from devlaunch.generator import generate_file, create_from_prompt
from typing import List
from typing_extensions import Annotated
from devlaunch.loader import find_template
from pathlib import Path


app = typer.Typer(rich_markup_mode="rich")

TEMPLATES_DIR = os.path.join(os.getcwd(), "templates", "scaffolds")
PROJECTS_DIR = os.path.join(os.getcwd(), "projects")

CONFIG_PATH = Path(
    "~/my_studies/pet_projects/devlaunch/devlaunch/.llm_config.yaml"
).expanduser()

SAFE_FLAGS = {"--build", "--detach", "-d", "--no-color", "--quiet-pull"}

DANGEROUS_FLAGS = {
    "--force-recreate",
    "--remove-orphans",
    "--renew-anon-volumes",
    "--abort-on-container-exit",
    "--abort-on-container-failure",
    "--no-start",
    "--no-deps",
    "--scale",
    "--exit-code-from",
    "--pull=always",
}


@app.command()
def ls(show: str = typer.Option("all", help="templates, projects, or all")):
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


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="""
[bold cyan]Create and start containers[/bold cyan] (wraps [italic]docker-compose[/italic])

Use `[green]--unsafe[/green]` to allow potentially dangerous flags.

[underline]Common Options[/underline]:
- [bold]--build[/bold]: Build images before starting containers
- [bold]-d, --detach[/bold]: Run containers in background (detached mode)
- [bold]--no-color[/bold]: Produce monochrome output
- [bold]--quiet-pull[/bold]: Pull without printing progress
- [bold]--dry-run[/bold]: Execute command in dry run mode
- [bold]--menu[/bold]: Enable interactive shortcuts when attached (incompatible with --detach)
- [bold]--no-attach[/bold] [stringArray]: Do not attach (stream logs) to specified services
- [bold]--attach[/bold] [stringArray]: Attach only to specified services (incompatible with --attach-dependencies)
- [bold]--attach-dependencies[/bold]: Attach to log output of dependent services automatically
- [bold]--no-build[/bold]: Don't build images even if policy requires
- [bold]--no-log-prefix[/bold]: Don't print prefix in logs
- [bold]--timeout, -t[/bold] [int]: Timeout (seconds) for container shutdown/startup
- [bold]--timestamps[/bold]: Show timestamps in logs
- [bold]--wait[/bold]: Wait for services to be running or healthy (implies detached mode)
- [bold]--wait-timeout[/bold] [int]: Max wait duration for services to be running/healthy
- [bold]-w, --watch[/bold]: Watch source code and rebuild/refresh containers on file changes

[red]Dangerous Flags[/red] (require --unsafe):
- --force-recreate: Recreate containers even if config/image unchanged (incompatible with --no-recreate)
- --remove-orphans: Remove containers not defined in the Compose file
- -V, --renew-anon-volumes: Recreate anonymous volumes instead of reusing old data
- --abort-on-container-exit: Stop all containers if any container stops (incompatible with -d)
- --abort-on-container-failure: Stop all containers if any container exited with failure (incompatible with -d)
- --no-deps: Do not start linked/dependent services
- --no-start: Don't start containers after creating them
- --scale [SERVICE=NUM]: Scale SERVICE to NUM instances (overrides Compose file scale)
- --exit-code-from [SERVICE]: Return exit code from specified service container (implies --abort-on-container-exit)
- --pull [always|missing|never]: Pull image before running (default "policy")

[bold cyan]Create and start containers[/bold cyan] (wraps [italic]docker-compose[/italic])
""",
)
def up(
    ctx: typer.Context,
    extra_args: Annotated[
        List[str],
        typer.Argument(
            ...,
            help="[italic]NAME[/italic] of the project and any docker-compose flags.",
        ),
    ],
):
    args = list(extra_args)

    name = None
    cleaned_args = []
    for arg in args:
        if name is None and not arg.startswith("-"):
            name = arg
        else:
            cleaned_args.append(arg)

    if name is None:
        typer.echo("[!] Project name not specified.")
        raise typer.Exit(1)

    unsafe_mode = "--unsafe" in cleaned_args
    if unsafe_mode:
        cleaned_args.remove("--unsafe")

    if not unsafe_mode:
        for arg in cleaned_args:
            flag = arg.split("=")[0]
            if flag not in SAFE_FLAGS:
                typer.echo(
                    f"⚠️  Unsupported or potentially dangerous flag '{
                        arg
                    }' in safe mode."
                )
                typer.echo("   Use '--unsafe' if you're sure.")
                raise typer.Exit(1)

    project_path = os.path.join(PROJECTS_DIR, name, "docker-compose.yml")
    if not os.path.exists(project_path):
        project_path = os.path.join(TEMPLATES_DIR, name, "docker-compose.yml")
        if not os.path.exists(project_path):
            print(f"[!] docker-compose.yml for '{name}' not found.")
            raise typer.Exit(1)

    command = ["docker-compose", "-f", project_path, "up"] + cleaned_args
    subprocess.run(command)


@app.command()
def stop(name: str):
    project_path = os.path.join(PROJECTS_DIR, name, "docker-compose.yml")
    if not os.path.exists(project_path):
        project_path = os.path.join(TEMPLATES_DIR, name, "docker-compose.yml")
        if not os.path.exists(project_path):
            print(f"[!] docker-compose.yml for '{name}' not found.")
            raise typer.Exit(1)

    subprocess.run(["docker-compose", "-f", project_path, "stop"])


@app.command(
    help="""
[bold cyan]🤖 LLM (Large Language Model) Assistant Help[/bold cyan]

This command uses an AI model to generate [green]DevOps infrastructure templates[/green] based on your prompt.

To use this feature, you must configure [bold]one[/bold] of the two available providers:

[bold][1] 🌐 OpenRouter (Remote API)[/bold]
[dim]- Ideal for users who want access to various models hosted in the cloud.[/dim]
• Go to: [link=https://openrouter.ai]https://openrouter.ai[/link]
• Create an account and generate an API key
• Pick a model from: [link=https://openrouter.ai/models]https://openrouter.ai/models[/link]
• Configure your ~/.llm_config.yaml like this:

    llm_config: openrouter
    openrouter_api_key: YOUR_API_KEY
    openrouter_model: YOUR_MODEL_NAME  # ← Choose any available model

[italic yellow]⚠ Some models are paid! Even without a credit card, usage may consume free credits.[/italic yellow]

[bold][2] 🖥️ Ollama (Local Inference)[/bold]
[dim]- Ideal for offline use, but requires system resources.[/dim]
• Download and install from: [link=https://ollama.com]https://ollama.com[/link]
• Make sure Ollama is running
• Use this config:

    llm_config: local
    local_model: llama3
    ollama_url: http://localhost:11434/api/generate

• You can install models manually with:
    [italic]ollama run llama3[/italic]

[italic yellow]⚠ Local models may require 4–8+ GB RAM or more.[/italic yellow]

---

[bold green]🛠️ Automatic Setup:[/bold green]
Run [bold]devlaunch configure[/bold] to auto-generate your ~/.llm_config.yaml

Or create/edit manually.

---

[bold magenta]🧠 Model Quality Matters[/bold magenta]
Some models generate better infrastructure than others. Try different ones and update your config as needed.

Suggested models to test (to be filled by you):
 • ...

---

[bold cyan]Once configured, just run:[/bold cyan]

    devlaunch prompt

...and start generating scaffolds with AI!
"""
)
def prompt():
    user_input = input("🧠 What do you want to build?\n> ").strip()
    template = find_template(user_input)

    if template:
        print(f"\n✅ Template found: {template}")
        print("👉 To use it, run:")
        print(f"   devlaunch load {template}")
        print(f"   devlaunch up {template}")
    else:
        print(f"\n❌ No matching template found for: '{user_input}'")
        confirm = input("🚀 Generate a new one locally? [y/N] ").strip().lower()
        if confirm == "y":
            create_from_prompt(user_input)
            print("\n✅ Project generated.")
            print("👉 Use:")
            print(f"   devlaunch generate {template}")
            print(f"   devlaunch up {template}")


@app.command(help="⚙️ Configure your LLM provider for DevLaunch (OpenRouter or local)")
def configure():
    typer.echo("🧠 [bold]Choose LLM Provider:[/bold]\n1) OpenRouter\n2) Local (Ollama)")
    choice = input("Enter 1 or 2: ").strip()
    config = {}

    if choice == "1":
        config["llm_config"] = "openrouter"
        config["openrouter_api_key"] = input(
            "🔑 Enter your OpenRouter API key: "
        ).strip()
        config["openrouter_model"] = input(
            "🤖 Enter your preferred model (e.g. openai/gpt-3.5-turbo): "
        ).strip()

    elif choice == "2":
        config["llm_config"] = "local"
        config["local_model"] = input(
            "🤖 Enter your local model name (e.g. llama3): "
        ).strip()
        config["ollama_url"] = (
            input(
                "🌐 Enter Ollama URL (default: http://localhost:11434/api/generate): "
            ).strip()
            or "http://localhost:11434/api/generate"
        )

    else:
        typer.echo("❌ Invalid choice. Aborting.")
        raise typer.Exit(1)

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f)

    typer.echo(f"✅ Config saved to {CONFIG_PATH}")


@app.command()
def download():
    pass


@app.command()
def clean():
    pass


if __name__ == "__main__":
    app()
