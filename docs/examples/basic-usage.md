# Utilisation basique

Ce guide fournit des exemples simples d'utilisation de la bibliothèque MVola API.

## Installation

Commencez par installer la bibliothèque :

```bash
 pip install mvola-api-lib
```

## Initialisation

Pour commencer à utiliser la bibliothèque MVola API, vous devez d'abord initialiser un client :

```python
from mvola_api import MVolaClient

# Initialisation pour l'environnement sandbox (développement)
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="Nom de votre application",
    partner_msisdn="0343500003",  # Votre numéro MVola
    base_url="https://devapi.mvola.mg"  # URL de l'API sandbox
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

## Génération d'un token

La bibliothèque gère automatiquement les tokens d'authentification, mais vous pouvez également générer un token manuellement :

```python
# Générer un token d'authentification
token = client.generate_token()
print(f"Token: {token['access_token']}")
print(f"Expire dans: {token['expires_in']} secondes")
print(f"Type: {token['token_type']}")
print(f"Scope: {token['scope']}")

# Obtenir directement le token d'accès (la méthode génère un nouveau token si nécessaire)
access_token = client.get_access_token()
print(f"Token d'accès: {access_token}")
```

## Initier un paiement

Pour initier un paiement MVola :

```python
try:
    transaction_info = client.initiate_merchant_payment(
        amount="1000",                           # Montant en ariary (chaîne)
        debit_msisdn="0343500003",               # Numéro qui paie
        credit_msisdn="0343500004",              # Numéro qui reçoit
        description="Paiement pour produit ABC", # Description (max 50 caractères)
        currency="Ar",                           # Devise (Ar par défaut)
        requesting_organisation_transaction_reference="REF123456",  # Référence unique (optionnel)
        callback_url="https://example.com/callback"  # URL de notification (optionnel)
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

## Vérifier le statut d'une transaction

Pour vérifier le statut d'une transaction en cours :

```python
try:
    status_info = client.get_transaction_status(
        server_correlation_id="server-correlation-id-12345"  # ID obtenu lors de l'initiation
    )
    
    status = status_info['response']['status']
    print(f"Statut de la transaction: {status}")  # pending, completed, ou failed
    
    # États possibles : pending, completed, failed
    if status == 'completed' and 'objectReference' in status_info['response']:
        transaction_id = status_info['response']['objectReference']
        print(f"Transaction réussie! ID de transaction: {transaction_id}")
    elif status == 'pending':
        print("Transaction en attente de confirmation...")
    else:
        print(f"Transaction terminée avec statut: {status}")
    
except Exception as e:
    print(f"Erreur lors de la vérification du statut: {e}")
```

## Récupérer les détails d'une transaction

Pour obtenir tous les détails d'une transaction terminée :

```python
try:
    # Note: Vous avez besoin de l'ID de transaction (objectReference) et non du server_correlation_id
    transaction_details = client.get_transaction_details(
        transaction_id="transaction-id-12345"  # ID obtenu après complétion
    )
    
    details = transaction_details['response']
    print(f"Montant: {details.get('amount')} {details.get('currency')}")
    print(f"Statut: {details.get('transactionStatus')}")
    print(f"Référence: {details.get('transactionReference')}")
    print(f"Date: {details.get('createDate')}")
    
    # Accéder aux informations du payeur
    debit_party = next((party for party in details.get('debitParty', []) if party.get('key') == 'msisdn'), {})
    print(f"Payeur: {debit_party.get('value')}")
    
    # Accéder aux informations du bénéficiaire
    credit_party = next((party for party in details.get('creditParty', []) if party.get('key') == 'msisdn'), {})
    print(f"Bénéficiaire: {credit_party.get('value')}")
    
    # Accéder aux frais
    fee = next((f for f in details.get('fee', [])), {})
    print(f"Frais: {fee.get('feeAmount')}")
    
except Exception as e:
    print(f"Erreur lors de la récupération des détails: {e}")
```

## Exemple complet

Voici un exemple complet qui combine plusieurs opérations :

```python
from mvola_api import MVolaClient
from mvola_api.exceptions import MVolaError, MVolaTransactionError
import uuid
import time

# Générer un ID de corrélation unique pour cette session
correlation_id = str(uuid.uuid4())

# Initialisation du client
try:
    client = MVolaClient(
        consumer_key="votre_consumer_key",
        consumer_secret="votre_consumer_secret",
        partner_name="Nom de votre application",
        partner_msisdn="0343500003",
        base_url="https://devapi.mvola.mg"
    )
    
    # Générer une référence unique pour la transaction
    reference = f"REF-{uuid.uuid4().hex[:8].upper()}"
    
    # Initier un paiement
    print("Initiation du paiement...")
    transaction_info = client.initiate_merchant_payment(
        amount="1000",
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Paiement test",
        requesting_organisation_transaction_reference=reference,
        correlation_id=correlation_id
    )
    
    server_correlation_id = transaction_info['response']['serverCorrelationId']
    print(f"Transaction initiée avec succès!")
    print(f"ID de corrélation du serveur: {server_correlation_id}")
    print(f"Référence: {reference}")
    
    # Vérifier le statut initial
    print("\nVérification du statut initial...")
    status_info = client.get_transaction_status(
        server_correlation_id=server_correlation_id,
        correlation_id=correlation_id
    )
    
    print(f"Statut initial: {status_info['response']['status']}")
    print("Veuillez confirmer la transaction sur votre téléphone...")
    
    # Simuler une attente pour la confirmation
    print("\nAttente de la confirmation de la transaction (simulation)...")
    time.sleep(5)  # Attendre 5 secondes pour la simulation
    
    # Vérifier à nouveau le statut
    print("\nVérification du statut après confirmation...")
    status_info = client.get_transaction_status(
        server_correlation_id=server_correlation_id,
        correlation_id=correlation_id
    )
    
    status = status_info['response']['status']
    print(f"Statut actuel: {status}")
    
    # Si la transaction est complétée, récupérer les détails
    if status == 'completed' and 'objectReference' in status_info['response']:
        transaction_id = status_info['response']['objectReference']
        
        print("\nRécupération des détails de la transaction...")
        details = client.get_transaction_details(
            transaction_id=transaction_id,
            correlation_id=correlation_id
        )
        
        print(f"Détails de la transaction:")
        print(f"- Montant: {details['response'].get('amount')} {details['response'].get('currency')}")
        print(f"- Statut: {details['response'].get('transactionStatus')}")
        print(f"- Date: {details['response'].get('createDate')}")
    
except MVolaTransactionError as e:
    print(f"Erreur de transaction: {e}")
    if hasattr(e, 'field'):
        print(f"Champ en erreur: {e.field}")
    
except MVolaError as e:
    print(f"Erreur MVola: {e}")
    if hasattr(e, 'status_code'):
        print(f"Code HTTP: {e.status_code}")
    
except Exception as e:
    print(f"Erreur inattendue: {e}")
```

## Gestion avec environnement virtuel

Pour une utilisation dans un projet, il est recommandé de configurer un environnement virtuel :

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows
venv\Scripts\activate
# Sur macOS/Linux
source venv/bin/activate

# Installer la bibliothèque
 pip install mvola-api-lib
```

## Voir aussi

- [Guide d'authentification](../guides/authentication.md) - Guide complet sur l'authentification
- [Guide des transactions](../guides/transactions.md) - Guide complet sur les transactions
- [Gestion des erreurs](../guides/error-handling.md) - Comment gérer les erreurs efficacement
- [Intégration web](web-integration.md) - Exemples d'intégration avec des frameworks web 