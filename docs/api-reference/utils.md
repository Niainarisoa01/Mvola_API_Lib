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

# Formatage du numéro de téléphone au format requis par l'API
formatted_number = format_msisdn("0343500003")
print(formatted_number)  # Affiche: 0343500003
```

## Validation du texte de description

```python
from mvola_api.utils import validate_description

# Validation de la description des transactions
try:
    # Vérification du texte de description (max 50 caractères et caractères spéciaux limités)
    validate_description("Paiement pour produit ABC")  # Valide
    validate_description("Paiement avec tiret-underscore_point.")  # Valide
    validate_description("Texte avec virgule, et espace")  # Valide
    
    # Invalides :
    validate_description("Texte avec caractère spécial interdit ! @ # $ % ^ & * ( )")  # Lève MVolaValidationError
    validate_description("Texte beaucoup trop long qui dépasse largement la limite de 50 caractères imposée par l'API MVola")  # Lève MVolaValidationError
except Exception as e:
    print(f"Description invalide: {e}")
```

## Génération d'identifiants

```python
from mvola_api.utils import generate_correlation_id, generate_reference

# Génération d'un ID de corrélation unique (UUID v4)
correlation_id = generate_correlation_id()
print(correlation_id)  # Ex: 550e8400-e29b-41d4-a716-446655440000

# Génération d'une référence unique pour les transactions
reference = generate_reference(prefix="PAY")
print(reference)  # Ex: PAY-12AB34CD
```

## Formatage de données

```python
from mvola_api.utils import format_date

# Formatage de la date au format ISO 8601 requis par l'API
iso_date = format_date()  # Utilise la date et heure actuelles
print(iso_date)  # Ex: 2023-07-24T10:15:30.000Z

# Formatage avec une date spécifique
from datetime import datetime
specific_date = datetime(2023, 1, 1, 12, 0, 0)
formatted_date = format_date(specific_date)
print(formatted_date)  # "2023-01-01T12:00:00.000Z"
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

## Construction des en-têtes pour les requêtes API

```python
from mvola_api.utils import build_headers

# Construction des en-têtes pour les requêtes API
headers = build_headers(
    access_token="votre_token_d_acces",
    correlation_id="550e8400-e29b-41d4-a716-446655440000",
    user_language="FR",
    partner_name="NomPartenaire",
    partner_msisdn="0343500003"
)

print(headers)
# Affiche:
# {
#     "Authorization": "Bearer votre_token_d_acces",
#     "Version": "1.0",
#     "X-CorrelationID": "550e8400-e29b-41d4-a716-446655440000",
#     "UserLanguage": "FR",
#     "UserAccountIdentifier": "msisdn;0343500003",
#     "partnerName": "NomPartenaire",
#     "Content-Type": "application/json",
#     "Cache-Control": "no-cache"
# }
```

## Préparation des données pour les requêtes API

```python
from mvola_api.utils import prepare_transaction_request

# Préparation des données pour une requête de transaction
transaction_data = prepare_transaction_request(
    amount="1000",
    currency="Ar",
    description="Paiement produit",
    debit_msisdn="0343500003",
    credit_msisdn="0343500004",
    partner_name="NomPartenaire",
    requesting_organisation_transaction_reference="REF123456",
    original_transaction_reference="",
    foreign_currency="USD",
    foreign_amount="2.5"
)

print(transaction_data)
# Affiche:
# {
#     "amount": "1000",
#     "currency": "Ar",
#     "descriptionText": "Paiement produit",
#     "requestDate": "2023-07-24T10:15:30.000Z",
#     "requestingOrganisationTransactionReference": "REF123456",
#     "originalTransactionReference": "",
#     "debitParty": [{"key": "msisdn", "value": "0343500003"}],
#     "creditParty": [{"key": "msisdn", "value": "0343500004"}],
#     "metadata": [
#         {"key": "partnerName", "value": "NomPartenaire"},
#         {"key": "fc", "value": "USD"},
#         {"key": "amountFc", "value": "2.5"}
#     ]
# }
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
        method="POST",
        url="https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/",
        headers={
            "Authorization": "Bearer token",
            "Version": "1.0",
            "X-CorrelationID": "550e8400-e29b-41d4-a716-446655440000",
            "Content-Type": "application/json"
        },
        json={
            "amount": "1000",
            "currency": "Ar",
            "descriptionText": "Paiement produit"
            # Autres champs...
        },
        timeout=30
    )
    
    # Traiter la réponse
    print(f"Statut: {response.status_code}")
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
    url="https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/",
    headers={
        "Authorization": "Bearer token", 
        "Content-Type": "application/json"
    },
    data={
        "amount": "1000",
        "currency": "Ar"
    }
)

# Afficher les détails d'une réponse HTTP pour le débogage
response = requests.post(
    "https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/",
    headers={"Authorization": "Bearer token"},
    json={"amount": "1000"}
)
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
    "debitParty": [{"key": "msisdn", "value": "0343500003"}],
    "amount": "1000"
}

masked_data = mask_sensitive_data(data)
print(masked_data)
# Affiche: {'consumer_key': '***', 'consumer_secret': '***', 'debitParty': [{'key': 'msisdn', 'value': '0343******'}], 'amount': '1000'}
```

## Analyse des réponses

```python
from mvola_api.utils import extract_transaction_info, parse_api_response

# Extraire les informations d'une transaction à partir d'une réponse
response_data = {
    "amount": "1000",
    "currency": "Ar",
    "transactionReference": "transactionID123",
    "transactionStatus": "completed"
}

transaction_info = extract_transaction_info(response_data)
print(f"Montant: {transaction_info['amount']}")
print(f"Statut: {transaction_info['status']}")

# Analyser une réponse d'API complète
response = requests.post(
    "https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/",
    headers={"Authorization": "Bearer token"},
    json={"amount": "1000"}
)

parsed_response = parse_api_response(response)
print(f"Statut HTTP: {parsed_response['status_code']}")
print(f"Corps de la réponse: {parsed_response['response']}")
print(f"En-têtes: {parsed_response['headers']}")
```

## Bonnes pratiques

1. **Validez les numéros de téléphone** : Utilisez `validate_msisdn` pour vous assurer que les numéros sont au format correct avant d'effectuer des transactions.

2. **Validez les descriptions** : Utilisez `validate_description` pour vous assurer que les descriptions respectent les contraintes de l'API MVola (50 caractères max, caractères spéciaux limités).

3. **Générez des références uniques** : Utilisez `generate_reference` pour créer des références de transaction uniques et traçables.

4. **Utilisez le logging** : Configurez un logger avec `setup_logger` pour faciliter le débogage et le suivi des opérations.

5. **Masquez les données sensibles** : Utilisez `mask_sensitive_data` avant de journaliser des informations qui pourraient contenir des données confidentielles.

6. **Gestion des erreurs HTTP** : Utilisez `make_api_request` qui gère les erreurs HTTP communes et transforme les réponses d'erreur en exceptions Python compréhensibles.

## Voir aussi

- [Guide des transactions](../guides/transactions.md) - Voir comment ces utilitaires sont utilisés dans les transactions
- [Référence du client](client.md) - Documentation de la classe principale qui utilise ces utilitaires
- [Gestion des erreurs](../guides/error-handling.md) - Comment les utilitaires contribuent à la gestion des erreurs 