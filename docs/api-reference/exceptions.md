# Référence des exceptions

Le module `mvola_api.exceptions` définit toutes les exceptions spécifiques à la bibliothèque MVola API. Ces exceptions vous permettent de gérer précisément les différents types d'erreurs qui peuvent survenir lors de l'utilisation de l'API.

## Hiérarchie des exceptions

La bibliothèque utilise une hiérarchie d'exceptions pour vous permettre de capturer des catégories spécifiques d'erreurs :

```
MVolaError (Exception de base)
├── MVolaAuthError (Erreurs d'authentification)
├── MVolaTransactionError (Erreurs de transaction)
├── MVolaValidationError (Erreurs de validation)
└── MVolaConnectionError (Erreurs de connexion)
```

## Exception de base

### MVolaError

Classe de base pour toutes les erreurs spécifiques à la bibliothèque MVola API. Elle étend la classe `Exception` standard de Python et ajoute des attributs pour le code d'erreur et la réponse HTTP.

```python
from mvola_api.exceptions import MVolaError

try:
    # Code utilisant MVola API
    pass
except MVolaError as e:
    print(f"Message: {e.message}")
    print(f"Code HTTP: {e.code}")
    print(f"Réponse: {e.response}")
```

#### Attributs

| Attribut | Type | Description |
|----------|------|-------------|
| `message` | `str` | Message d'erreur descriptif |
| `code` | `int` ou `None` | Code d'erreur HTTP (ex: 401, 500) |
| `response` | `Response` ou `None` | Objet réponse HTTP complet |

#### Méthode `__str__`

L'affichage de l'exception inclut le code d'erreur s'il est présent :

```python
# Avec code : "[401] Invalid Credentials"
# Sans code : "Consumer key and secret are required"
```

## Exceptions d'authentification

### MVolaAuthError

Levée lorsqu'une erreur se produit pendant l'authentification avec l'API MVola (identifiants invalides, token expiré, erreur serveur lors de la génération du token).

```python
from mvola_api.exceptions import MVolaAuthError

try:
    client.generate_token()
except MVolaAuthError as e:
    print(f"Code d'erreur HTTP: {e.code}")
    print(f"Message d'erreur: {e.message}")
    print(f"Réponse complète: {e.response}")
```

**Causes courantes :**

- Consumer Key ou Consumer Secret invalide
- Compte développeur désactivé
- Erreur serveur côté MVola

## Exceptions de transaction

### MVolaTransactionError

Levée lorsqu'une erreur se produit pendant une opération de transaction (initiation de paiement, vérification de statut, récupération des détails).

```python
from mvola_api.exceptions import MVolaTransactionError

try:
    client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Test"
    )
except MVolaTransactionError as e:
    print(f"Erreur de transaction: {e}")
    print(f"Code: {e.code}")
```

**Causes courantes :**

- Solde insuffisant
- Numéro de téléphone non enregistré chez MVola
- Transaction dupliquée (conflit)
- Erreur de l'API MVola lors du traitement

## Exceptions de validation

### MVolaValidationError

Levée lorsque les paramètres fournis ne passent pas la validation côté client, avant même d'envoyer une requête à l'API.

```python
from mvola_api.exceptions import MVolaValidationError

try:
    # Consumer key manquant
    client = MVolaClient(consumer_key=None, consumer_secret=None)
except MVolaValidationError as e:
    print(f"Validation échouée: {e}")
```

**Causes courantes :**

- Consumer Key ou Consumer Secret manquant
- Partner Name non fourni
- Paramètres de transaction manquants ou invalides

## Exceptions de connexion

### MVolaConnectionError

Levée lorsqu'un problème de réseau empêche la communication avec l'API MVola.

```python
from mvola_api.exceptions import MVolaConnectionError

try:
    client.get_transaction_status(server_correlation_id="id-12345")
except MVolaConnectionError as e:
    print(f"Problème de connexion: {e}")
```

**Causes courantes :**

- Pas de connexion Internet
- Timeout de la requête (> 30 secondes)
- Serveur MVola indisponible

## Formats d'erreur de l'API MVola

L'API MVola renvoie des erreurs dans deux formats différents selon le type d'erreur.

### Format d'erreur standard

```json
{
    "ErrorCategory": "Error category",
    "ErrorCode": "Error Code",
    "ErrorDescription": "Description on the error",
    "ErrorDateTime": "Date and time when the error occurred",
    "ErrorParameters": {
        "key1": "value1"
    }
}
```

### Format d'erreur d'authentification

```json
{
    "fault": {
        "code": 900901,
        "message": "Invalid Credentials",
        "description": "Invalid Credentials. Make sure you have given the correct access token"
    }
}
```

La bibliothèque MVola API transforme ces formats d'erreur en exceptions Python appropriées, en préservant toutes les informations pertinentes.

## Stratégies de gestion des erreurs

### Approche par type spécifique

Attrapez d'abord les exceptions les plus spécifiques, puis les plus générales :

```python
from mvola_api.exceptions import (
    MVolaAuthError,
    MVolaTransactionError,
    MVolaValidationError,
    MVolaConnectionError,
    MVolaError,
)

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

Pour certaines erreurs temporaires (connexion, timeout), implémentez une stratégie de retry :

```python
from mvola_api.exceptions import MVolaConnectionError
import time

max_retries = 3
retry_count = 0

while retry_count < max_retries:
    try:
        result = client.initiate_payment(
            amount=1000,
            debit_msisdn="0343500003",
            credit_msisdn="0343500004",
            description="Test"
        )
        break
    except MVolaConnectionError as e:
        retry_count += 1
        if retry_count >= max_retries:
            print(f"Échec après {max_retries} tentatives: {e}")
            raise

        wait_time = 2 ** retry_count  # Backoff exponentiel
        print(f"Erreur temporaire: {e}. Tentative {retry_count}/{max_retries} dans {wait_time}s")
        time.sleep(wait_time)
```

## Codes d'erreur HTTP

L'API utilise les codes d'erreur HTTP standard :

| Code | Description |
|------|-------------|
| 200 | OK - La requête a réussi |
| 400 | Bad Request - Requête incorrecte |
| 401 | Unauthorized - Identifiants invalides |
| 402 | Request Failed - Requête échouée |
| 403 | Forbidden - Permissions insuffisantes |
| 404 | Not Found - Ressource introuvable |
| 409 | Conflict - Conflit avec une autre requête |
| 429 | Too Many Requests - Trop de requêtes |
| 500-504 | Server Errors - Erreur serveur |

## Bonnes pratiques

1. **Utilisez des exceptions spécifiques** : Attrapez les exceptions les plus spécifiques pertinentes pour votre cas d'utilisation.
2. **Journalisez les détails** : Les exceptions contiennent `code` et `response` — journalisez-les.
3. **Implémentez des retries** : Pour les erreurs temporaires, mettez en place un backoff exponentiel.
4. **Validez en amont** : Utilisez `validate_msisdn()` et `validate_description()` avant d'appeler l'API.
5. **Traitement spécifique** : Certaines erreurs nécessitent un traitement adapté dans votre application.

## Voir aussi

- [Guide de gestion des erreurs](../guides/error-handling.md) - Stratégies complètes
- [Référence MVolaClient](client.md) - Documentation de la classe principale
- [Utilisation basique](../examples/basic-usage.md) - Exemples incluant la gestion des erreurs