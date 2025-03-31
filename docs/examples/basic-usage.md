# Utilisation basique

Ce guide fournit des exemples simples d'utilisation de la bibliothèque MVola API.

## Installation

Commencez par installer la bibliothèque :

```bash
pip install mvola-api
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
    sandbox=True  # Pour l'environnement de test
)
```

## Génération d'un token

La bibliothèque gère automatiquement les tokens d'authentification, mais vous pouvez également générer ou rafraîchir un token manuellement :

```python
# Générer un token d'authentification
token = client.generate_token()
print(f"Token: {token['access_token']}")
print(f"Expire dans: {token['expires_in']} secondes")

# Vérifier si un token est expiré
is_expired = client.is_token_expired()
print(f"Token expiré: {is_expired}")

# Rafraîchir manuellement le token
client.refresh_token()
```

## Initier un paiement

Pour initier un paiement MVola :

```python
try:
    transaction_info = client.initiate_payment(
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

## Vérifier le statut d'une transaction

Pour vérifier le statut d'une transaction en cours :

```python
try:
    status_info = client.get_transaction_status(
        transaction_id="transaction-id-12345",  # ID obtenu lors de l'initiation
        msisdn="0343500003"                     # Numéro associé à la transaction
    )
    
    status = status_info.get('status')
    print(f"Statut de la transaction: {status}")
    
    # États possibles : pending, completed, failed, cancelled
    if status == 'completed':
        print("Transaction réussie!")
    elif status == 'pending':
        print("Transaction en attente de confirmation...")
    else:
        print(f"Transaction terminée avec statut: {status}")
        if 'reason' in status_info:
            print(f"Raison: {status_info['reason']}")
    
except Exception as e:
    print(f"Erreur lors de la vérification du statut: {e}")
```

## Récupérer les détails d'une transaction

Pour obtenir tous les détails d'une transaction terminée :

```python
try:
    transaction_details = client.get_transaction_details(
        transaction_id="transaction-id-12345"  # ID obtenu lors de l'initiation
    )
    
    print(f"Détails de la transaction: {transaction_details}")
    print(f"Montant: {transaction_details.get('amount')} {transaction_details.get('currency')}")
    print(f"ID financier: {transaction_details.get('financialTransactionId')}")
    print(f"Date de création: {transaction_details.get('creationDate')}")
    
    # Accéder aux informations du payeur
    debit_party = transaction_details.get('debitParty', [])
    for party in debit_party:
        if party.get('key') == 'msisdn':
            print(f"Payeur: {party.get('value')}")
    
    # Accéder aux informations du bénéficiaire
    credit_party = transaction_details.get('creditParty', [])
    for party in credit_party:
        if party.get('key') == 'msisdn':
            print(f"Bénéficiaire: {party.get('value')}")
    
except Exception as e:
    print(f"Erreur lors de la récupération des détails: {e}")
```

## Exemple complet

Voici un exemple complet qui combine plusieurs opérations :

```python
from mvola_api import MVolaClient
from mvola_api.exceptions import MVolaError, MVolaTransactionError
from mvola_api.utils import generate_reference

# Initialisation du client
try:
    client = MVolaClient(
        consumer_key="votre_consumer_key",
        consumer_secret="votre_consumer_secret",
        partner_name="Nom de votre application",
        partner_msisdn="0343500003",
        sandbox=True
    )
    
    # Générer une référence unique pour la transaction
    reference = generate_reference(prefix="PAY")
    
    # Initier un paiement
    transaction_info = client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        reference=reference,
        description="Paiement test"
    )
    
    transaction_id = transaction_info.get('server_correlation_id')
    print(f"Transaction initiée avec succès!")
    print(f"ID de transaction: {transaction_id}")
    print(f"Référence: {reference}")
    
    # Vérifier le statut initial
    status_info = client.get_transaction_status(
        transaction_id=transaction_id,
        msisdn="0343500003"
    )
    
    print(f"Statut initial: {status_info.get('status')}")
    print("Veuillez confirmer la transaction sur votre téléphone...")
    
    # Dans une application réelle, vous pourriez implémenter une boucle de polling
    # pour vérifier régulièrement le statut, ou utiliser des webhooks
    
except MVolaTransactionError as e:
    print(f"Erreur de transaction: {e}")
    if hasattr(e, 'field'):
        print(f"Champ en erreur: {e.field}")
    
except MVolaError as e:
    print(f"Erreur MVola: {e}")
    
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
pip install mvola-api
```

## Voir aussi

- [Guide d'authentification](../guides/authentication.md) - Guide complet sur l'authentification
- [Guide des transactions](../guides/transactions.md) - Guide complet sur les transactions
- [Gestion des erreurs](../guides/error-handling.md) - Comment gérer les erreurs efficacement
- [Intégration web](web-integration.md) - Exemples d'intégration avec des frameworks web 