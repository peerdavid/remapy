from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="remapy",
    version="0.5.0",
    description="An open source file exporer for your reMarkable tablet.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/peerdavid/remapy",
    author="Peer David",
    packages=find_packages(where="."),
    python_requires=">=3.6, <4",
    install_requires=[
        "numpy",
        "Pillow",
        "pdfrw",
        "pyyaml",
        "reportlab",
        "requests",
    ],
    package_data={
        "gui": ["icons/*.png"],
    },
    entry_points={
        "gui_scripts": [
            "remapy=rema:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/peerdavid/remapy/issues",
        "Source": "https://github.com/peerdavid/remapy",
    },
)
