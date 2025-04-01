# MVola API Library

Bienvenue dans la documentation de la bibliothèque MVola API.

## Introduction

MVola API Library est une bibliothèque Python robuste conçue pour faciliter l'intégration des services de paiement mobile MVola dans vos applications. Cette bibliothèque vous permet d'interagir avec les API de MVola de manière simple et intuitive, en gérant automatiquement l'authentification, la validation des paramètres, et le traitement des erreurs.

## Documentation complète de l'API

**La documentation complète de l'API MVola est disponible [ici](documentation.md).**

Cette documentation détaillée contient:
- Configuration du portail développeur
- Endpoints d'API et paramètres
- Structures de requêtes et réponses
- Codes d'erreur
- Bonnes pratiques
- Environnement de test

## Installation

```bash
pip install mvola-api-lib
```

## Fonctionnalités principales

- ✅ Gestion des jetons d'authentification
- ✅ Paiements marchands (initiation, statut, détails)
- ✅ Support des environnements Sandbox et Production
- ✅ Validation des paramètres
- ✅ Gestion robuste des erreurs
- ✅ Journalisation intégrée

## Utilisation rapide

Pour un démarrage rapide, consultez les exemples dans la section [Guide d'utilisation](guides/installation.md).

## Formats de documentation

La documentation est disponible en plusieurs formats:

- [Documentation en ligne](https://niainarisoa01.github.io/Mvlola_API_Lib/)
- [Documentation PDF](output/mvola_api_documentation.pdf) (si disponible)
- [Documentation Markdown sur GitHub](https://github.com/Niainarisoa01/Mvlola_API_Lib/blob/main/docs/documentation.md)

## Support

Pour toute question technique, contactez:
- Le support MVola via le portail développeur
- Créez une [issue sur GitHub](https://github.com/Niainarisoa01/Mvlola_API_Lib/issues)

## Fonctionnalités

- ✅ API simple et intuitive pour l'intégration des paiements MVola
- ✅ Gestion automatique des tokens d'authentification
- ✅ Support complet des opérations de paiement marchand
- ✅ Gestion complète des erreurs et validation des paramètres
- ✅ Support de journalisation
- ✅ Compatible avec les environnements sandbox et production

## Démarrage rapide

```python
from mvola_api import MVolaClient

# Initialiser le client
client = MVolaClient(
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret",
    partner_name="Your Application Name",
    partner_msisdn="0340000000",  # Votre numéro marchand
    sandbox=True  # Utiliser l'environnement sandbox
)

# Générer un token
token_data = client.generate_token()
print(f"Token généré: {token_data['access_token'][:10]}...")

# Initier un paiement
result = client.initiate_payment(
    amount=10000,
    debit_msisdn="0343500003",  # Numéro du client
    credit_msisdn="0343500004",  # Numéro du marchand
    description="Paiement pour service",
    callback_url="https://example.com/callback"
)

# Suivre l'ID de corrélation du serveur pour les vérifications de statut
server_correlation_id = result['response']['serverCorrelationId']
print(f"Transaction initiée avec l'ID de corrélation: {server_correlation_id}")

# Vérifier le statut de la transaction
status = client.get_transaction_status(server_correlation_id)
print(f"Statut de la transaction: {status['response']['status']}")
```

## Tests en sandbox

Pour les tests en sandbox, utilisez les numéros de téléphone de test suivants :
- 0343500003
- 0343500004

## Structure de la documentation

Cette documentation a été structurée selon le framework [Diátaxis](https://diataxis.fr/), qui organise l'information en quatre sections distinctes :

1. **Guides d'utilisation** - Orientés apprentissage, pour vous aider à comprendre les concepts
2. **Exemples** - Orientés problèmes, pour résoudre des cas d'utilisation spécifiques
3. **Référence API** - Orientés information, documentation technique détaillée
4. **Explication** - Orientés compréhension, pour expliquer les choix et l'architecture

## Contribution

Les contributions sont les bienvenues ! Consultez notre [guide de contribution](contributing.md) pour plus d'informations.

## Licence

Ce projet est sous licence [MIT](https://opensource.org/licenses/MIT). 