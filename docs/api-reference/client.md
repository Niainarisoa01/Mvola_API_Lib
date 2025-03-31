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
    sandbox=True  # Pour l'environnement de test
)

# Initialisation pour l'environnement de production
prod_client = MVolaClient(
    consumer_key="votre_consumer_key_prod",
    consumer_secret="votre_consumer_secret_prod",
    partner_name="Nom de votre application",
    partner_msisdn="0343500003",  # Votre numéro MVola
    sandbox=False  # Pour l'environnement de production
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
    sandbox=True,
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

# Vérifier si un token est expiré
is_expired = client.is_token_expired()
print(f"Token expiré: {is_expired}")

# Rafraîchir manuellement le token
client.refresh_token()
```

### Opérations de transaction

```python
# Initier un paiement
transaction_info = client.initiate_payment(
    amount=1000,
    debit_msisdn="0343500003",  # Numéro qui paie
    credit_msisdn="0343500004",  # Numéro qui reçoit
    reference="REF123456",       # Référence unique
    description="Paiement pour produit ABC",
    callback_url="https://example.com/callback"  # Optionnel
)

# Récupérer l'ID de transaction
transaction_id = transaction_info.get('server_correlation_id')

# Vérifier le statut d'une transaction
status = client.get_transaction_status(
    transaction_id=transaction_id,
    msisdn="0343500003"
)
print(f"Statut: {status.get('status')}")

# Récupérer les détails d'une transaction
details = client.get_transaction_details(transaction_id=transaction_id)
print(f"Détails: {details}")
```

## Notes importantes

1. **Gestion des tokens** : Le client gère automatiquement les tokens d'authentification, en les générant et les rafraîchissant au besoin. Vous n'avez normalement pas besoin d'appeler explicitement `generate_token()` ou `refresh_token()`.

2. **Environnements** : Utilisez toujours l'environnement sandbox (`sandbox=True`) pour les tests avant de passer à la production.

3. **Numéros de téléphone** : Les numéros de téléphone doivent être au format national (ex: 034XXXXXXX, 038XXXXXXX)

4. **Références de transaction** : Générez toujours des références uniques pour chaque transaction.

5. **Gestion des erreurs** : Utilisez la gestion d'exceptions appropriée pour capturer et traiter les différentes erreurs qui peuvent survenir.

## Voir aussi

- [Guide d'authentification](../guides/authentication.md) - Guide complet sur l'authentification
- [Guide des transactions](../guides/transactions.md) - Guide complet sur les transactions
- [Référence d'authentification](auth.md) - Documentation détaillée du module d'authentification
- [Référence de transaction](transaction.md) - Documentation détaillée du module de transaction 