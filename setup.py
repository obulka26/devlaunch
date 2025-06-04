from setuptools import setup, find_packages

setup(
    name="devlaunch",
    version="0.1",
    packages=find_packages(),
    install_requires=["typer"],
    entry_points={
        "console_scripts": [
            "devlaunch = devlaunch.cli:app",
        ],
    },
)
