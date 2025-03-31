# Transactions

Ce guide explique comment effectuer des transactions avec la bibliothèque MVola API. Après avoir configuré l'authentification, vous pourrez initier des paiements, vérifier leur statut et récupérer les détails des transactions.

## Concepts de base

Dans le système MVola, une transaction se compose généralement de ces éléments essentiels :

- **Montant** : Le montant à transférer
- **MSISDN débiteur** : Le numéro de téléphone qui effectue le paiement
- **MSISDN créditeur** : Le numéro de téléphone qui reçoit le paiement
- **Référence** : Une référence unique pour identifier la transaction
- **URL de callback** (optionnel) : Une URL pour recevoir des notifications sur le statut de la transaction

## Initier un paiement

La méthode `initiate_payment()` de `MVolaTransaction` vous permet d'initier un paiement. Voici un exemple :

```python
from mvola_api import MVolaClient

# Initialisation du client
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="NOM_DU_PARTENAIRE",
    partner_msisdn="0343500003",
    sandbox=True  # Utiliser False pour l'environnement de production
)

# Informations de transaction
payment_data = {
    "amount": 1000,
    "debit_msisdn": "0343500003",  # Numéro qui paie
    "credit_msisdn": "0343500004",  # Numéro qui reçoit
    "reference": "REF123456",  # Référence unique
    "description": "Paiement pour produit ABC"
}

# Initier le paiement
try:
    transaction_info = client.initiate_payment(
        **payment_data,
        callback_url="https://example.com/callback"  # Optionnel
    )
    
    # Récupérer l'ID de la transaction pour un suivi ultérieur
    transaction_id = transaction_info.get('server_correlation_id')
    print(f"Paiement initié avec succès. ID de transaction: {transaction_id}")
    
except Exception as e:
    print(f"Erreur lors de l'initiation du paiement: {e}")
```

## Vérifier le statut d'une transaction

Après avoir initié un paiement, vous pouvez vérifier son statut à l'aide de la méthode `get_transaction_status()` :

```python
try:
    status_info = client.get_transaction_status(
        transaction_id=transaction_id,
        msisdn="0343500003"  # MSISDN du compte partenaire
    )
    
    print(f"Statut de la transaction: {status_info.get('status')}")
    
except Exception as e:
    print(f"Erreur lors de la vérification du statut: {e}")
```

## Récupérer les détails d'une transaction

Vous pouvez récupérer les détails d'une transaction à l'aide de la méthode `get_transaction_details()` :

```python
try:
    transaction_details = client.get_transaction_details(
        transaction_id=transaction_id
    )
    
    print(f"Détails de la transaction: {transaction_details}")
    
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
    transaction_info = client.initiate_payment(**payment_data)
    
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
```

## Meilleures pratiques

1. **Générez des références uniques** pour chaque transaction.
2. **Stockez les IDs de transaction** retournés par l'API pour un suivi ultérieur.
3. **Implémentez un système de retry** pour vérifier le statut des transactions jusqu'à ce qu'elles soient terminées.
4. **Utilisez des webhooks** pour être notifié des changements de statut des transactions plutôt que de faire des sondages répétés.

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
    sandbox=True
)

# Informations de transaction
payment_data = {
    "amount": 1000,
    "debit_msisdn": "0343500003",
    "credit_msisdn": "0343500004",
    "reference": "REF123456",
    "description": "Paiement pour produit ABC"
}

def process_payment():
    try:
        # Initier le paiement
        transaction_info = client.initiate_payment(**payment_data)
        transaction_id = transaction_info.get('server_correlation_id')
        print(f"Paiement initié avec succès. ID: {transaction_id}")
        
        # Vérifier le statut (avec des tentatives)
        max_attempts = 5
        attempts = 0
        status = None
        
        while attempts < max_attempts:
            status_info = client.get_transaction_status(
                transaction_id=transaction_id,
                msisdn="0343500003"
            )
            status = status_info.get('status')
            print(f"Statut actuel: {status}")
            
            if status.lower() == 'completed':
                # Récupérer les détails de la transaction
                details = client.get_transaction_details(transaction_id=transaction_id)
                print(f"Transaction réussie! Détails: {details}")
                return True
            elif status.lower() in ['failed', 'cancelled', 'rejected']:
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