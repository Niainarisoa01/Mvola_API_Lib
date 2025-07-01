# Installation

Ce guide vous aidera à installer la bibliothèque MVola API dans votre environnement Python.

## Prérequis

- Python 3.7 ou supérieur
- pip (gestionnaire de paquets Python)
- Un compte développeur MVola avec des clés d'API (pour l'utilisation réelle)

## Installation depuis PyPI

La méthode recommandée est d'installer la bibliothèque directement depuis PyPI :

```bash
pip install mvola-api-lib
```

Pour installer une version spécifique :

```bash
pip install mvola-api-lib==1.0.0
```

## Installation avec les extras

Vous pouvez installer des dépendances supplémentaires en fonction de vos besoins :

```bash
# Pour le développement (tests, formatage, etc.)
pip install mvola-api-lib[dev]

# Pour générer la documentation
pip install mvola-api-lib[docs]

# Pour exécuter les exemples
pip install mvola-api-lib[examples]

# Pour tout installer
pip install mvola-api-lib[dev,docs,examples]
```

## Installation depuis les sources

Pour installer la dernière version de développement depuis GitHub :

```bash
git clone https://github.com/Niainarisoa01/Mvola_API_Lib.git
cd Mvola_API_Lib
pip install -e .
```

## Vérification de l'installation

Vous pouvez vérifier que l'installation a réussi en important la bibliothèque dans Python :

```python
import mvola_api
print(mvola_api.__version__)
```

## Configuration initiale

Après l'installation, vous devrez configurer la bibliothèque avec vos identifiants MVola Developer :

```python
from mvola_api import MVolaClient

# Configuration pour l'environnement sandbox
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="Nom de votre application",
    partner_msisdn="0343500003",  # Votre numéro MVola
    base_url="https://devapi.mvola.mg"  # URL pour l'environnement sandbox
)
```

## Inscription au portail MVola Developer

Pour obtenir vos identifiants d'API, vous devez créer un compte sur le portail MVola Developer :

1. Visitez [https://developer.mvola.mg/](https://developer.mvola.mg/)
2. Cliquez sur "Connectez-vous" puis "S'inscrire" si vous n'avez pas encore de compte
3. Suivez les instructions pour créer votre compte
4. Après avoir confirmé votre compte via l'email reçu, connectez-vous au portail
5. Déclarez votre application en fournissant les informations requises
6. Abonnez-vous aux API MVola que vous souhaitez utiliser
7. Générez vos clés API pour l'environnement sandbox

## Test dans l'environnement sandbox

L'environnement sandbox vous permet de tester l'intégration sans effectuer de transactions réelles :

1. Utilisez uniquement les numéros de test fournis dans la documentation (ex: 0343500003 et 0343500004)
2. Toutes les transactions initiées dans l'environnement sandbox doivent être approuvées manuellement via le portail développeur
3. Accédez à la section "Transaction Approvals" du portail pour approuver vos transactions de test

## Passage en production

Une fois que vous avez terminé vos tests dans l'environnement sandbox :

1. Cliquez sur le bouton "GO LIVE" dans le portail développeur
2. Suivez les instructions pour fournir les documents et informations requises
3. Une fois approuvée, vous recevrez vos clés API de production
4. Mettez à jour la configuration de votre application pour utiliser l'URL de production (https://api.mvola.mg)

## Prochaines étapes

Après l'installation, consultez le [guide d'authentification](authentication.md) pour apprendre à configurer l'authentification avec l'API MVola. 