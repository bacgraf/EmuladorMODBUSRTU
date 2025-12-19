"""Setup para instalação do EmuladorMODBUSRTU"""
from setuptools import setup, find_packages

with open("VERSION", "r") as f:
    version = f.read().strip()

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="emulador-modbus-rtu",
    version=version,
    author="Marcel Hilleshein",
    description="Emulador de BMS com protocolo Modbus RTU Serial",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seu-usuario/EmuladorMODBUSRTU",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.4.0",
        "pymodbus>=3.0.0",
        "pyserial>=3.5",
    ],
    entry_points={
        "console_scripts": [
            "emulador-bms=main:main",
        ],
    },
)
