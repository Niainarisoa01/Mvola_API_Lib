# Bibliothèque MVola API Python

Une bibliothèque Python robuste pour l'intégration avec l'API de paiement mobile MVola à Madagascar.

## Mise à jour importante

Cette bibliothèque a été mise à jour pour être conforme à la documentation 2023-2024 de l'API MVola.

## Changements principaux

1. **URL Sandbox** : L'URL sandbox a été mise à jour de `pre-api.mvola.mg` à `devapi.mvola.mg`

2. **Paramètres supplémentaires** : Les méthodes d'initiation de paiement ont été mises à jour pour inclure les paramètres suivants:
   - `requesting_organisation_transaction_reference` : ID de transaction côté client
   - `original_transaction_reference` : Numéro de référence lié à la transaction d'origine

3. **Limite de caractères pour la description** : La limite de caractères pour la description est maintenant de 50 (au lieu de 40)

## Installation

```bash
pip install mvola-api-lib
```

## Configuration

Pour utiliser la bibliothèque, vous aurez besoin de:

1. Un compte développeur MVola avec accès à l'API
2. Une clé API (Consumer Key et Consumer Secret) du portail développeur MVola
3. Un numéro de téléphone partenaire (MSISDN) enregistré auprès de MVola

## Utilisation

### Initialisation du client

```python
from mvola_api import MVolaClient

# Initialiser le client
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="nom_de_votre_application",
    partner_msisdn="votre_numero_partenaire",  # ex: 034xxxxxxx
    sandbox=True  # Utiliser l'environnement sandbox (True) ou production (False)
)
```

### Authentification

```python
# Générer un token d'authentification (valide pendant 1 heure)
token_data = client.generate_token()

# Le token est automatiquement utilisé pour les appels d'API suivants
# Mais vous pouvez forcer le rafraîchissement si nécessaire
token_data = client.generate_token(force_refresh=True)
```

### Initier un paiement

```python
try:
    # Générer une référence de transaction
    transaction_ref = "MVOLA-TEST-12345678"
    
    payment_result = client.initiate_payment(
        amount=1000,  # 1000 Ar
        debit_msisdn="034xxxxxxx",  # Numéro du débiteur (qui paie)
        credit_msisdn="034xxxxxxx",  # Numéro du créditeur (qui reçoit)
        description="Test de paiement MVola",
        currency="Ar",
        callback_url="https://votre-site.com/callback",  # URL où MVola enverra des notifications
        requesting_organisation_transaction_reference=transaction_ref,
        foreign_currency="USD",  # Optionnel - devise étrangère
        foreign_amount=0.25,     # Optionnel - montant en devise étrangère
        user_language="FR"       # FR ou MG
    )
    
    # Récupérer l'ID de corrélation du serveur pour vérifier le statut
    server_correlation_id = payment_result['response']['serverCorrelationId']
    print(f"Paiement initié, ID de corrélation: {server_correlation_id}")
    
except MVolaError as e:
    print(f"Erreur: {e}")
```

### Vérifier le statut d'une transaction

```python
try:
    status_result = client.get_transaction_status(server_correlation_id)
    status = status_result['response']['status']
    print(f"Statut de la transaction: {status}")
    
    # Les statuts possibles sont: pending, completed, failed
    if status == "completed":
        transaction_id = status_result['response'].get('objectReference')
        print(f"Transaction complétée, ID: {transaction_id}")
    
except MVolaError as e:
    print(f"Erreur: {e}")
```

### Obtenir les détails d'une transaction

```python
try:
    details_result = client.get_transaction_details(transaction_id)
    details = details_result['response']
    print(f"Montant: {details.get('amount')} {details.get('currency')}")
    print(f"Statut: {details.get('transactionStatus')}")
    
except MVolaError as e:
    print(f"Erreur: {e}")
```

## Environnement Sandbox

Pour les tests dans l'environnement sandbox, utilisez les numéros de téléphone suivants:
- 0343500003
- 0343500004

**Note importante**: Dans l'environnement sandbox, les transactions restent souvent en état "pending". Vous devrez peut-être approuver manuellement les transactions dans le portail développeur MVola.

## Gestion des erreurs

La bibliothèque fournit des exceptions personnalisées pour différents types d'erreurs:

```python
from mvola_api import MVolaClient, MVolaError, MVolaAuthError, MVolaTransactionError

try:
    result = client.initiate_payment(...)
except MVolaAuthError as e:
    print(f"Erreur d'authentification: {e}")
except MVolaTransactionError as e:
    print(f"Erreur de transaction: {e}")
except MVolaError as e:
    print(f"Erreur générale MVola: {e}")
```

## Référence de l'API MVola

### Endpoints

- **Authentification**: `POST /token`
- **Initier une transaction**: `POST /mvola/mm/transactions/type/merchantpay/1.0.0/`
- **Vérifier le statut**: `GET /mvola/mm/transactions/type/merchantpay/1.0.0/status/{serverCorrelationId}`
- **Détails de transaction**: `GET /mvola/mm/transactions/type/merchantpay/1.0.0/{transactionId}`

### Statuts de transaction

- `pending`: Transaction en attente
- `completed`: Transaction réussie
- `failed`: Transaction échouée

## Exemple complet

Voir le fichier `examples/mvola_api_example.py` pour un exemple complet d'utilisation de la bibliothèque.

## Ressources

- [Documentation officielle MVola API](https://docs.mvola.mg/) (si disponible)
- [Portail développeur MVola](https://developer.mvola.mg/) (si disponible)

## Licence

Cette bibliothèque est distribuée sous licence MIT. Voir le fichier LICENSE pour plus de détails. 