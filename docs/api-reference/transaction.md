# Référence du module de transaction

Le module de transaction `mvola_api.transaction` gère toutes les opérations de paiement et de vérification de statut auprès de l'API MVola. Ce module permet d'initier des paiements, de vérifier leur statut et de récupérer les détails des transactions.

## Classe MVolaTransaction

La classe `MVolaTransaction` est responsable de toutes les opérations liées aux transactions financières via l'API MVola.

### Initialisation

```python
from mvola_api.transaction import MVolaTransaction
from mvola_api.auth import MVolaAuth

# Initialiser l'authentification
auth = MVolaAuth(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    sandbox=True  # Utiliser False pour l'environnement de production
)

# Initialiser le gestionnaire de transactions
transaction = MVolaTransaction(
    auth=auth,
    partner_name="NOM_DU_PARTENAIRE",
    partner_msisdn="0343500003",
    language="FR",  # Optionnel, par défaut "FR"
    logger=None     # Optionnel, un logger personnalisé
)
```

## Opérations principales

### Initier un paiement

```python
try:
    transaction_info = transaction.initiate_payment(
        amount=1000,                             # Montant en ariary
        debit_msisdn="0343500003",               # Numéro qui paie
        credit_msisdn="0343500004",              # Numéro qui reçoit
        reference="REF123456",                   # Référence unique
        description="Paiement pour produit ABC", # Description
        callback_url="https://example.com/callback"  # URL de notification (optionnel)
    )
    
    # Récupérer l'ID de la transaction pour suivi ultérieur
    transaction_id = transaction_info.get('server_correlation_id')
    print(f"Transaction initiée avec succès. ID: {transaction_id}")
    
except Exception as e:
    print(f"Erreur lors de l'initiation du paiement: {e}")
```

### Vérifier le statut d'une transaction

```python
try:
    status_info = transaction.get_transaction_status(
        transaction_id="transaction-id-12345",
        msisdn="0343500003"  # MSISDN associé à la transaction
    )
    
    status = status_info.get('status')
    print(f"Statut de la transaction: {status}")
    
except Exception as e:
    print(f"Erreur lors de la vérification du statut: {e}")
```

### Récupérer les détails d'une transaction

```python
try:
    transaction_details = transaction.get_transaction_details(
        transaction_id="transaction-id-12345"
    )
    
    print(f"Détails de la transaction: {transaction_details}")
    
except Exception as e:
    print(f"Erreur lors de la récupération des détails: {e}")
```

## Structure des données de transaction

### Résultat de l'initiation d'un paiement

```python
{
    'status': 'pending',                 # Statut initial de la transaction
    'server_correlation_id': '12345678-1234-1234-1234-123456789012',  # ID de transaction
    'notification_method': 'polling',    # Méthode de notification (polling ou callback)
    'reference': 'REF123456',            # Référence fournie lors de la création
    'request_date': '2024-07-24T10:15:30.000Z'  # Date de la demande
}
```

### Statut d'une transaction

```python
{
    'status': 'completed',               # Statut actuel (pending, completed, failed, rejected, cancelled)
    'transaction_id': '12345678-1234-1234-1234-123456789012',  # ID de transaction
    'amount': '1000',                    # Montant de la transaction
    'currency': 'Ar',                    # Devise (Ariary)
    'financialTransactionId': '12345678',  # ID financier unique
    'reason': '',                        # Raison du statut, généralement présent en cas d'échec
    'date': '2024-07-24T10:15:30.000Z'   # Date de mise à jour du statut
}
```

### Détails d'une transaction

```python
{
    'status': 'completed',                # Statut final de la transaction
    'amount': '1000',                     # Montant de la transaction
    'currency': 'Ar',                     # Devise
    'financialTransactionId': '12345678',  # ID financier
    'externalId': 'REF123456',            # Référence externe (celle fournie à l'initiation)
    'debitParty': [                       # Information sur le payeur
        {
            'key': 'msisdn',
            'value': '0343500003'
        }
    ],
    'creditParty': [                      # Information sur le bénéficiaire
        {
            'key': 'msisdn',
            'value': '0343500004'
        }
    ],
    'fees': {                             # Frais associés à la transaction
        'amount': '20',
        'currency': 'Ar'
    },
    'creationDate': '2024-07-24T10:15:30.000Z'  # Date de création de la transaction
}
```

## Validation des données

Le module de transaction effectue une validation approfondie des données avant d'envoyer des requêtes à l'API MVola:

```python
# Formats acceptés pour les numéros de téléphone
# - 034XXXXXXX, 038XXXXXXX, etc. (format national)
# - 0XXXXXXXXX (format générique)

# Validation du montant
# - Doit être un nombre positif
# - Doit respecter les limites de transaction MVola

# Validation de la référence
# - Doit être unique
# - Ne doit pas contenir certains caractères spéciaux
```

## Exceptions spécifiques aux transactions

Le module de transaction peut lever les exceptions suivantes :

- `MVolaTransactionError`: Exception de base pour les erreurs de transaction
  - `MVolaTransactionValidationError`: Levée lorsque les données de transaction sont invalides
  - `MVolaTransactionStatusError`: Levée lorsqu'une vérification de statut échoue
  - `MVolaTransactionCreationError`: Levée lorsque la création d'une transaction échoue

```python
from mvola_api.exceptions import (
    MVolaTransactionError,
    MVolaTransactionValidationError,
    MVolaTransactionStatusError,
    MVolaTransactionCreationError
)

try:
    transaction_info = transaction.initiate_payment(...)
except MVolaTransactionValidationError as e:
    print(f"Erreur de validation: {e}")
except MVolaTransactionCreationError as e:
    print(f"Erreur de création: {e}")
except MVolaTransactionError as e:
    print(f"Erreur de transaction: {e}")
```

## Fonctionnement interne

### Endpoints des transactions

Le module utilise différents endpoints en fonction de l'environnement:

**Sandbox**:
- Initiation de paiement: `https://api-uat.orange.mg/mvola/mm/transactions/type/merchantpay`
- Vérification de statut: `https://api-uat.orange.mg/mvola/mm/transactions/{transaction_id}`
- Détails de transaction: `https://api-uat.orange.mg/mvola/mm/transactions/{transaction_id}`

**Production**:
- Initiation de paiement: `https://api.orange.mg/mvola/mm/transactions/type/merchantpay`
- Vérification de statut: `https://api.orange.mg/mvola/mm/transactions/{transaction_id}`
- Détails de transaction: `https://api.orange.mg/mvola/mm/transactions/{transaction_id}`

### En-têtes de requête

```python
headers = {
    "Authorization": "Bearer {token}",
    "Version": "1.0",
    "X-Correlation-ID": "{uuid4}",  # Identifiant unique généré pour chaque requête
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "*/*"
}
```

## Bonnes pratiques

1. **Générez des références uniques** pour chaque transaction. La bibliothèque n'impose pas ce comportement, mais c'est fortement recommandé.

2. **Stockez les IDs de transaction** retournés par l'API pour un suivi ultérieur. Ces identifiants sont essentiels pour vérifier le statut.

3. **Implémentez un système de retry** pour vérifier le statut des transactions jusqu'à ce qu'elles soient terminées.

4. **Utilisez les webhooks** (URL de callback) lorsque c'est possible, plutôt que de faire des sondages répétés.

5. **Vérifiez toujours le statut final** d'une transaction avant de considérer un paiement comme réussi.

## Voir aussi

- [Guide des transactions](../guides/transactions.md) - Guide complet sur les transactions MVola
- [Référence MVolaClient](client.md) - Documentation de la classe principale qui utilise MVolaTransaction
- [Gestion des Webhooks](../examples/webhook-handling.md) - Comment gérer les notifications de transaction 