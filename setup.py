import pathlib
from setuptools import setup, find_packages


HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name = "PyExalus",
    version = "0.1",
    author = "Marcel Janicki",
    description = "Tiny module to communicate with Exalus controller",
    long_description=README,
    long_description_content_type="text/markdown",
    license = "Apache License 2.0",
    packages = find_packages(),
    python_requires = ">=3.10.6",
    install_requires = ["requests", "events", "signalrcore"],
    keywords = "exalus",
)