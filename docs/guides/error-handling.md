# Guide de gestion des erreurs

Ce guide explique comment gérer efficacement les erreurs qui peuvent survenir lors de l'utilisation de la bibliothèque MVola API.

## Introduction

La bibliothèque MVola API utilise un système d'exceptions hiérarchique pour vous permettre de gérer facilement les différents types d'erreurs qui peuvent se produire lors des opérations avec l'API MVola. Ce guide couvre les codes d'erreur standard de l'API MVola et comment les gérer efficacement dans votre application.

## Hiérarchie des exceptions

```
MVolaError (Exception de base)
├── MVolaAuthError (Erreurs d'authentification)
├── MVolaTransactionError (Erreurs de transaction)
├── MVolaValidationError (Erreurs de validation)
└── MVolaConnectionError (Erreurs de connexion)
```

Cette hiérarchie vous permet de capturer des erreurs à différents niveaux de spécificité selon vos besoins.

## Codes d'erreur HTTP de l'API MVola

L'API MVola utilise les codes d'erreur HTTP standard pour indiquer si une requête a réussi ou échoué. Voici les principaux codes que vous pourriez rencontrer :

| Code | Description | Traitement recommandé |
|------|-------------|------------------------|
| 200 | OK - La requête a réussi | Traiter la réponse normalement |
| 400 | Bad Request - Requête incorrecte | Vérifier les paramètres de votre requête |
| 401 | Unauthorized - Clé API invalide | Vérifier vos identifiants d'API ou générer un nouveau token |
| 402 | Request Failed - Requête échouée | Vérifier l'état du compte MVola ou les limites de transaction |
| 403 | Forbidden - Permissions insuffisantes | Demander les autorisations appropriées |
| 404 | Not Found - Ressource introuvable | Vérifier l'URL ou l'ID de la ressource |
| 409 | Conflict - Conflit de requêtes | Éviter les requêtes dupliquées |
| 429 | Too Many Requests - Limite atteinte | Implémenter un système de backoff exponentiel |
| 500-504 | Server Errors - Erreur serveur | Attendre et réessayer plus tard |

### Format des réponses d'erreur

Les erreurs de l'API MVola sont généralement retournées au format JSON :

```json
{
  "ErrorCategory": "Catégorie de l'erreur",
  "ErrorCode": "Code d'erreur spécifique",
  "ErrorDescription": "Description détaillée de l'erreur",
  "ErrorDateTime": "Date et heure de l'erreur",
  "ErrorParameters": {
    "key1": "value1"
  }
}
```

Pour les erreurs d'authentification, le format peut être différent :

```json
{
  "fault": {
    "code": 900901,
    "message": "Invalid Credentials",
    "description": "Invalid Credentials. Make sure you have given the correct access token"
  }
}
```

## Importation des exceptions

```python
from mvola_api.exceptions import (
    MVolaError,              # Exception de base
    MVolaAuthError,          # Erreurs d'authentification
    MVolaTransactionError,   # Erreurs de transaction
    MVolaValidationError,    # Erreurs de validation des paramètres
    MVolaConnectionError,    # Erreurs de connexion réseau
)
```

## Gestion basique des erreurs

La façon la plus simple de gérer les erreurs est d'utiliser un bloc try/except pour capturer toutes les erreurs MVola :

```python
from mvola_api import MVolaClient
from mvola_api.exceptions import MVolaError

try:
    # Initialiser le client
    client = MVolaClient(
        consumer_key="votre_consumer_key",
        consumer_secret="votre_consumer_secret",
        partner_name="Nom de votre application",
        partner_msisdn="0343500003",
        sandbox=True
    )

    # Initier un paiement
    transaction_info = client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Paiement test"
    )

    print(f"Transaction initiée avec succès: {transaction_info}")

except MVolaError as e:
    print(f"Une erreur MVola s'est produite: {e}")
    print(f"Code: {e.code}")
    # Gérer l'erreur (journalisation, notification, etc.)
```

## Gestion avancée des erreurs

Pour une gestion plus précise, vous pouvez capturer des types d'exceptions spécifiques :

```python
from mvola_api import MVolaClient
from mvola_api.exceptions import (
    MVolaAuthError,
    MVolaTransactionError,
    MVolaValidationError,
    MVolaConnectionError,
    MVolaError,
)

try:
    client = MVolaClient.from_env()

    transaction_info = client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Paiement test"
    )

    print(f"Transaction initiée avec succès: {transaction_info}")

except MVolaAuthError as e:
    print(f"Erreur d'authentification: {e}")
    # Vérifiez vos consumer_key et consumer_secret

except MVolaValidationError as e:
    print(f"Données invalides: {e}")
    # Afficher des messages d'erreur spécifiques aux champs

except MVolaTransactionError as e:
    print(f"Erreur de transaction: {e}")
    # Gérer les erreurs spécifiques aux transactions

except MVolaConnectionError as e:
    print(f"Erreur de connexion: {e}")
    # Suggérer de vérifier la connexion Internet ou de réessayer plus tard

except MVolaError as e:
    print(f"Autre erreur MVola: {e}")
    # Gérer les autres erreurs MVola

except Exception as e:
    print(f"Erreur inattendue: {e}")
```

## Types d'erreurs spécifiques

### Erreurs d'authentification (MVolaAuthError)

Levée lorsque l'authentification échoue (identifiants invalides, token expiré, etc.).

```python
from mvola_api.exceptions import MVolaAuthError

try:
    client.generate_token()
except MVolaAuthError as e:
    print(f"Authentification échouée: {e}")
    print(f"Code HTTP: {e.code}")
    print(f"Réponse: {e.response}")
```

### Erreurs de transaction (MVolaTransactionError)

Levée lorsqu'une opération de transaction échoue.

```python
from mvola_api.exceptions import MVolaTransactionError

try:
    client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Paiement test"
    )
except MVolaTransactionError as e:
    print(f"Erreur de transaction: {e}")
    print(f"Code: {e.code}")
```

### Erreurs de validation (MVolaValidationError)

Levée lorsque les paramètres fournis ne passent pas la validation.

```python
from mvola_api.exceptions import MVolaValidationError

try:
    # Tentative avec des paramètres manquants
    client = MVolaClient(consumer_key=None, consumer_secret=None)
except MVolaValidationError as e:
    print(f"Erreur de validation: {e}")
```

### Erreurs de connexion (MVolaConnectionError)

Levée lorsqu'un problème de réseau empêche la communication avec l'API.

```python
from mvola_api.exceptions import MVolaConnectionError

try:
    status = client.get_transaction_status(server_correlation_id="id-12345")
except MVolaConnectionError as e:
    print(f"Problème de connexion: {e}")
    # Réessayer plus tard
```

## Techniques de gestion des erreurs

### Approche hiérarchique

Attrapez d'abord les exceptions les plus spécifiques, puis les plus générales :

```python
try:
    # Code utilisant MVola API
    pass
except MVolaAuthError as e:
    print(f"Erreur d'authentification: {e}")
except MVolaValidationError as e:
    print(f"Erreur de validation: {e}")
except MVolaTransactionError as e:
    print(f"Erreur de transaction: {e}")
except MVolaConnectionError as e:
    print(f"Erreur de connexion: {e}")
except MVolaError as e:
    print(f"Autre erreur MVola: {e}")
except Exception as e:
    print(f"Erreur inattendue: {e}")
```

### Gestion avec retries

Pour certaines erreurs temporaires (timeout, erreurs serveur), vous pouvez implémenter une stratégie de retry :

```python
from mvola_api.exceptions import MVolaConnectionError, MVolaError
import time

max_retries = 3
retry_count = 0
backoff_factor = 2

while retry_count < max_retries:
    try:
        result = client.initiate_payment(
            amount=1000,
            debit_msisdn="0343500003",
            credit_msisdn="0343500004",
            description="Paiement test"
        )
        break  # Succès

    except MVolaConnectionError as e:
        retry_count += 1

        if retry_count >= max_retries:
            print(f"Échec après {max_retries} tentatives: {e}")
            raise

        wait_time = backoff_factor ** retry_count
        print(f"Erreur temporaire: {e}. Nouvelle tentative dans {wait_time}s...")
        time.sleep(wait_time)
```

## Validation préventive

Pour éviter certaines exceptions, validez vos données avant d'appeler l'API :

```python
from mvola_api.utils import validate_msisdn, validate_description

# Valider les numéros de téléphone
if not validate_msisdn("0343500003"):
    print("Numéro de téléphone invalide")

# Valider la description
is_valid, error_msg = validate_description("Paiement pour produit ABC")
if not is_valid:
    print(f"Description invalide: {error_msg}")
```

## Journalisation des erreurs

Il est recommandé de journaliser les erreurs pour faciliter le débogage :

```python
import logging

logger = logging.getLogger("mvola")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("mvola_errors.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

try:
    result = client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Paiement test"
    )
except MVolaError as e:
    logger.error(f"Erreur MVola: {e}", exc_info=True)
    logger.error(f"Code: {e.code}")
    print("Une erreur s'est produite. Veuillez réessayer plus tard.")
```

## Messages d'erreur conviviaux

Transformez les erreurs techniques en messages compréhensibles pour l'utilisateur final :

```python
from mvola_api.exceptions import (
    MVolaAuthError,
    MVolaTransactionError,
    MVolaValidationError,
    MVolaConnectionError,
    MVolaError,
)

def get_user_friendly_message(exception):
    """Convertit une exception MVola en message utilisateur convivial"""

    if isinstance(exception, MVolaAuthError):
        return "Impossible de se connecter au service MVola. Veuillez contacter le support."
    elif isinstance(exception, MVolaValidationError):
        return "Certaines informations fournies ne sont pas valides. Veuillez vérifier et réessayer."
    elif isinstance(exception, MVolaTransactionError):
        return "Impossible de traiter la transaction. Veuillez réessayer plus tard."
    elif isinstance(exception, MVolaConnectionError):
        return "Problème de connexion au service MVola. Vérifiez votre connexion Internet."
    elif isinstance(exception, MVolaError):
        return "Une erreur s'est produite lors du traitement. Veuillez réessayer plus tard."
    else:
        return "Une erreur inattendue s'est produite."

# Utilisation
try:
    result = client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Test"
    )
except Exception as e:
    logger.error(f"Erreur: {e}", exc_info=True)
    print(get_user_friendly_message(e))
```

## Bonnes pratiques

1. **Utilisez la hiérarchie d'exceptions** pour capturer les erreurs à différents niveaux de spécificité.
2. **Validez les données en amont** pour éviter les erreurs prévisibles.
3. **Implémentez des retries** pour les erreurs temporaires, avec un backoff exponentiel.
4. **Journalisez les erreurs** avec suffisamment de contexte pour faciliter le débogage.
5. **Présentez des messages conviviaux** à l'utilisateur final, sans exposer les détails techniques.
6. **Testez vos scénarios d'erreur** pour vous assurer que votre application les gère correctement.

## Voir aussi

- [Référence des exceptions](../api-reference/exceptions.md) - Documentation technique détaillée
- [Guide d'authentification](authentication.md) - Comment gérer l'authentification
- [Guide des transactions](transactions.md) - Comment effectuer des transactions