import pathlib
from setuptools import setup, find_packages


HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name = "pyexalus",
    version = "0.2.1",
    author = "Marcel Janicki",
    description = "A simple wrapper for Exalus Home, created specifically for HomeAssistant integration.",
    long_description=README,
    long_description_content_type="text/markdown",
    license = "Apache License 2.0",
    packages = find_packages(),
    python_requires = ">=3.10.6",
    install_requires = ["requests", "events", "signalrcore"],
    keywords = "exalus, home assistant, client",
    url = "https://github.com/marceljanicki/PyExalus"
)