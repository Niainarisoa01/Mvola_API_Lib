# Guide d'authentification

Ce guide vous explique comment configurer et gérer l'authentification avec l'API MVola en utilisant la bibliothèque MVola API.

## Obtenir les identifiants API

Avant de pouvoir vous authentifier auprès de l'API MVola, vous devez obtenir vos identifiants API (Consumer Key et Consumer Secret) :

1. Créez un compte sur le [Portail Développeur MVola](https://developer.mvola.mg/)
2. Créez une nouvelle application dans votre tableau de bord développeur
3. Notez votre `Consumer Key` et `Consumer Secret`

## Types d'environnements

MVola offre deux environnements distincts :

- **Sandbox** : Environnement de test et de développement
- **Production** : Environnement de production pour les applications en direct

### Différences entre les environnements

| Caractéristique | Sandbox | Production |
|-----------------|---------|------------|
| Transactions réelles | Non | Oui |
| Limites de transaction | Illimitées | Selon la réglementation |
| URL de base | api-uat.orange.mg | api.orange.mg |
| Nécessite validation | Non | Oui |

## Configuration de l'authentification

### Initialisation directe

```python
from mvola_api import MVolaClient

# Initialisation pour l'environnement sandbox
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="Nom de votre application",
    partner_msisdn="0343500003",  # Votre numéro MVola
    sandbox=True  # Pour l'environnement de test
)
```

### Utilisation des variables d'environnement

Pour une meilleure sécurité, il est recommandé de stocker vos identifiants dans des variables d'environnement :

Créez un fichier `.env` à la racine de votre projet :

```
MVOLA_CONSUMER_KEY=votre_consumer_key
MVOLA_CONSUMER_SECRET=votre_consumer_secret
MVOLA_PARTNER_NAME=Nom de votre application
MVOLA_PARTNER_MSISDN=0343500003
MVOLA_SANDBOX=True
```

Puis, dans votre code :

```python
import os
from dotenv import load_dotenv
from mvola_api import MVolaClient

# Charger les variables d'environnement
load_dotenv()

# Initialisation avec les variables d'environnement
client = MVolaClient(
    consumer_key=os.getenv("MVOLA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MVOLA_CONSUMER_SECRET"),
    partner_name=os.getenv("MVOLA_PARTNER_NAME"),
    partner_msisdn=os.getenv("MVOLA_PARTNER_MSISDN"),
    sandbox=os.getenv("MVOLA_SANDBOX", "True").lower() == "true"
)
```

## Gestion des tokens

### Comment la bibliothèque gère les tokens

La bibliothèque MVola API gère automatiquement les tokens d'authentification pour vous :

1. La première fois que vous effectuez une opération, un token est généré
2. Ce token est stocké en mémoire
3. Pour les opérations suivantes, le token existant est utilisé
4. Si le token est expiré, un nouveau token est généré automatiquement

Vous n'avez généralement pas besoin de manipuler les tokens directement.

### Cycle de vie des tokens

```python
# Le token est généré automatiquement lors de la première utilisation
transaction_info = client.initiate_payment(...)

# Pour accéder manuellement au token (rarement nécessaire)
token = client.auth.get_valid_token()
print(f"Token: {token['access_token']}")
print(f"Expire dans: {token['expires_in']} secondes")

# Vérifier si un token est expiré
is_expired = client.auth.is_token_expired()
print(f"Token expiré: {is_expired}")

# Forcer le rafraîchissement du token
client.auth.refresh_token()
```

## Gestion des erreurs d'authentification

Les erreurs d'authentification sont gérées par des exceptions spécifiques :

```python
from mvola_api.exceptions import MVolaAuthError, MVolaInvalidCredentialsError

try:
    # Une opération qui nécessite une authentification
    client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        reference="REF123456",
        description="Paiement test"
    )
except MVolaInvalidCredentialsError as e:
    print(f"Identifiants API invalides: {e}")
    # Vérifiez vos consumer_key et consumer_secret
except MVolaAuthError as e:
    print(f"Erreur d'authentification: {e}")
    # Gérer les autres erreurs d'authentification
```

## Bonnes pratiques de sécurité

1. **Ne stockez jamais les identifiants API dans le code source** - Utilisez des variables d'environnement ou un service de gestion de secrets
2. **Ne partagez jamais vos identifiants API** - Chaque application doit avoir ses propres identifiants
3. **Utilisez HTTPS pour toutes les communications** - La bibliothèque MVola API le fait automatiquement
4. **Implémentez un système de rotation des identifiants** pour les applications de production
5. **Journalisez les tentatives d'authentification échouées** pour détecter les abus potentiels

## Passage en production

Lorsque vous êtes prêt à passer en production :

1. Obtenez des identifiants API de production auprès de MVola
2. Mettez à jour votre configuration pour utiliser `sandbox=False`
3. Assurez-vous que votre application respecte toutes les exigences de sécurité
4. Effectuez des tests de bout en bout avec des montants minimes avant de manipuler des transactions plus importantes

## Prochaines étapes

Une fois l'authentification configurée, vous pouvez commencer à effectuer des transactions. Consultez le [Guide des transactions](transactions.md) pour apprendre à initier des paiements et à vérifier leur statut. 