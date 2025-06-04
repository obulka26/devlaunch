import typer

app = typer.Typer()


@app.command()
def list():
    typer.echo("Availavle templates: ...")


@app.command()
def create(name: str):
    typer.echo(f"Creating {name}...")


@app.command()
def deploy():
    typer.echo("Deploying...")


if __name__ == "__main__":
    app()
