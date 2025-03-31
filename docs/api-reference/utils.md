# Référence des utilitaires

Le module `mvola_api.utils` fournit un ensemble de fonctions utilitaires et d'outils pour faciliter l'utilisation de la bibliothèque MVola API. Ces utilitaires vous aident à formater les données, valider les paramètres, gérer les numéros de téléphone et plus encore.

## Fonctions utilitaires

Ce module contient plusieurs fonctions utilitaires qui vous aident à travailler avec l'API MVola.

## Validation des numéros de téléphone

```python
from mvola_api.utils import validate_msisdn, format_msisdn

# Validation d'un numéro de téléphone
try:
    # Vérifie si le format du numéro est valide
    validate_msisdn("0343500003")  # Valide
    validate_msisdn("0343500004")  # Valide
    validate_msisdn("0340000")     # Lève MVolaValidationError (trop court)
    validate_msisdn("abcdefghij")  # Lève MVolaValidationError (format invalide)
except Exception as e:
    print(f"Numéro invalide: {e}")

# Formatage du numéro de téléphone au format international (si nécessaire pour l'API)
international_number = format_msisdn("0343500003")
print(international_number)  # Affiche: 261343500003 (pour l'API)

# La fonction détecte automatiquement le format
same_number = format_msisdn("0343500003")
print(same_number)  # Formate correctement le numéro
```

## Génération d'identifiants

```python
from mvola_api.utils import generate_uuid, generate_reference

# Génération d'un UUID unique
correlation_id = generate_uuid()
print(correlation_id)  # Ex: 550e8400-e29b-41d4-a716-446655440000

# Génération d'une référence unique pour les transactions
reference = generate_reference(prefix="PAY")
print(reference)  # Ex: PAY-12AB34CD
```

## Formatage de données

```python
from mvola_api.utils import format_amount, format_date

# Formatage du montant
formatted_amount = format_amount(1234.56)
print(formatted_amount)  # "1234.56" (chaîne de caractères)

# Formatage de la date au format ISO 8601
iso_date = format_date()  # Utilise la date et heure actuelles
print(iso_date)  # Ex: 2024-07-24T10:15:30.000Z

# Formatage avec une date spécifique
from datetime import datetime
specific_date = datetime(2024, 1, 1, 12, 0, 0)
formatted_date = format_date(specific_date)
print(formatted_date)  # "2024-01-01T12:00:00.000Z"
```

## Validation des paramètres

```python
from mvola_api.utils import validate_required_params

# Validation des paramètres requis
data = {
    "param1": "value1",
    "param2": None,
    "param3": "value3"
}

required_params = ["param1", "param2", "param4"]

try:
    # Vérifie si tous les paramètres requis sont présents et non None
    validate_required_params(data, required_params)
except Exception as e:
    print(f"Paramètres manquants: {e}")
    # Affiche: "Paramètres manquants: Les paramètres suivants sont requis: param2, param4"
```

## Configuration du logging

```python
from mvola_api.utils import setup_logger
import logging

# Configuration du logger par défaut
logger = setup_logger()
logger.info("Message d'information")
logger.error("Message d'erreur")

# Configuration personnalisée
custom_logger = setup_logger(
    name="custom_logger",
    level=logging.DEBUG,
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file="mvola.log"  # Optionnel
)

custom_logger.debug("Message de débogage")
```

## Gestion des requêtes HTTP

```python
from mvola_api.utils import make_api_request
import requests

# Effectuer une requête API avec gestion d'erreurs
try:
    response = make_api_request(
        method="GET",
        url="https://api.example.com/resource",
        headers={"Authorization": "Bearer token"},
        params={"param1": "value1"},
        timeout=10,
        verify_ssl=True
    )
    
    print(f"Réponse: {response.json()}")
    
except Exception as e:
    print(f"Erreur lors de la requête: {e}")
```

## Outils de débogage

```python
from mvola_api.utils import debug_request, debug_response

# Afficher les détails d'une requête HTTP pour le débogage
debug_request(
    method="POST",
    url="https://api.example.com/resource",
    headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
    data={"key": "value"}
)

# Afficher les détails d'une réponse HTTP pour le débogage
response = requests.get("https://api.example.com/resource")
debug_response(response)
```

## Utilitaires de sécurité

```python
from mvola_api.utils import encode_credentials, mask_sensitive_data

# Encodage des identifiants en Base64 pour l'authentification
encoded = encode_credentials("consumer_key", "consumer_secret")
print(encoded)  # Chaîne encodée en Base64

# Masquage des données sensibles pour la journalisation
data = {
    "consumer_key": "my_consumer_key",
    "consumer_secret": "my_consumer_secret",
    "msisdn": "0343500003",
    "amount": 1000
}

masked_data = mask_sensitive_data(data)
print(masked_data)
# Affiche: {'consumer_key': '***', 'consumer_secret': '***', 'msisdn': '0343******', 'amount': 1000}
```

## Utilitaires de conversion

```python
from mvola_api.utils import to_boolean, to_int, to_float, to_str

# Conversion en booléen
print(to_boolean("true"))   # True
print(to_boolean("yes"))    # True
print(to_boolean("1"))      # True
print(to_boolean("false"))  # False
print(to_boolean("no"))     # False
print(to_boolean("0"))      # False

# Conversion en entier avec valeur par défaut
print(to_int("123"))        # 123
print(to_int("abc", 0))     # 0 (valeur par défaut)

# Conversion en flottant avec valeur par défaut
print(to_float("123.45"))   # 123.45
print(to_float("abc", 0.0)) # 0.0 (valeur par défaut)

# Conversion en chaîne avec formatage
print(to_str(123))          # "123"
print(to_str(None, "N/A"))  # "N/A" (valeur par défaut)
```

## Bonnes pratiques

1. **Validez les numéros de téléphone** : Utilisez `validate_msisdn` et `format_msisdn` pour vous assurer que les numéros sont au format correct avant d'effectuer des transactions.

2. **Générez des références uniques** : Utilisez `generate_reference` pour créer des références de transaction uniques et traçables.

3. **Utilisez le logging** : Configurez un logger avec `setup_logger` pour faciliter le débogage et le suivi des opérations.

4. **Masquez les données sensibles** : Utilisez `mask_sensitive_data` avant de journaliser des informations qui pourraient contenir des données confidentielles.

5. **Utilisez la validation de paramètres** : Assurez-vous que tous les paramètres requis sont présents avec `validate_required_params` avant d'effectuer des opérations.

## Voir aussi

- [Guide des transactions](../guides/transactions.md) - Voir comment ces utilitaires sont utilisés dans les transactions
- [Référence du client](client.md) - Documentation de la classe principale qui utilise ces utilitaires
- [Gestion des erreurs](../guides/error-handling.md) - Comment les utilitaires contribuent à la gestion des erreurs 