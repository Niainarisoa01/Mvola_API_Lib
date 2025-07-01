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
    base_url="https://devapi.mvola.mg"  # URL de l'API (sandbox par défaut)
)

# Initialiser le gestionnaire de transactions
transaction = MVolaTransaction(
    auth=auth,
    base_url="https://devapi.mvola.mg",  # URL de l'API (sandbox par défaut)
    partner_name="NOM_DU_PARTENAIRE",
    partner_msisdn="0343500003"  # Format: 03XXXXXXXX
)
```

## Opérations principales

### Initier un paiement

```python
try:
    transaction_info = transaction.initiate_merchant_payment(
        amount="1000",                           # Montant en ariary (sous forme de chaîne)
        debit_msisdn="0343500003",               # Numéro qui paie (format: 03XXXXXXXX)
        credit_msisdn="0343500004",              # Numéro qui reçoit (format: 03XXXXXXXX)
        description="Paiement pour produit ABC", # Description (max 50 caractères)
        currency="Ar",                          # Devise (Ar par défaut)
        requesting_organisation_transaction_reference="REF123456",  # Référence unique (optionnel)
        original_transaction_reference="",       # Référence de transaction originale (optionnel)
        foreign_currency="USD",                  # Devise étrangère (optionnel)
        foreign_amount="2.5",                    # Montant en devise étrangère (optionnel)
        callback_url="https://example.com/callback",  # URL de notification (optionnel)
        correlation_id=None,                     # ID de corrélation (généré automatiquement si non fourni)
        user_language="FR"                       # Langue (FR ou MG)
    )
    
    # Récupérer les informations importantes
    server_correlation_id = transaction_info['response']['serverCorrelationId']
    status = transaction_info['response']['status']  # Généralement "pending" à ce stade
    notification_method = transaction_info['response']['notificationMethod']  # "callback" ou "polling"
    
    print(f"Transaction initiée avec succès. ID: {server_correlation_id}")
    print(f"Statut initial: {status}")
    print(f"Méthode de notification: {notification_method}")
    
except Exception as e:
    print(f"Erreur lors de l'initiation du paiement: {e}")
```

### Vérifier le statut d'une transaction

```python
try:
    status_info = transaction.get_transaction_status(
        server_correlation_id="correlation-id-12345",  # ID de corrélation reçu lors de l'initiation
        correlation_id=None,  # ID de corrélation pour cette requête (optionnel)
        user_language="FR"    # Langue (FR ou MG)
    )
    
    status = status_info['response']['status']
    print(f"Statut de la transaction: {status}")  # pending, completed, ou failed
    
    # Si la transaction est complétée, l'ID de transaction sera disponible
    if status == "completed" and 'objectReference' in status_info['response']:
        transaction_id = status_info['response']['objectReference']
        print(f"ID de transaction: {transaction_id}")
    
except Exception as e:
    print(f"Erreur lors de la vérification du statut: {e}")
```

### Récupérer les détails d'une transaction

```python
try:
    transaction_details = transaction.get_transaction_details(
        transaction_id="transaction-id-12345",  # ID de transaction obtenu après complétion
        correlation_id=None,  # ID de corrélation pour cette requête (optionnel)
        user_language="FR"    # Langue (FR ou MG)
    )
    
    details = transaction_details['response']
    print(f"Montant: {details.get('amount')} {details.get('currency')}")
    print(f"Statut: {details.get('transactionStatus')}")
    print(f"Référence: {details.get('transactionReference')}")
    print(f"Date: {details.get('createDate')}")
    
    # Informations sur le débiteur et le créditeur
    debit_party = next((party for party in details.get('debitParty', []) if party.get('key') == 'msisdn'), {})
    credit_party = next((party for party in details.get('creditParty', []) if party.get('key') == 'msisdn'), {})
    
    print(f"Débiteur: {debit_party.get('value')}")
    print(f"Créditeur: {credit_party.get('value')}")
    
    # Frais de transaction
    fee = next((f for f in details.get('fee', [])), {})
    print(f"Frais: {fee.get('feeAmount')}")
    
except Exception as e:
    print(f"Erreur lors de la récupération des détails: {e}")
```

## Structure des données de transaction

### Requête d'initiation de paiement

```python
headers = {
    "Authorization": "Bearer <ACCESS_TOKEN>",
    "Version": "1.0",
    "X-CorrelationID": "<ID_CORRELATION>",
    "UserLanguage": "FR",  # ou "MG"
    "UserAccountIdentifier": "msisdn;<MSISDN_PARTENAIRE>",
    "partnerName": "<NOM_PARTENAIRE>",
    "Content-Type": "application/json",
    "Cache-Control": "no-cache"
}

payload = {
    "amount": "1000",
    "currency": "Ar",
    "descriptionText": "Description du paiement",
    "requestDate": "2023-07-24T10:15:30.000Z",
    "requestingOrganisationTransactionReference": "REF123456",
    "originalTransactionReference": "",
    "debitParty": [{"key": "msisdn", "value": "0343500003"}],
    "creditParty": [{"key": "msisdn", "value": "0343500004"}],
    "metadata": [
        {"key": "partnerName", "value": "NomPartenaire"},
        {"key": "fc", "value": "USD"},  # Optionnel - devise étrangère
        {"key": "amountFc", "value": "2.5"}  # Optionnel - montant en devise étrangère
    ]
}
```

### Réponse d'initiation de paiement

```python
{
    "status": "pending",                 # Statut initial (toujours "pending")
    "serverCorrelationId": "421a22a2-ef1d-42bc-9452-f4939a3d5cdf",  # ID de corrélation
    "notificationMethod": "polling"      # Méthode de notification (polling ou callback)
}
```

### Réponse de statut de transaction

```python
{
    "status": "completed",              # pending, completed, ou failed
    "serverCorrelationId": "421a22a2-ef1d-42bc-9452-f4939a3d5cdf",
    "notificationMethod": "polling",
    "objectReference": "transactionID123"  # Disponible uniquement si status = "completed"
}
```

### Réponse de détails de transaction

```python
{
    "amount": "1000",
    "currency": "Ar",
    "transactionReference": "transactionID123",
    "transactionStatus": "completed",    # ou "failed"
    "createDate": "2023-07-24T10:15:30.000Z",
    "debitParty": [
        {"key": "msisdn", "value": "0343500003"}
    ],
    "creditParty": [
        {"key": "msisdn", "value": "0343500004"}
    ],
    "fee": [
        {"feeAmount": "20"}
    ],
    "metadata": [
        {"key": "originalTransactionResult", "value": "0"},
        {"key": "originalTransactionResultDesc", "value": "Success"}
    ]
}
```

### Réponse de callback (succès)

```python
{
    "transactionStatus": "completed",
    "serverCorrelationId": "421a22a2-ef1d-42bc-9452-f4939a3d5cdf",
    "transactionReference": "641235",
    "requestDate": "2023-07-24T10:15:30.000Z",
    "debitParty": [
        {"key": "msisdn", "value": "0343500003"}
    ],
    "creditParty": [
        {"key": "msisdn", "value": "0343500004"}
    ],
    "fees": [
        {"feeAmount": "20"}
    ],
    "metadata": [
        {"key": "string", "value": "string"}
    ]
}
```

### Réponse de callback (échec)

```python
{
    "transactionStatus": "failed",
    "serverCorrelationId": "421a22a2-ef1d-42bc-9452-f4939a3d5cdf",
    "transactionReference": "641235",
    "requestDate": "2023-07-24T10:15:30.000Z",
    "debitParty": [
        {"key": "msisdn", "value": "0343500003"}
    ],
    "creditParty": [
        {"key": "msisdn", "value": "0343500004"}
    ],
    "metadata": [
        {"key": "string", "value": "string"}
    ]
}
```

## Validation des données

Le module de transaction effectue une validation approfondie des données avant d'envoyer des requêtes à l'API MVola:

```python
# Validation du montant
# - Doit être un nombre positif

# Validation de la description
# - Max 50 caractères
# - Seuls les caractères suivants sont autorisés: alphanumériques, espace, tiret, point, underscore, virgule

# Validation des numéros MSISDN
# - Format national malgache (034XXXXXXX, etc.)
```

## Endpoints des transactions

Le module utilise les endpoints suivants:

**Sandbox**:
- Initiation de paiement: `https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/`
- Vérification de statut: `https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/status/{serverCorrelationId}`
- Détails de transaction: `https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/{transactionId}`

**Production**:
- Initiation de paiement: `https://api.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/`
- Vérification de statut: `https://api.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/status/{serverCorrelationId}`
- Détails de transaction: `https://api.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/{transactionId}`

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

## Format d'erreur d'authentification

```json
{
    "fault": {
        "code": 900901,
        "message": "Invalid Credentials",
        "description": "Invalid Credentials. Make sure you have given the correct access token"
    }
}
```

## Bonnes pratiques

1. **Générez des références uniques** pour chaque transaction. Utilisez le paramètre `requesting_organisation_transaction_reference` pour faciliter le suivi côté client.

2. **Stockez les IDs de corrélation** retournés par l'API (`serverCorrelationId`) pour vérifier le statut ultérieurement.

3. **Implémentez un système de retry** pour vérifier le statut des transactions jusqu'à ce qu'elles soient terminées.

4. **Utilisez les webhooks** (URL de callback) lorsque c'est possible, plutôt que de faire des sondages répétés.

5. **Vérifiez toujours le statut final** d'une transaction avant de considérer un paiement comme réussi.

6. **Validez la description** en vous assurant qu'elle ne dépasse pas 50 caractères et qu'elle ne contient que les caractères autorisés.

7. **Utilisez l'environnement sandbox** avec les numéros de test (0343500003 et 0343500004) pour vos développements.

## Voir aussi

- [Guide des transactions](../guides/transactions.md) - Guide complet sur les transactions MVola
- [Référence MVolaClient](client.md) - Documentation de la classe principale qui utilise MVolaTransaction
- [Gestion des Webhooks](../examples/webhook-handling.md) - Comment gérer les notifications de transaction 