# Installation

Ce guide vous aidera à installer la bibliothèque MVola API dans votre environnement Python.

## Prérequis

- Python 3.7 ou supérieur
- pip (gestionnaire de paquets Python)
- Un compte développeur MVola avec des clés d'API (pour l'utilisation réelle)

## Installation depuis PyPI

La méthode recommandée est d'installer la bibliothèque directement depuis PyPI :

```bash
pip install mvola-api
```

Pour installer une version spécifique :

```bash
pip install mvola-api==1.0.0
```

## Installation avec les extras

Vous pouvez installer des dépendances supplémentaires en fonction de vos besoins :

```bash
# Pour le développement (tests, formatage, etc.)
pip install mvola-api[dev]

# Pour générer la documentation
pip install mvola-api[docs]

# Pour exécuter les exemples
pip install mvola-api[examples]

# Pour tout installer
pip install mvola-api[dev,docs,examples]
```

## Installation depuis les sources

Pour installer la dernière version de développement depuis GitHub :

```bash
git clone https://github.com/Niainarisoa01/Mvlola_API_Lib.git
cd Mvlola_API_Lib
pip install -e .
```

## Vérification de l'installation

Vous pouvez vérifier que l'installation a réussi en important la bibliothèque dans Python :

```python
import mvola_api
print(mvola_api.__version__)
```

## Prochaines étapes

Après l'installation, consultez le [guide d'authentification](authentication.md) pour apprendre à configurer l'authentification avec l'API MVola. 