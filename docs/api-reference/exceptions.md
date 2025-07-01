# Référence des exceptions

Le module `mvola_api.exceptions` définit toutes les exceptions spécifiques à la bibliothèque MVola API. Ces exceptions vous permettent de gérer précisément les différents types d'erreurs qui peuvent survenir lors de l'utilisation de l'API.

## Hiérarchie des exceptions

La bibliothèque utilise une hiérarchie d'exceptions pour vous permettre de capturer des catégories spécifiques d'erreurs :

```
MVolaError (Exception de base)
├── MVolaAuthError (Erreurs d'authentification)
│   └── MVolaInvalidCredentialsError
├── MVolaTransactionError (Erreurs de transaction)
│   ├── MVolaTransactionValidationError
│   ├── MVolaTransactionStatusError
│   └── MVolaTransactionCreationError
├── MVolaValidationError (Erreurs de validation)
│   ├── MVolaInvalidParameterError
│   └── MVolaInvalidDescriptionError
├── MVolaConnectionError (Erreurs de connexion)
│   ├── MVolaRequestTimeoutError
│   └── MVolaServerError
└── MVolaConfigError (Erreurs de configuration)
```

## Exception de base

`MVolaError`

Cette classe est l'exception de base pour toutes les erreurs spécifiques à la bibliothèque MVola API. Elle étend la classe `Exception` standard de Python et ajoute des fonctionnalités supplémentaires pour la gestion des erreurs.

```python
try:
    # Code utilisant MVola API
except mvola_api.exceptions.MVolaError as e:
    print(f"Une erreur MVola s'est produite: {e}")
    print(f"Détails supplémentaires: {e.details if hasattr(e, 'details') else 'Aucun'}")
    print(f"Code HTTP: {e.status_code if hasattr(e, 'status_code') else 'N/A'}")
```

## Exceptions d'authentification

`MVolaAuthError`

Cette classe représente les erreurs liées à l'authentification avec l'API MVola.

### MVolaInvalidCredentialsError

Levée lorsque les identifiants fournis (consumer_key, consumer_secret) sont invalides ou incorrects.

```python
try:
    auth.generate_token()
except mvola_api.exceptions.MVolaInvalidCredentialsError as e:
    print(f"Identifiants invalides: {e}")
    print(f"Message d'erreur: {e.message}")
    print(f"Code d'erreur: {e.code}")
    print(f"Description: {e.description}")
```

## Exceptions de transaction

`MVolaTransactionError`

Cette classe représente les erreurs qui se produisent lors des opérations de transaction.

### MVolaTransactionValidationError

Levée lorsque les données de transaction ne passent pas la validation (montant incorrect, numéro de téléphone invalide, description non conforme, etc.).

```python
try:
    transaction.initiate_merchant_payment(amount="-100", ...)  # Montant négatif
except mvola_api.exceptions.MVolaTransactionValidationError as e:
    print(f"Erreur de validation: {e}")
    print(f"Champ en erreur: {e.field}")
    print(f"Détails: {e.details}")
```

### MVolaTransactionStatusError

Levée lorsqu'une erreur se produit pendant la vérification du statut d'une transaction.

```python
try:
    transaction.get_transaction_status(server_correlation_id="id-inexistant", ...)
except mvola_api.exceptions.MVolaTransactionStatusError as e:
    print(f"Erreur de statut: {e}")
    print(f"ID de corrélation: {e.server_correlation_id}")
    print(f"Code d'erreur: {e.error_code}")
    print(f"Description: {e.error_description}")
```

### MVolaTransactionCreationError

Levée lorsqu'une erreur se produit pendant la création d'une transaction.

```python
try:
    transaction.initiate_merchant_payment(...)
except mvola_api.exceptions.MVolaTransactionCreationError as e:
    print(f"Erreur lors de la création de la transaction: {e}")
    print(f"Catégorie d'erreur: {e.error_category}")
    print(f"Code d'erreur: {e.error_code}")
    print(f"Description: {e.error_description}")
    print(f"Date et heure: {e.error_datetime}")
    print(f"Paramètres: {e.error_parameters}")
```

## Exceptions de validation

`MVolaValidationError`

Cette classe représente les erreurs de validation des paramètres et données.

### MVolaInvalidParameterError

Levée lorsqu'un paramètre fourni est invalide pour une opération.

```python
try:
    client = MVolaClient(consumer_key=None, ...)  # consumer_key manquant
except mvola_api.exceptions.MVolaInvalidParameterError as e:
    print(f"Paramètre invalide: {e}")
    print(f"Nom du paramètre: {e.parameter_name}")
    print(f"Raison: {e.reason}")
```

### MVolaInvalidDescriptionError

Levée lorsque le texte de description ne respecte pas les contraintes de l'API MVola (max 50 caractères, caractères spéciaux limités).

```python
try:
    # Description trop longue ou avec caractères non autorisés
    transaction.initiate_merchant_payment(
        description="Texte avec caractères spéciaux interdits ! @ # $ % ^ & * ( )",
        ...
    )
except mvola_api.exceptions.MVolaInvalidDescriptionError as e:
    print(f"Description invalide: {e}")
    print(f"Texte fourni: {e.description}")
    print(f"Raison: {e.reason}")
```

## Exceptions de connexion

`MVolaConnectionError`

Cette classe représente les erreurs de connexion à l'API MVola.

### MVolaRequestTimeoutError

Levée lorsqu'une requête dépasse le délai d'attente configuré.

```python
try:
    transaction.initiate_merchant_payment(...)
except mvola_api.exceptions.MVolaRequestTimeoutError as e:
    print(f"Délai d'attente dépassé: {e}")
    print(f"URL: {e.url}")
    print(f"Temps écoulé: {e.timeout} secondes")
```

### MVolaServerError

Levée lorsque le serveur MVola renvoie une erreur (500, 502, 503, etc.).

```python
try:
    transaction.initiate_merchant_payment(...)
except mvola_api.exceptions.MVolaServerError as e:
    print(f"Erreur serveur MVola: {e}")
    print(f"Code HTTP: {e.status_code}")
    print(f"URL: {e.url}")
    print(f"Réponse: {e.response}")
```

## Exceptions de configuration

`MVolaConfigError`

Cette classe représente les erreurs de configuration de la bibliothèque.

```python
try:
    # Tentative d'initialisation avec une configuration incomplète
    client = MVolaClient(...)
except mvola_api.exceptions.MVolaConfigError as e:
    print(f"Erreur de configuration: {e}")
```

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
        "key1": "value1",
        "key2": "value2"
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
try:
    # Code utilisant MVola API
except mvola_api.exceptions.MVolaInvalidCredentialsError as e:
    # Gérer les erreurs d'identifiants spécifiquement
    print(f"Identifiants invalides: {e}")
except mvola_api.exceptions.MVolaAuthError as e:
    # Gérer les autres erreurs d'authentification
    print(f"Erreur d'authentification: {e}")
except mvola_api.exceptions.MVolaTransactionValidationError as e:
    # Gérer les erreurs de validation
    print(f"Erreur de validation: {e}")
except mvola_api.exceptions.MVolaTransactionError as e:
    # Gérer les autres erreurs de transaction
    print(f"Erreur de transaction: {e}")
except mvola_api.exceptions.MVolaConnectionError as e:
    # Gérer les erreurs de connexion
    print(f"Erreur de connexion: {e}")
except mvola_api.exceptions.MVolaError as e:
    # Gérer toutes les autres erreurs MVola
    print(f"Erreur MVola: {e}")
except Exception as e:
    # Attraper toutes les autres exceptions Python
    print(f"Erreur inattendue: {e}")
```

### Gestion avec retries

Pour certaines erreurs temporaires (timeout, erreurs serveur), vous pouvez implémenter une stratégie de retry :

```python
from mvola_api.exceptions import MVolaRequestTimeoutError, MVolaServerError
import time

max_retries = 3
retry_count = 0

while retry_count < max_retries:
    try:
        result = transaction.initiate_merchant_payment(...)
        # Succès, sortie de la boucle
        break
    except (MVolaRequestTimeoutError, MVolaServerError) as e:
        retry_count += 1
        if retry_count >= max_retries:
            print(f"Échec après {max_retries} tentatives: {e}")
            raise
        
        wait_time = 2 ** retry_count  # Backoff exponentiel
        print(f"Erreur temporaire: {e}. Tentative {retry_count}/{max_retries} dans {wait_time}s")
        time.sleep(wait_time)
```

## Codes d'erreur HTTP

L'API utilise les codes d'erreur HTTP standard:

- **200 - OK**: Tout a fonctionné comme prévu.
- **400 - Bad Request**: La requête est inacceptable, souvent en raison d'un paramètre manquant.
- **401 - Unauthorized**: Aucune clé API valide fournie.
- **402 - Request Failed**: Les paramètres étaient valides mais la requête a échoué.
- **403 - Forbidden**: La clé API n'a pas les permissions pour effectuer la requête.
- **404 - Not Found**: La ressource demandée n'existe pas.
- **409 - Conflict**: La requête est en conflit avec une autre requête.
- **429 - Too Many Requests**: Trop de requêtes envoyées à l'API trop rapidement.
- **500, 502, 503, 504 - Server Errors**: Une erreur s'est produite sur le serveur.

## Bonnes pratiques

1. **Utilisez des exceptions spécifiques** : Attrapez les exceptions les plus spécifiques pertinentes pour votre cas d'utilisation.

2. **Journalisez les détails** : Les exceptions contiennent des informations utiles pour le débogage - journalisez-les.

3. **Implémentez des retries** : Pour les erreurs temporaires, mettez en place une logique de retry avec backoff exponentiel.

4. **Validez en amont** : Pour éviter certaines exceptions de validation, validez vos données avant d'appeler l'API.

5. **Backoff exponentiel** : En cas d'erreur 429 (trop de requêtes), implémentez un délai exponentiel entre les tentatives.

6. **Traitement spécifique** : Certaines erreurs, comme les soldes insuffisants ou les numéros invalides, nécessitent un traitement spécifique dans votre application.

## Voir aussi

- [Guide de gestion des erreurs](../guides/error-handling.md) - Stratégies complètes pour la gestion des erreurs
- [Référence MVolaClient](client.md) - Documentation de la classe principale
- [Utilisation basique](../examples/basic-usage.md) - Exemples incluant la gestion des erreurs