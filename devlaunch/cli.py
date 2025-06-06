import typer
import os
import subprocess
from devlaunch.generator import generate_file

app = typer.Typer()

TEMPLATES_DIR = os.path.join(os.getcwd(), "templates", "scaffolds")
PROJECTS_DIR = os.path.join(os.getcwd(), "projects")


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


DEVLUANCH_UP_HELP = """
Usage:  devlaunch up NAME [OPTIONS]

Create and start containers (wraps docker-compose)

Options:
      --abort-on-container-exit      Stops all containers if any container was stopped. Incompatible with -d
      --abort-on-container-failure   Stops all containers if any container exited with failure. Incompatible with -d
      --always-recreate-deps         Recreate dependent containers. Incompatible with --no-recreate.
      --attach stringArray           Restrict attaching to the specified services. Incompatible with --attach-dependencies.
      --attach-dependencies          Automatically attach to log output of dependent services
      --build                        Build images before starting containers
  -d, --detach                       Detached mode: Run containers in the background
      --dry-run                      Execute command in dry run mode
      --exit-code-from string        Return the exit code of the selected service container. Implies --abort-on-container-exit
      --force-recreate               Recreate containers even if their configuration and image haven't changed
      --menu                         Enable interactive shortcuts when running attached. Incompatible with --detach. Can also be enable/disable by setting COMPOSE_MENU environment var.
      --no-attach stringArray        Do not attach (stream logs) to the specified services
      --no-build                     Don't build an image, even if it's policy
      --no-color                     Produce monochrome output
      --no-deps                      Don't start linked services
      --no-log-prefix                Don't print prefix in logs
      --no-recreate                  If containers already exist, don't recreate them. Incompatible with --force-recreate.
      --no-start                     Don't start the services after creating them
      --pull string                  Pull image before running ("always"|"missing"|"never") (default "policy")
      --quiet-pull                   Pull without printing progress information
      --remove-orphans               Remove containers for services not defined in the Compose file
  -V, --renew-anon-volumes           Recreate anonymous volumes instead of retrieving data from the previous containers
      --scale scale                  Scale SERVICE to NUM instances. Overrides the scale setting in the Compose file if present.
  -t, --timeout int                  Use this timeout in seconds for container shutdown when attached or when containers are already running
      --timestamps                   Show timestamps
      --wait                         Wait for services to be running|healthy. Implies detached mode.
      --wait-timeout int             Maximum duration to wait for the project to be running|healthy
  -w, --watch                        Watch source code and rebuild/refresh containers when files are updated.
"""

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


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def up(ctx: typer.Context):
    args = list(ctx.args)

    if "--help" in args or "-h" in args or len(args) == 0:
        typer.echo(DEVLUANCH_UP_HELP)
        raise typer.Exit()

    name = None
    extra_args = []
    for arg in args:
        if name is None and not arg.startswith("-"):
            name = arg
        else:
            extra_args.append(arg)

    if name is None:
        typer.echo("[!] Project name not specified.")
        raise typer.Exit(1)

    unsafe_mode = "--unsafe" in extra_args
    if unsafe_mode:
        extra_args.remove("--unsafe")

    if not unsafe_mode:
        for arg in extra_args:
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

    command = ["docker-compose", "-f", project_path, "up"] + extra_args
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
    pass


@app.command()
def download():
    pass


@app.command()
def clean():
    pass


if __name__ == "__main__":
    app()
