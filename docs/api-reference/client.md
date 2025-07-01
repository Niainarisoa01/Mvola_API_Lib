# Client MVola API

Le `MVolaClient` est la classe principale qui vous permet d'interagir avec l'API MVola. Il encapsule les fonctionnalités des modules d'authentification et de transaction, offrant une interface unifiée et simple pour effectuer des opérations avec l'API MVola.

## Classe MVolaClient

La classe `MVolaClient` est le point d'entrée principal pour l'utilisation de la bibliothèque MVola API.

### Initialisation

```python
from mvola_api import MVolaClient

# Initialisation pour l'environnement sandbox (développement)
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="Nom de votre application",
    partner_msisdn="0343500003",  # Votre numéro MVola
    base_url="https://devapi.mvola.mg"  # URL de l'API (sandbox par défaut)
)

# Initialisation pour l'environnement de production
prod_client = MVolaClient(
    consumer_key="votre_consumer_key_prod",
    consumer_secret="votre_consumer_secret_prod",
    partner_name="Nom de votre application",
    partner_msisdn="0343500003",  # Votre numéro MVola
    base_url="https://api.mvola.mg"  # URL de l'API de production
)
```

### Utilisation d'un logger personnalisé

Vous pouvez fournir votre propre logger pour surveiller les opérations :

```python
import logging

# Configurer un logger personnalisé
logger = logging.getLogger("mvola_custom_logger")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Utiliser le logger personnalisé
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="Nom de votre application",
    partner_msisdn="0343500003",
    base_url="https://devapi.mvola.mg",
    logger=logger  # Fournir votre logger personnalisé
)
```

## Méthodes principales

### Gestion des tokens

```python
# Générer un token d'authentification
token = client.generate_token()
print(f"Token: {token['access_token']}")
print(f"Expire dans: {token['expires_in']} secondes")

# Obtenir directement la chaîne du token d'accès
access_token = client.get_access_token()
print(f"Token d'accès: {access_token}")
```

### Opérations de transaction

```python
# Initier un paiement merchant
transaction_info = client.initiate_merchant_payment(
    amount="1000",                # Montant en ariary (chaîne)
    debit_msisdn="0343500003",    # Numéro qui paie
    credit_msisdn="0343500004",   # Numéro qui reçoit
    description="Paiement pour produit ABC",  # Max 50 caractères
    currency="Ar",                # Devise (Ar par défaut)
    requesting_organisation_transaction_reference="REF123456",  # Référence unique (optionnel)
    original_transaction_reference="",  # Référence transaction originale (optionnel)
    callback_url="https://example.com/callback"  # URL de notification (optionnel)
)

# Récupérer l'ID de corrélation pour le suivi
server_correlation_id = transaction_info['response']['serverCorrelationId']
print(f"ID de corrélation: {server_correlation_id}")

# Vérifier le statut d'une transaction
status = client.get_transaction_status(
    server_correlation_id=server_correlation_id
)
print(f"Statut: {status['response']['status']}")  # pending, completed, ou failed

# Si la transaction est complétée, récupérer son ID
if status['response']['status'] == 'completed' and 'objectReference' in status['response']:
    transaction_id = status['response']['objectReference']
    
    # Récupérer les détails d'une transaction
    details = client.get_transaction_details(transaction_id=transaction_id)
    print(f"Montant: {details['response'].get('amount')} {details['response'].get('currency')}")
    print(f"Référence: {details['response'].get('transactionReference')}")
```

## Format des réponses

### Réponse d'initiation de transaction

```python
{
    'response': {
        'status': 'pending',  # Toujours "pending" à l'initiation
        'serverCorrelationId': '421a22a2-ef1d-42bc-9452-f4939a3d5cdf',  # ID pour suivi
        'notificationMethod': 'polling'  # ou "callback" si URL fournie
    },
    'status_code': 200,
    'headers': { ... }  # En-têtes de la réponse HTTP
}
```

### Réponse de statut de transaction

```python
{
    'response': {
        'status': 'completed',  # ou "pending", "failed"
        'serverCorrelationId': '421a22a2-ef1d-42bc-9452-f4939a3d5cdf',
        'notificationMethod': 'polling',
        'objectReference': 'transactionID123'  # Présent si status = "completed"
    },
    'status_code': 200,
    'headers': { ... }
}
```

### Réponse de détails de transaction

```python
{
    'response': {
        'amount': '1000',
        'currency': 'Ar',
        'transactionReference': 'transactionID123',
        'transactionStatus': 'completed',
        'createDate': '2023-07-24T10:15:30.000Z',
        'debitParty': [
            {'key': 'msisdn', 'value': '0343500003'}
        ],
        'creditParty': [
            {'key': 'msisdn', 'value': '0343500004'}
        ],
        'fee': [
            {'feeAmount': '20'}
        ],
        'metadata': [
            {'key': 'originalTransactionResult', 'value': '0'},
            {'key': 'originalTransactionResultDesc', 'value': 'Success'}
        ]
    },
    'status_code': 200,
    'headers': { ... }
}
```

## Gestion des erreurs

```python
from mvola_api.exceptions import MVolaError

try:
    # Tentative d'opération
    result = client.initiate_merchant_payment(...)
except MVolaError as e:
    print(f"Erreur MVola: {e}")
    print(f"Code HTTP: {getattr(e, 'status_code', 'N/A')}")
    print(f"Détails: {getattr(e, 'details', 'N/A')}")
```

## Notes importantes

1. **Gestion des tokens** : Le client gère automatiquement les tokens d'authentification, en les générant et les rafraîchissant au besoin.

2. **Environnements** : L'environnement sandbox (`https://devapi.mvola.mg`) doit être utilisé pour les tests avant de passer à la production (`https://api.mvola.mg`).

3. **Numéros de téléphone** : Les numéros de téléphone doivent être au format national malgache (ex: 034XXXXXXX).

4. **Description des transactions** : La description ne doit pas dépasser 50 caractères et ne peut contenir que des caractères alphanumériques, espaces, tirets, points, underscores et virgules.

5. **Références de transaction** : Utilisez `requesting_organisation_transaction_reference` pour associer vos propres identifiants aux transactions.

6. **Suivi des transactions** : Stockez toujours le `serverCorrelationId` retourné lors de l'initiation pour pouvoir vérifier le statut ultérieurement.

7. **Webhook vs Polling** : Si vous fournissez une URL de callback, MVola notifiera cette URL lorsque la transaction sera terminée. Sinon, vous devrez interroger l'API pour connaître le statut.

## Voir aussi

- [Guide d'authentification](../guides/authentication.md) - Guide complet sur l'authentification
- [Guide des transactions](../guides/transactions.md) - Guide complet sur les transactions
- [Référence d'authentification](auth.md) - Documentation détaillée du module d'authentification
- [Référence de transaction](transaction.md) - Documentation détaillée du module de transaction 