import typer
import os
import subprocess
from devlaunch.generator import generate_file, create_from_prompt
from typing import List
from typing_extensions import Annotated
from devlaunch.loader import find_template


app = typer.Typer(rich_markup_mode="rich")

TEMPLATES_DIR = os.path.join(os.getcwd(), "templates", "scaffolds")
PROJECTS_DIR = os.path.join(os.getcwd(), "projects")

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


@app.command()
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
            print("\n✅ Project generated. Use `up <name>` to run.")


@app.command()
def download():
    pass


@app.command()
def clean():
    pass


if __name__ == "__main__":
    app()
