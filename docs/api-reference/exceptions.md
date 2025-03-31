# Référence des exceptions

Le module `mvola_api.exceptions` définit toutes les exceptions spécifiques à la bibliothèque MVola API. Ces exceptions vous permettent de gérer précisément les différents types d'erreurs qui peuvent survenir lors de l'utilisation de l'API.

## Hiérarchie des exceptions

La bibliothèque utilise une hiérarchie d'exceptions pour vous permettre de capturer des catégories spécifiques d'erreurs :

```
MVolaError (Exception de base)
├── MVolaAuthError (Erreurs d'authentification)
│   ├── MVolaInvalidCredentialsError
│   └── MVolaTokenExpiredError
├── MVolaTransactionError (Erreurs de transaction)
│   ├── MVolaTransactionValidationError
│   ├── MVolaTransactionStatusError
│   └── MVolaTransactionCreationError
├── MVolaValidationError (Erreurs de validation)
│   └── MVolaInvalidParameterError
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
    print(f"Détails supplémentaires: {e.details}")
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
    print(f"Code d'erreur: {e.error_code}")
```

### MVolaTokenExpiredError

Levée lorsqu'un token d'authentification a expiré et qu'une opération tente de l'utiliser.

```python
try:
    transaction.initiate_payment(...)
except mvola_api.exceptions.MVolaTokenExpiredError as e:
    print(f"Token expiré: {e}")
    # Rafraîchir le token et réessayer
    auth.refresh_token()
    transaction.initiate_payment(...)
```

## Exceptions de transaction

`MVolaTransactionError`

Cette classe représente les erreurs qui se produisent lors des opérations de transaction.

### MVolaTransactionValidationError

Levée lorsque les données de transaction ne passent pas la validation (montant incorrect, numéro de téléphone invalide, etc.).

```python
try:
    transaction.initiate_payment(amount=-100, ...)  # Montant négatif
except mvola_api.exceptions.MVolaTransactionValidationError as e:
    print(f"Erreur de validation: {e}")
    print(f"Champ en erreur: {e.field}")
    print(f"Détails: {e.details}")
```

### MVolaTransactionStatusError

Levée lorsqu'une erreur se produit pendant la vérification du statut d'une transaction.

```python
try:
    transaction.get_transaction_status(transaction_id="id-inexistant", ...)
except mvola_api.exceptions.MVolaTransactionStatusError as e:
    print(f"Erreur de statut: {e}")
    print(f"ID de transaction: {e.transaction_id}")
```

### MVolaTransactionCreationError

Levée lorsqu'une erreur se produit pendant la création d'une transaction.

```python
try:
    transaction.initiate_payment(...)
except mvola_api.exceptions.MVolaTransactionCreationError as e:
    print(f"Erreur lors de la création de la transaction: {e}")
    print(f"Détails: {e.details}")
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

## Exceptions de connexion

`MVolaConnectionError`

Cette classe représente les erreurs de connexion à l'API MVola.

### MVolaRequestTimeoutError

Levée lorsqu'une requête dépasse le délai d'attente configuré.

```python
try:
    transaction.initiate_payment(...)
except mvola_api.exceptions.MVolaRequestTimeoutError as e:
    print(f"Délai d'attente dépassé: {e}")
    print(f"URL: {e.url}")
    print(f"Temps écoulé: {e.timeout} secondes")
```

### MVolaServerError

Levée lorsque le serveur MVola renvoie une erreur (500, 502, 503, etc.).

```python
try:
    transaction.initiate_payment(...)
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
except mvola_api.exceptions.MVolaTransactionError as e:
    # Gérer les erreurs de transaction
    print(f"Erreur de transaction: {e}")
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
        result = transaction.initiate_payment(...)
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

## Bonnes pratiques

1. **Utilisez des exceptions spécifiques** : Attrapez les exceptions les plus spécifiques pertinentes pour votre cas d'utilisation.

2. **Journalisez les détails** : Les exceptions contiennent des informations utiles pour le débogage - journalisez-les.

3. **Implémentez des retries** : Pour les erreurs temporaires, mettez en place une logique de retry avec backoff.

4. **Validez en amont** : Pour éviter certaines exceptions de validation, validez vos données avant d'appeler l'API.

5. **Informez clairement l'utilisateur** : Transformez les exceptions techniques en messages compréhensibles pour l'utilisateur final.

## Voir aussi

- [Guide de gestion des erreurs](../guides/error-handling.md) - Stratégies complètes pour la gestion des erreurs
- [Référence MVolaClient](client.md) - Documentation de la classe principale
- [Utilisation basique](../examples/basic-usage.md) - Exemples incluant la gestion des erreurs