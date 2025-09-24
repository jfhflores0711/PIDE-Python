from setuptools import setup, find_packages

setup(
    name="pide_client",
    version="0.1.0",
    packages=find_packages(include=["reniec", "sunarp", "web", "reniec.*", "sunarp.*", "web.*"]),
    install_requires=[
        "requests>=2.31.0",
        "Flask>=2.3.2",
        "python-dotenv>=1.0.0"
    ],
    entry_points={
        "console_scripts": [
            "pide-web = web.app:main"
        ]
    },
    python_requires=">=3.8",
)