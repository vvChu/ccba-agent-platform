from setuptools import find_packages, setup

setup(
    name="ccba-legal-intel",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "websocket-client",
        "python-docx",
        "pyyaml",
    ],
)
