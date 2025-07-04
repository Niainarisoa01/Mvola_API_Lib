# Client MVola API

Le `MVolaClient` est la classe principale qui vous permet d'interagir avec l'API MVola. Il encapsule les fonctionnalités des modules d'authentification et de transaction, offrant une interface unifiée et simple pour effectuer des opérations avec l'API MVola.

## Classe MVolaClient

La classe `MVolaClient` est le point d'entrée principal pour l'utilisation de la bibliothèque MVola API.

### Méthode 1 : Initialisation directe

```python
from mvola_api import MVolaClient

# Initialisation pour l'environnement sandbox (développement)
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="Nom de votre application",
    partner_msisdn="0343500004",  # Utiliser 0343500004 pour sandbox
    sandbox=True  # True pour sandbox, False pour production
)

# Initialisation pour l'environnement de production
prod_client = MVolaClient(
    consumer_key="votre_consumer_key_prod",
    consumer_secret="votre_consumer_secret_prod",
    partner_name="Nom de votre application",
    partner_msisdn="votre_numero_mvola",  # Votre vrai numéro MVola
    sandbox=False  # Utiliser l'environnement de production
)
```

### Méthode 2 : Utilisation des variables d'environnement (Recommandée)

```python
from mvola_api import MVolaClient
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Créer un client à partir des variables d'environnement
client = MVolaClient.from_env()

# Créer un client en surchargeant certaines variables d'environnement
custom_client = MVolaClient(
    # Ces valeurs seront chargées depuis les variables d'environnement
    consumer_key=None,  # None indique d'utiliser la variable d'environnement
    consumer_secret=None,
    # Ces valeurs surchargeront les variables d'environnement
    partner_name="Nom personnalisé",
    sandbox=False  # Forcer l'utilisation de la production
)
```

Votre fichier `.env` doit contenir :

```
MVOLA_CONSUMER_KEY=votre_consumer_key
MVOLA_CONSUMER_SECRET=votre_consumer_secret
MVOLA_PARTNER_NAME=Nom de votre application
MVOLA_PARTNER_MSISDN=0343500004
MVOLA_SANDBOX=True
```

### Paramètres d'initialisation

| Paramètre        | Type    | Description                                      | Défaut                 |
|------------------|---------|--------------------------------------------------|------------------------|
| consumer_key     | str     | Consumer Key obtenue du portail développeur      | MVOLA_CONSUMER_KEY     |
| consumer_secret  | str     | Consumer Secret obtenue du portail développeur   | MVOLA_CONSUMER_SECRET  |
| partner_name     | str     | Nom de votre entreprise/application              | MVOLA_PARTNER_NAME     |
| partner_msisdn   | str     | Votre numéro MVola                               | MVOLA_PARTNER_MSISDN   |
| sandbox          | bool    | True pour utiliser l'environnement sandbox       | MVOLA_SANDBOX ou True  |
| language         | str     | Langue par défaut ("MG" ou "FR")                 | "MG"                   |
| logger           | Logger  | Logger personnalisé                              | None                   |

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
    partner_msisdn="0343500004",
    sandbox=True,
    logger=logger  # Fournir votre logger personnalisé
)
```

## Méthodes principales

### Méthodes de classe

```python
# Créer un client à partir des variables d'environnement
client = MVolaClient.from_env()
```

### Gestion des tokens

```python
# Générer un token d'authentification
token = client.generate_token()
print(f"Token: {token['access_token'][:10]}...")  # Ne jamais afficher le token complet
print(f"Expire dans: {token['expires_in']} secondes")

# Forcer le rafraîchissement d'un token
token = client.generate_token(force_refresh=True)
```

### Opérations de transaction

```python
# Initier un paiement
transaction_info = client.initiate_payment(
    amount="1000",                # Montant en ariary (chaîne)
    debit_msisdn="0343500003",    # Numéro qui paie
    credit_msisdn="0343500004",   # Numéro qui reçoit
    description="Paiement pour produit ABC",  # Description
    currency="Ar",                # Devise (Ar par défaut)
    callback_url="https://example.com/callback"  # URL de notification (recommandé)
)

# Récupérer l'ID de corrélation pour le suivi
server_correlation_id = transaction_info['response']['serverCorrelationId']
print(f"ID de corrélation: {server_correlation_id}")

# Vérifier le statut d'une transaction
status = client.get_transaction_status(server_correlation_id)
print(f"Statut: {status['response']['status']}")  # pending, completed, ou failed

# Si la transaction est complétée, récupérer son ID
if status['response']['status'] == 'completed' and 'objectReference' in status['response']:
    transaction_id = status['response']['objectReference']
    
    # Récupérer les détails d'une transaction
    details = client.get_transaction_details(transaction_id)
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
        'notificationMethod': 'callback'  # ou "polling" si pas d'URL callback
    },
    'status_code': 202,  # Le code 202 indique que la requête est acceptée pour traitement
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
from mvola_api import MVolaClient
from mvola_api.exceptions import MVolaError, MVolaAuthError

try:
    # Créer un client et effectuer une opération
    client = MVolaClient.from_env()
    result = client.initiate_payment(
        amount="1000",
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Test payment"
    )
except MVolaAuthError as e:
    print(f"Erreur d'authentification: {e}")
    # Vérifiez vos credentials
except MVolaError as e:
    print(f"Erreur MVola: {e}")
    print(f"Code HTTP: {getattr(e, 'status_code', 'N/A')}")
    print(f"Détails: {getattr(e, 'details', 'N/A')}")
```

## Notes importantes

1. **Variables d'environnement** : La méthode recommandée est d'utiliser `MVolaClient.from_env()` pour charger vos identifiants depuis un fichier `.env`.

2. **Gestion des tokens** : Le client gère automatiquement les tokens d'authentification, en les générant et les rafraîchissant au besoin.

3. **Environnements** : L'environnement sandbox doit être utilisé pour les tests avant de passer à la production.

4. **Numéros de téléphone** : Pour l'environnement sandbox, utilisez uniquement `0343500003` et `0343500004`.

5. **En-têtes HTTP** : La bibliothèque utilise désormais des en-têtes optimisés pour la compatibilité avec l'API MVola, comme :
   - `version` en minuscule (au lieu de `Version`)
   - `Accept-Charset: utf-8`
   - `UserLanguage: MG` par défaut (au lieu de `FR`)

6. **Callbacks** : L'utilisation de l'en-tête `X-Callback-URL` est fortement recommandée pour recevoir des notifications automatiques.

7. **Métadonnées** : Les champs `fc` et `amountFc` sont automatiquement ajoutés aux métadonnées pour la compatibilité.

## Voir aussi

- [Guide d'authentification](../guides/authentication.md) - Guide complet sur l'authentification
- [Guide des transactions](../guides/transactions.md) - Guide complet sur les transactions
- [Référence d'authentification](auth.md) - Documentation détaillée du module d'authentification
- [Référence de transaction](transaction.md) - Documentation détaillée du module de transaction