# Transactions

Ce guide explique comment effectuer des transactions avec la bibliothèque MVola API. Après avoir configuré l'authentification, vous pourrez initier des paiements marchands, vérifier leur statut et récupérer les détails des transactions.

## Concepts de base

Dans le système MVola, une transaction de paiement marchand se compose généralement de ces éléments essentiels :

- **Montant** : Le montant à transférer (sans décimales)
- **Devise** : La devise (généralement "Ar" pour Ariary)
- **MSISDN débiteur** : Le numéro de téléphone qui effectue le paiement
- **MSISDN créditeur** : Le numéro de téléphone du marchand qui reçoit le paiement
- **Description** : Description de la transaction (maximum 50 caractères)
- **Référence** : Une référence unique pour identifier la transaction côté client (`requestingOrganisationTransactionReference`)
- **URL de callback** (optionnel) : Une URL pour recevoir des notifications sur le statut de la transaction

## Endpoints API

L'API MVola fournit trois endpoints principaux pour gérer les transactions :

1. **Initier une transaction** : `POST /mvola/mm/transactions/type/merchantpay/1.0.0/`
2. **Détails d'une transaction** : `GET /mvola/mm/transactions/type/merchantpay/1.0.0/{{transID}}`
3. **Statut d'une transaction** : `GET /mvola/mm/transactions/type/merchantpay/1.0.0/status/{{serverCorrelationId}}`

## Initier un paiement marchand

La méthode `initiate_merchant_payment()` de `MVolaTransaction` vous permet d'initier un paiement marchand. Voici un exemple :

```python
from mvola_api import MVolaClient

# Initialisation du client
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="NOM_DU_PARTENAIRE",
    partner_msisdn="0343500003",
    base_url="https://devapi.mvola.mg"  # URL pour l'environnement sandbox
)

# Informations de transaction
payment_data = {
    "amount": 1000,                           # Montant sans décimales
    "currency": "Ar",                         # Devise
    "debit_msisdn": "0343500003",             # Numéro qui paie
    "credit_msisdn": "0343500004",            # Numéro marchand qui reçoit
    "description": "Paiement pour produit ABC", # Max 50 caractères
    "requesting_organisation_transaction_reference": "REF123456", # Référence unique côté client
    "original_transaction_reference": "",     # Référence de transaction originale (optionnel)
    # Métadonnées optionnelles
    "metadata": {
        "fc": "USD",                          # Devise étrangère (optionnel)
        "amountFc": "1"                       # Montant en devise étrangère (optionnel)
    }
}

# Initier le paiement
try:
    transaction_info = client.initiate_merchant_payment(
        **payment_data,
        callback_url="https://example.com/callback"  # Optionnel
    )
    
    # Récupérer l'ID de corrélation serveur pour un suivi ultérieur
    server_correlation_id = transaction_info.get('serverCorrelationId')
    print(f"Paiement initié avec succès. ID de corrélation: {server_correlation_id}")
    print(f"Méthode de notification: {transaction_info.get('notificationMethod')}")
    
except Exception as e:
    print(f"Erreur lors de l'initiation du paiement: {e}")
```

## Réception des notifications par callback

Si vous fournissez une URL de callback, MVola enverra une notification PUT à cette URL lorsque le statut de la transaction change. Voici un exemple de traitement de ces notifications avec Flask :

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/callback', methods=['PUT'])
def mvola_callback():
    transaction_data = request.json
    
    # Récupérer les informations importantes
    transaction_status = transaction_data.get('transactionStatus')
    server_correlation_id = transaction_data.get('serverCorrelationId')
    transaction_reference = transaction_data.get('transactionReference')
    
    print(f"Notification reçue - Statut: {transaction_status}")
    print(f"ID de corrélation: {server_correlation_id}")
    print(f"Référence de transaction: {transaction_reference}")
    
    # Traiter selon le statut
    if transaction_status == 'completed':
        # Paiement réussi - mettre à jour votre base de données, etc.
        print("Transaction réussie!")
        # Accéder aux frais si nécessaire
        fees = transaction_data.get('fees', [])
        if fees:
            fee_amount = fees[0].get('feeAmount')
            print(f"Frais: {fee_amount}")
    elif transaction_status == 'failed':
        # Paiement échoué - gérer l'échec
        print("Transaction échouée!")
    
    # Toujours renvoyer un succès pour confirmer la réception de la notification
    return jsonify({'status': 'notification_received'}), 200

if __name__ == '__main__':
    app.run(port=5000)
```

## Vérifier le statut d'une transaction

Après avoir initié un paiement, vous pouvez vérifier son statut à l'aide de la méthode `get_transaction_status()` avec le `serverCorrelationId` :

```python
try:
    status_info = client.get_transaction_status(
        server_correlation_id=server_correlation_id
    )
    
    status = status_info.get('status')
    print(f"Statut de la transaction: {status}")
    
    # Traiter selon le statut
    if status == 'completed':
        print("Transaction réussie!")
    elif status == 'pending':
        print("Transaction en attente...")
    elif status == 'failed':
        print("Transaction échouée!")
    
except Exception as e:
    print(f"Erreur lors de la vérification du statut: {e}")
```

## Récupérer les détails d'une transaction

Vous pouvez récupérer les détails d'une transaction à l'aide de la méthode `get_transaction_details()` avec l'ID de transaction retourné par MVola :

```python
try:
    # Remarque: transID est l'identifiant de transaction MVola (transactionReference)
    transaction_details = client.get_transaction_details(
        transaction_id=transaction_reference
    )
    
    # Accéder aux détails de la transaction
    amount = transaction_details.get('amount')
    currency = transaction_details.get('currency')
    status = transaction_details.get('transactionStatus')
    create_date = transaction_details.get('createDate')
    
    # Accéder aux parties de la transaction
    debit_party = transaction_details.get('debitParty', [])
    credit_party = transaction_details.get('creditParty', [])
    
    # Extraire les MSISDNs
    debit_msisdn = next((item['value'] for item in debit_party if item['key'] == 'msisdn'), None)
    credit_msisdn = next((item['value'] for item in credit_party if item['key'] == 'msisdn'), None)
    
    print(f"Détails de la transaction: {transaction_id}")
    print(f"Montant: {amount} {currency}")
    print(f"Statut: {status}")
    print(f"Date de création: {create_date}")
    print(f"Payeur: {debit_msisdn}")
    print(f"Bénéficiaire: {credit_msisdn}")
    
except Exception as e:
    print(f"Erreur lors de la récupération des détails: {e}")
```

## Gestion des erreurs

Lors du traitement des transactions, plusieurs types d'erreurs peuvent survenir. La bibliothèque MVola API fournit des exceptions spécifiques pour vous aider à les gérer :

```python
from mvola_api.exceptions import (
    MVolaTransactionError,
    MVolaValidationError,
    MVolaConnectionError
)

try:
    transaction_info = client.initiate_merchant_payment(**payment_data)
    
except MVolaValidationError as e:
    print(f"Erreur de validation: {e}")
    # Gérer les erreurs de validation des données
    
except MVolaTransactionError as e:
    print(f"Erreur de transaction: {e}")
    # Gérer les erreurs spécifiques aux transactions
    
except MVolaConnectionError as e:
    print(f"Erreur de connexion: {e}")
    # Gérer les problèmes de connexion à l'API
    
except Exception as e:
    print(f"Erreur inattendue: {e}")
    # Gérer toute autre erreur inattendue

## Codes d'erreur HTTP

L'API MVola utilise les codes d'erreur HTTP standard pour indiquer le résultat des requêtes :

| Code | Description |
|------|-------------|
| 200 | OK - La requête a réussi |
| 400 | Bad Request - Requête incorrecte, souvent en raison d'un paramètre manquant |
| 401 | Unauthorized - Clé API invalide fournie |
| 402 | Request Failed - Les paramètres sont valides mais la requête a échoué |
| 403 | Forbidden - La clé API n'a pas les permissions nécessaires |
| 404 | Not Found - La ressource demandée n'existe pas |
| 409 | Conflict - La requête est en conflit avec une autre requête |
| 429 | Too Many Requests - Trop de requêtes envoyées à l'API trop rapidement |
| 500, 502, 503, 504 | Server Errors - Erreur au niveau du serveur |
```

## Codes d'erreur HTTP

L'API MVola utilise les codes d'erreur HTTP standard pour indiquer le résultat des requêtes :

| Code | Description |
|------|-------------|
| 200 | OK - La requête a réussi |
| 400 | Bad Request - Requête incorrecte, souvent en raison d'un paramètre manquant |
| 401 | Unauthorized - Clé API invalide fournie |
| 402 | Request Failed - Les paramètres sont valides mais la requête a échoué |
| 403 | Forbidden - La clé API n'a pas les permissions nécessaires |
| 404 | Not Found - La ressource demandée n'existe pas |
| 409 | Conflict - La requête est en conflit avec une autre requête |
| 429 | Too Many Requests - Trop de requêtes envoyées à l'API trop rapidement |
| 500, 502, 503, 504 | Server Errors - Erreur au niveau du serveur |

## Meilleures pratiques

1. **Générez des références uniques** pour chaque transaction en utilisant le champ `requestingOrganisationTransactionReference`.
2. **Stockez les IDs de corrélation** (`serverCorrelationId`) retournés par l'API pour un suivi ultérieur.
3. **Utilisez des webhooks** (URL de callback) pour être notifié des changements de statut des transactions.
4. **Implémentez un système de retry** pour vérifier le statut des transactions jusqu'à ce qu'elles soient terminées.
5. **Respectez la limite de 50 caractères** pour la description de la transaction.

## Exemple complet de flux de paiement

Voici un exemple complet qui combine l'initiation d'un paiement, la vérification du statut et la récupération des détails :

```python
import time
from mvola_api import MVolaClient
from mvola_api.exceptions import MVolaTransactionError

# Initialisation du client
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="NOM_DU_PARTENAIRE",
    partner_msisdn="0343500003",
    base_url="https://devapi.mvola.mg"
)

# Informations de transaction
payment_data = {
    "amount": 1000,
    "currency": "Ar",
    "debit_msisdn": "0343500003",
    "credit_msisdn": "0343500004",
    "description": "Paiement pour produit ABC",
    "requesting_organisation_transaction_reference": "REF123456"
}

def process_payment():
    try:
        # Initier le paiement
        transaction_info = client.initiate_merchant_payment(**payment_data)
        server_correlation_id = transaction_info.get('serverCorrelationId')
        print(f"Paiement initié avec succès. ID: {server_correlation_id}")
        
        # Vérifier le statut (avec des tentatives)
        max_attempts = 5
        attempts = 0
        transaction_reference = None
        
        while attempts < max_attempts:
            status_info = client.get_transaction_status(
                server_correlation_id=server_correlation_id
            )
            status = status_info.get('status')
            print(f"Statut actuel: {status}")
            
            # Si la transaction est terminée, récupérer sa référence
            if status == 'completed':
                transaction_reference = status_info.get('objectReference')
                print(f"Transaction réussie! Référence: {transaction_reference}")
                
                # Récupérer les détails complets
                if transaction_reference:
                    details = client.get_transaction_details(transaction_id=transaction_reference)
                    print(f"Détails complets: {details}")
                return True
            elif status in ['failed', 'cancelled', 'rejected']:
                print(f"La transaction a échoué avec le statut: {status}")
                return False
            
            attempts += 1
            # Attendre avant de vérifier à nouveau
            time.sleep(5)
        
        print("Nombre maximum de tentatives atteint")
        return False
        
    except MVolaTransactionError as e:
        print(f"Erreur de transaction: {e}")
        return False
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        return False

# Exécuter le processus de paiement
result = process_payment()
print(f"Résultat du paiement: {'Succès' if result else 'Échec'}")
```

## Prochaines étapes

Consultez le guide [Gestion des erreurs](error-handling.md) pour apprendre à gérer efficacement les erreurs qui peuvent survenir lors des transactions, ou le guide [Intégration web](../examples/web-integration.md) pour voir comment intégrer les paiements MVola dans une application web. 