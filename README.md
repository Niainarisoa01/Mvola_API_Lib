# MVola API Python Library

A robust Python library for integrating with MVola mobile payment API in Madagascar.

## Installation

```bash
pip install mvola-api-lib
```

Pour utiliser les variables d'environnement (recommandé), installez également:

```bash
pip install python-dotenv
```

## Documentation

La documentation complète de l'API est disponible dans [docs/documentation.md](docs/documentation.md).

Pour consulter la documentation en ligne, visitez [https://niainarisoa01.github.io/Mvola_API_Lib/documentation/](https://niainarisoa01.github.io/Mvola_API_Lib/documentation/)

## Features

- Simple and intuitive API for MVola payment integration
- Handles authentication token generation and management with `EXT_INT_MVOLA_SCOPE` scope
- Supports merchant payment operations
- Comprehensive error handling
- Logging support
- Built-in parameter validation
- Works with both sandbox and production environments
- Support for environment variables to securely store credentials

## Variables d'environnement

Pour une gestion sécurisée des identifiants API, utilisez les variables d'environnement:

1. Créez un fichier `.env` à la racine de votre projet:

```
# MVola API credentials
MVOLA_CONSUMER_KEY=votre_consumer_key
MVOLA_CONSUMER_SECRET=votre_consumer_secret
MVOLA_PARTNER_NAME=Nom de votre application
MVOLA_PARTNER_MSISDN=0343500004
MVOLA_SANDBOX=True
```

2. Chargez ces variables dans votre code:

```python
from mvola_api import MVolaClient
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Créer un client à partir des variables d'environnement
client = MVolaClient.from_env()
```

## Known Limitations

**API Sandbox Limitations**

Lors des tests avec l'environnement sandbox MVola, nous avons identifié certaines limitations:

1. **Erreur "Missing field" (code 4001)** : L'API sandbox peut retourner cette erreur même lorsque tous les champs obligatoires mentionnés dans la documentation sont présents dans la requête. Cette erreur est particulièrement fréquente lors de l'initiation de paiement.

2. **Authentification vs. Transactions** : L'authentification (génération de token) fonctionne correctement, mais l'initiation de transaction peut échouer malgré la validité du token et la présence de tous les champs requis.

3. **Champs fc et amountFc** : Ces champs de métadonnées sont requis selon la documentation (et ont été ajoutés à l'implémentation), mais leur présence ne garantit pas le succès de l'opération dans l'environnement sandbox.

4. **Traitement des webhooks** : Le retour des callbacks peut ne pas fonctionner dans l'environnement sandbox comme décrit dans la documentation.

**Solutions de contournement**

- Pour les applications de production, nous recommandons de tester directement dans l'environnement de production (après validation préalable avec MVola).
- Si vous ne pouvez pas tester en production, vérifiez que vous utilisez bien les numéros sandbox (0343500003 et 0343500004).
- Vérifiez régulièrement si MVola a mis à jour son environnement sandbox.

## Quick Start

```python
"""
MVola API Library - Guide de démarrage rapide

Ce script démontre comment utiliser la bibliothèque MVola API pour:
1. Initialiser un client MVola
2. Générer un token d'authentification
3. Initier un paiement
4. Suivre l'état d'une transaction
5. Obtenir les détails d'une transaction

Pour plus d'informations, consultez la documentation complète: 
https://github.com/Niainarisoa01/Mvola_API_Lib
"""

from mvola_api import MVolaClient
import time
from dotenv import load_dotenv

# ======================================================
# 1. INITIALISATION DU CLIENT
# ======================================================

# Méthode 1: Utilisation des variables d'environnement (recommandée)
# Chargez le fichier .env contenant vos credentials
load_dotenv()

# Création du client à partir des variables d'environnement
client = MVolaClient.from_env()

# Méthode 2: Initialisation directe
# client = MVolaClient(
#    consumer_key="your_consumer_key",  # Obtenu du portail développeur MVola
#    consumer_secret="your_consumer_secret",  # Obtenu du portail développeur MVola
#    partner_name="nom de votre entreprise",  # Nom de votre application/entreprise
#    partner_msisdn="0343500004",  # En sandbox, utilisez uniquement 0343500004
#    sandbox=True  # True pour sandbox, False pour production
# )

# ======================================================
# 2. AUTHENTIFICATION - GÉNÉRATION DE TOKEN
# ======================================================
# Un token est valide pendant 1 heure
# La bibliothèque gère automatiquement le renouvellement
token_data = client.generate_token()
print(f"Token généré: {token_data['access_token'][:10]}...")  # Ne jamais afficher le token complet

# ======================================================
# 3. INITIER UN PAIEMENT
# ======================================================
# REMARQUE IMPORTANTE: Dans l'environnement sandbox MVola:
# - Utilisez uniquement 0343500003 et 0343500004
result = client.initiate_payment(
    amount=1000,  # Montant en Ariary (minimum 100)
    currency="Ar",  # Devise (Ariary)
    debit_msisdn="0343500003",  # Numéro du débiteur (celui qui paie)
    credit_msisdn="0343500004",  # Numéro du créditeur (celui qui reçoit)
    description="Test Transaction",  # Description de la transaction (max 50 caractères)
    callback_url="https://example.com/callback"  # URL où MVola enverra des notifications (recommandé)
)

# ======================================================
# 4. SUIVI DE LA TRANSACTION
# ======================================================
# L'ID de corrélation est nécessaire pour suivre l'état de la transaction
server_correlation_id = result['response']['serverCorrelationId']
print(f"Transaction initiée avec l'ID de corrélation: {server_correlation_id}")

# 4.1 Vérification initiale du statut
print("\n=== Test de get_transaction_status (statut initial) ===")
status_result = client.get_transaction_status(server_correlation_id)
print(f"Statut de la transaction: {status_result['response']['status']}")

# 4.2 Suivi automatique du statut - boucle de vérification
# La transaction peut prendre du temps pour être traitée
print("\n=== Boucle de vérification du statut ===")
max_attempts = 10  # Maximum d'essais
waiting_time = 3   # Secondes entre chaque vérification
current_attempt = 1
transaction_status = status_result['response']['status']

# La boucle continue jusqu'à ce que le statut change ou le nombre max de tentatives soit atteint
while transaction_status == "pending" and current_attempt <= max_attempts:
    print(f"Tentative {current_attempt}/{max_attempts} - Statut actuel: {transaction_status}")
    print(f"Attente de {waiting_time} secondes avant nouvelle vérification...")
    time.sleep(waiting_time)
    
    # Vérification périodique du statut
    status_result = client.get_transaction_status(server_correlation_id)
    transaction_status = status_result['response']['status']
    current_attempt += 1

print(f"\nStatut final après {current_attempt-1} vérifications: {transaction_status}")

# 4.3 Interprétation du statut final
# Les statuts possibles sont: pending, completed, failed
if transaction_status == "pending":
    print("En attente d'approbation")
    print("La transaction est toujours en attente après toutes les tentatives de vérification.")
    print("Vous devrez peut-être l'approuver manuellement dans le portail développeur MVola.")
elif transaction_status == "completed":
    print("La transaction est Réussie")
    print("Le paiement a été approuvé et traité avec succès.")
elif transaction_status == "failed":
    print("Échec de transaction")
    print("Le paiement a été rejeté ou a échoué pendant le traitement.")
else:
    print(f"Statut final: {transaction_status}")
    print("Statut non reconnu ou en cours de traitement.")

# ======================================================
# 5. DÉTAILS DE LA TRANSACTION
# ======================================================
# Obtient des informations complètes sur la transaction
print("\n=== Test de get_transaction_details ===")

# L'objectReference est l'ID unique de la transaction, nécessaire pour obtenir les détails
transaction_id = status_result.get('objectReference')

if transaction_id and transaction_id.strip():
    print(f"ID de transaction obtenu: {transaction_id}")
    
    try:
        # Récupération des détails complets
        details_result = client.get_transaction_details(transaction_id)
        print(f"Détails de la transaction: {details_result}")
        
        # Accès aux détails spécifiques
        amount = details_result.get('amount')
        currency = details_result.get('currency')
        transaction_status = details_result.get('transactionStatus')
        
        print(f"Montant: {amount} {currency}")
        print(f"Statut: {transaction_status}")
    except Exception as e:
        print(f"Erreur lors de la récupération des détails: {str(e)}")
else:
    print("L'objectReference est vide ou non disponible")
    
    # Explication selon le statut actuel
    if transaction_status == "pending":
        print("La transaction est encore en attente d'approbation")
        print("\nNote: Dans l'environnement sandbox, les transactions restent souvent en état 'pending'")
        print("Pour les tests, vous devriez approuver manuellement la transaction dans le portail développeur MVola")
    elif transaction_status == "completed":
        print("La transaction est complétée mais l'ID de référence n'est pas disponible")
        print("C'est inhabituel - vérifiez dans le portail développeur MVola")
    elif transaction_status == "failed":
        print("La transaction a échoué. Aucun ID de référence n'est généré pour les transactions échouées")
        print("Vérifiez les détails de l'échec dans le portail développeur MVola")
    else:
        print(f"La transaction a un statut inhabituel: {transaction_status}")
        print("Vérifiez le portail développeur MVola pour plus de détails")

# ======================================================
# REMARQUES SUPPLÉMENTAIRES
# ======================================================
# 1. En environnement sandbox, vous devrez approuver manuellement les transactions
#    dans le portail développeur MVola pour qu'elles passent à l'état "completed"
# 
# 2. Cette bibliothèque gère automatiquement:
#    - Le renouvellement du token d'authentification
#    - Le formatage des requêtes selon les attentes de l'API MVola
#    - La gestion des erreurs et exceptions
#
# 3. Pour l'environnement de production:
#    - Utilisez l'URL "https://api.mvola.mg" lors de l'initialisation du client
#    - Utilisez vos véritables numéros de téléphone MVola
#    - Assurez-vous d'avoir les autorisations nécessaires 
```

## Sandbox Testing

For sandbox testing, use the following test phone numbers:
- 0343500003
- 0343500004

## API Endpoints

The library supports the following MVola API endpoints:

1. **Authentication**: `POST /token` (with scope `EXT_INT_MVOLA_SCOPE`)
2. **Merchant Payment**: `POST /mvola/mm/transactions/type/merchantpay/1.0.0/`
3. **Transaction Details**: `GET /mvola/mm/transactions/type/merchantpay/1.0.0/{{transID}}`
4. **Transaction Status**: `GET /mvola/mm/transactions/type/merchantpay/1.0.0/status/{{serverCorrelationId}}`

## Error Handling

The library provides custom exceptions for different error types:

```python
from mvola_api import MVolaClient, MVolaError, MVolaAuthError, MVolaTransactionError

client = MVolaClient(...)

try:
    result = client.initiate_merchant_payment(...)
except MVolaAuthError as e:
    print(f"Authentication error: {e}")
except MVolaTransactionError as e:
    print(f"Transaction error: {e}")
except MVolaError as e:
    print(f"General MVola error: {e}")
```

## Using Environment Variables

You can use environment variables to store your MVola API credentials and configuration. This is a safer approach than hardcoding sensitive information in your code.

### 1. Create a .env file

Create a `.env` file in your project root with the following content:

```
# MVola API credentials
MVOLA_CONSUMER_KEY=your_consumer_key_here
MVOLA_CONSUMER_SECRET=your_consumer_secret_here

# MVola API configuration
MVOLA_PARTNER_NAME=Your Partner Name
MVOLA_PARTNER_MSISDN=your_partner_msisdn_here

# Environment (set to True for sandbox, False for production)
MVOLA_SANDBOX=True
```

### 2. Use the client with environment variables

```python
from mvola_api import MVolaClient

# Method 1: Load all settings from environment variables
client = MVolaClient.from_env()

# Method 2: Override specific settings
client = MVolaClient(
    # These will be loaded from environment variables if not provided
    consumer_key=None,
    consumer_secret=None,
    # Override environment variables with specific values
    partner_name="Custom Partner Name",
    sandbox=False  # Use production environment
)

# Use the client as usual
token_data = client.generate_token()
```

The library will automatically load the values from your `.env` file using python-dotenv.

### 3. Example with environment variables

See the complete example in [examples/env_example.py](examples/env_example.py).

## API Documentation

### MVolaClient

The main client class for interacting with MVola API.

#### Initialization

```python
client = MVolaClient(
    consumer_key,          # Consumer key from MVola Developer Portal
    consumer_secret,       # Consumer secret from MVola Developer Portal
    partner_name,          # Your application/merchant name
    partner_msisdn=None,   # Partner MSISDN (phone number)
    base_url="https://devapi.mvola.mg",  # API base URL (sandbox or production)
    logger=None            # Custom logger
)
```

#### Methods

- `generate_token(force_refresh=False)`: Generate an access token
- `initiate_merchant_payment(amount, currency, debit_msisdn, credit_msisdn, description, requesting_organisation_transaction_reference, ...)`: Initiate a merchant payment
- `get_transaction_status(server_correlation_id, user_language="FR")`: Get transaction status
- `get_transaction_details(transaction_id, user_language="FR")`: Get transaction details

## Best Practices

1. **Token Management**: The library handles token refresh automatically, but you can force a refresh if needed.
2. **Error Handling**: Always implement proper error handling in your application.
3. **Logging**: The library includes logging, but you can provide your own logger.
4. **Sandbox Testing**: Always test your integration in the sandbox environment before going live.
5. **Webhook Handling**: Implement proper webhook handling for transaction notifications.
6. **Description Length**: Keep transaction descriptions under 50 characters.
7. **References**: Always use unique `requesting_organisation_transaction_reference` values for each transaction.

## Development

### Requirements

- Python 3.6+
- requests library

### Installation for Development

```bash
git clone https://github.com/Niainarisoa01/Mvola_API_Lib.git
cd mvola_api
pip install -e .
```

## License

MIT

## Credits

Developed based on the official MVola API documentation. 