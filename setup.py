"""
Setup script for mvola_api package
"""
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mvola_api",
    version="1.0.0",
    author="Niainarisoa",
    author_email="niainarisoa.mail@gmail.com",
    description="Une bibliothèque Python robuste pour l'intégration de l'API de paiement MVola",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Niainarisoa01/Mvlola_API_Lib",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
    ],
    keywords="mvola, paiement, madagascar, telma, mobile money, api, fintech",
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.5b2",
            "flake8>=3.9.0",
            "isort>=5.9.0",
        ],
        "docs": [
            "mkdocs>=1.2.0",
            "mkdocs-material>=7.1.0",
            "mkdocstrings>=0.15.0",
            "mkdocstrings-python>=0.5.0",
        ],
    },
    project_urls={
        "Documentation": "https://Niainarisoa01.github.io/Mvlola_API_Lib/",
        "Source": "https://github.com/Niainarisoa01/Mvlola_API_Lib",
        "Bug Reports": "https://github.com/Niainarisoa01/Mvlola_API_Lib/issues",
    },
) 