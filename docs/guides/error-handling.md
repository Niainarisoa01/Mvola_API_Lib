# Guide de gestion des erreurs

Ce guide explique comment gérer efficacement les erreurs qui peuvent survenir lors de l'utilisation de la bibliothèque MVola API.

## Introduction

La bibliothèque MVola API utilise un système d'exceptions hiérarchique pour vous permettre de gérer facilement les différents types d'erreurs qui peuvent se produire lors des opérations avec l'API MVola.

## Hiérarchie des exceptions

```
MVolaError (Exception de base)
├── MVolaAuthError (Erreurs d'authentification)
│   ├── MVolaInvalidCredentialsError
│   └── MVolaTokenExpiredError
├── MVolaTransactionError (Erreurs de transaction)
│   ├── MVolaTransactionValidationError
│   ├── MVolaTransactionStatusError
│   └── MVolaTransactionCreationError
├── MVolaValidationError (Erreurs de validation)
│   └── MVolaInvalidParameterError
├── MVolaConnectionError (Erreurs de connexion)
│   ├── MVolaRequestTimeoutError
│   └── MVolaServerError
└── MVolaConfigError (Erreurs de configuration)
```

Cette hiérarchie vous permet de capturer des erreurs à différents niveaux de spécificité selon vos besoins.

## Importation des exceptions

```python
from mvola_api.exceptions import (
    MVolaError,                    # Exception de base
    MVolaAuthError,                # Erreurs d'authentification
    MVolaInvalidCredentialsError,  # Identifiants invalides
    MVolaTokenExpiredError,        # Token expiré
    MVolaTransactionError,         # Erreurs de transaction
    MVolaTransactionValidationError, # Validation de transaction
    MVolaTransactionStatusError,   # Erreur de statut
    MVolaTransactionCreationError, # Création de transaction
    MVolaValidationError,          # Erreurs de validation
    MVolaInvalidParameterError,    # Paramètre invalide
    MVolaConnectionError,          # Erreurs de connexion
    MVolaRequestTimeoutError,      # Timeout
    MVolaServerError,              # Erreur serveur
    MVolaConfigError               # Erreurs de configuration
)
```

## Gestion basique des erreurs

La façon la plus simple de gérer les erreurs est d'utiliser un bloc try/except pour capturer toutes les erreurs MVola :

```python
from mvola_api import MVolaClient
from mvola_api.exceptions import MVolaError

try:
    # Initialiser le client
    client = MVolaClient(
        consumer_key="votre_consumer_key",
        consumer_secret="votre_consumer_secret",
        partner_name="Nom de votre application",
        partner_msisdn="0343500003",
        sandbox=True
    )
    
    # Initier un paiement
    transaction_info = client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        reference="REF123456",
        description="Paiement test"
    )
    
    print(f"Transaction initiée avec succès: {transaction_info}")
    
except MVolaError as e:
    print(f"Une erreur MVola s'est produite: {e}")
    # Gérer l'erreur (journalisation, notification, etc.)
```

## Gestion avancée des erreurs

Pour une gestion plus précise, vous pouvez capturer des types d'exceptions spécifiques :

```python
from mvola_api import MVolaClient
from mvola_api.exceptions import (
    MVolaInvalidCredentialsError,
    MVolaTransactionValidationError,
    MVolaConnectionError,
    MVolaError
)

try:
    # Initialiser le client
    client = MVolaClient(
        consumer_key="votre_consumer_key",
        consumer_secret="votre_consumer_secret",
        partner_name="Nom de votre application",
        partner_msisdn="0343500003",
        sandbox=True
    )
    
    # Initier un paiement
    transaction_info = client.initiate_payment(
        amount=1000,
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        reference="REF123456",
        description="Paiement test"
    )
    
    print(f"Transaction initiée avec succès: {transaction_info}")
    
except MVolaInvalidCredentialsError as e:
    print(f"Identifiants invalides: {e}")
    # Suggérer de vérifier les identifiants API
    
except MVolaTransactionValidationError as e:
    print(f"Données de transaction invalides: {e}")
    # Afficher des messages d'erreur spécifiques aux champs
    
except MVolaConnectionError as e:
    print(f"Erreur de connexion: {e}")
    # Suggérer de vérifier la connexion Internet ou de réessayer plus tard
    
except MVolaError as e:
    print(f"Autre erreur MVola: {e}")
    # Gérer les autres erreurs MVola
    
except Exception as e:
    print(f"Erreur inattendue: {e}")
    # Capturer toute autre erreur non prévue
```

## Types d'erreurs spécifiques

### Erreurs d'authentification

```python
try:
    # Tenter de générer un token avec des identifiants invalides
    client.generate_token()
except MVolaInvalidCredentialsError as e:
    print(f"Identifiants invalides: {e}")
    print(f"Code d'erreur: {e.error_code}")
    # Suggérer de vérifier les identifiants ou de générer de nouvelles clés
except MVolaTokenExpiredError as e:
    print(f"Token expiré: {e}")
    # Rafraîchir le token et réessayer
    client.refresh_token()
```

### Erreurs de transaction

```python
try:
    # Tenter un paiement avec des données invalides
    client.initiate_payment(
        amount=-100,  # Montant négatif (invalide)
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        reference="REF123456",
        description="Paiement test"
    )
except MVolaTransactionValidationError as e:
    print(f"Validation échouée: {e}")
    print(f"Champ en erreur: {e.field}")
    print(f"Détails: {e.details}")
    # Afficher un message d'erreur approprié à l'utilisateur
    
except MVolaTransactionStatusError as e:
    print(f"Erreur de statut: {e}")
    print(f"ID de transaction: {e.transaction_id}")
    # Suggérer de vérifier l'ID de transaction
    
except MVolaTransactionCreationError as e:
    print(f"Erreur lors de la création: {e}")
    print(f"Détails: {e.details}")
    # Suggérer de réessayer plus tard
```

### Erreurs de validation

```python
from mvola_api.utils import validate_msisdn

try:
    # Valider un numéro de téléphone
    validate_msisdn("abcdef")  # Format invalide
except MVolaValidationError as e:
    print(f"Erreur de validation: {e}")
    # Afficher un message d'erreur approprié
```

### Erreurs de connexion

```python
try:
    # Tenter une opération qui peut échouer en raison de problèmes réseau
    status = client.get_transaction_status(
        transaction_id="transaction-id-12345",
        msisdn="0343500003"
    )
except MVolaRequestTimeoutError as e:
    print(f"Délai d'attente dépassé: {e}")
    print(f"URL: {e.url}")
    print(f"Timeout: {e.timeout} secondes")
    # Suggérer de réessayer plus tard
    
except MVolaServerError as e:
    print(f"Erreur serveur MVola: {e}")
    print(f"Code HTTP: {e.status_code}")
    print(f"Réponse: {e.response}")
    # Suggérer de contacter le support MVola si le problème persiste
```

## Techniques de gestion des erreurs

### Approche hiérarchique

Attrapez d'abord les exceptions les plus spécifiques, puis les plus générales :

```python
try:
    # Code utilisant MVola API
except MVolaInvalidCredentialsError as e:
    # Gérer les erreurs d'identifiants spécifiquement
    print(f"Identifiants invalides: {e}")
except MVolaAuthError as e:
    # Gérer les autres erreurs d'authentification
    print(f"Erreur d'authentification: {e}")
except MVolaTransactionError as e:
    # Gérer les erreurs de transaction
    print(f"Erreur de transaction: {e}")
except MVolaError as e:
    # Gérer toutes les autres erreurs MVola
    print(f"Erreur MVola: {e}")
except Exception as e:
    # Attraper toutes les autres exceptions Python
    print(f"Erreur inattendue: {e}")
```

### Gestion avec retries

Pour certaines erreurs temporaires (timeout, erreurs serveur), vous pouvez implémenter une stratégie de retry :

```python
from mvola_api.exceptions import MVolaRequestTimeoutError, MVolaServerError
import time

max_retries = 3
retry_count = 0
backoff_factor = 2  # Pour le backoff exponentiel

while retry_count < max_retries:
    try:
        # Tenter une opération MVola
        result = client.initiate_payment(
            amount=1000,
            debit_msisdn="0343500003",
            credit_msisdn="0343500004",
            reference="REF123456",
            description="Paiement test"
        )
        # Succès, sortir de la boucle
        break
        
    except (MVolaRequestTimeoutError, MVolaServerError) as e:
        # Incrémenter le compteur de tentatives
        retry_count += 1
        
        # Si nous avons atteint le maximum de tentatives, lever l'exception
        if retry_count >= max_retries:
            print(f"Échec après {max_retries} tentatives: {e}")
            raise
        
        # Calculer le temps d'attente avec backoff exponentiel
        wait_time = backoff_factor ** retry_count
        print(f"Erreur temporaire: {e}. Nouvelle tentative dans {wait_time}s...")
        
        # Attendre avant de réessayer
        time.sleep(wait_time)
```

## Validation préventive

Pour éviter certaines exceptions, validez vos données avant d'appeler l'API :

```python
from mvola_api.utils import validate_msisdn, validate_required_params

# Données à valider
payment_data = {
    "amount": 1000,
    "debit_msisdn": "0343500003",
    "credit_msisdn": "0343500004",
    "reference": "REF123456",
    "description": "Paiement test"
}

# Paramètres requis
required_params = ["amount", "debit_msisdn", "credit_msisdn", "reference", "description"]

try:
    # Valider que tous les paramètres requis sont présents
    validate_required_params(payment_data, required_params)
    
    # Valider les numéros de téléphone
    validate_msisdn(payment_data["debit_msisdn"])
    validate_msisdn(payment_data["credit_msisdn"])
    
    # Valider le montant
    if payment_data["amount"] <= 0:
        raise MVolaValidationError("Le montant doit être positif")
    
    # Si toutes les validations passent, initier le paiement
    transaction_info = client.initiate_payment(**payment_data)
    
except MVolaValidationError as e:
    # Gérer les erreurs de validation
    print(f"Erreur de validation: {e}")
```

## Journalisation des erreurs

Il est recommandé de journaliser les erreurs pour faciliter le débogage :

```python
import logging

# Configurer le logger
logger = logging.getLogger("mvola")
logger.setLevel(logging.DEBUG)

# Ajouter un handler pour écrire dans un fichier
file_handler = logging.FileHandler("mvola_errors.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

try:
    # Code utilisant MVola API
    result = client.initiate_payment(...)
except MVolaError as e:
    # Journaliser l'erreur avec les détails appropriés
    logger.error(f"Erreur MVola: {e}", exc_info=True)
    logger.error(f"Détails: {e.details if hasattr(e, 'details') else 'Pas de détails'}")
    
    # Vous pouvez également inclure des informations contextuelles
    logger.error(f"Contexte: initiation de paiement pour la référence {reference}")
    
    # Répondre à l'utilisateur avec un message approprié
    print("Une erreur s'est produite lors du traitement de votre paiement. Veuillez réessayer plus tard.")
```

## Messages d'erreur conviviaux

Transformez les erreurs techniques en messages compréhensibles pour l'utilisateur final :

```python
def get_user_friendly_message(exception):
    """Convertit une exception MVola en message utilisateur convivial"""
    
    if isinstance(exception, MVolaInvalidCredentialsError):
        return "Impossible de se connecter au service MVola. Veuillez contacter le support."
    
    elif isinstance(exception, MVolaTokenExpiredError):
        return "Votre session a expiré. Veuillez rafraîchir la page et réessayer."
    
    elif isinstance(exception, MVolaTransactionValidationError):
        if getattr(exception, 'field', '') == 'amount':
            return "Le montant spécifié n'est pas valide. Veuillez vérifier et réessayer."
        elif getattr(exception, 'field', '') in ['debit_msisdn', 'credit_msisdn']:
            return "Le numéro de téléphone fourni n'est pas valide. Veuillez vérifier et réessayer."
        else:
            return "Certaines informations de paiement ne sont pas valides. Veuillez vérifier et réessayer."
    
    elif isinstance(exception, MVolaTransactionStatusError):
        return "Impossible de vérifier le statut de la transaction. Veuillez réessayer plus tard."
    
    elif isinstance(exception, MVolaConnectionError):
        return "Problème de connexion au service MVola. Veuillez vérifier votre connexion Internet et réessayer."
    
    elif isinstance(exception, MVolaError):
        return "Une erreur s'est produite lors du traitement de votre paiement. Veuillez réessayer plus tard."
    
    else:
        return "Une erreur inattendue s'est produite. Veuillez réessayer plus tard."

# Exemple d'utilisation
try:
    # Code utilisant MVola API
    result = client.initiate_payment(...)
except Exception as e:
    # Journaliser l'erreur technique détaillée
    logger.error(f"Erreur: {e}", exc_info=True)
    
    # Afficher un message convivial à l'utilisateur
    user_message = get_user_friendly_message(e)
    print(user_message)
```

## Bonnes pratiques pour la gestion des erreurs

1. **Utilisez la hiérarchie d'exceptions** pour capturer les erreurs à différents niveaux de spécificité.

2. **Validez les données en amont** pour éviter les erreurs prévisibles.

3. **Implémentez des retries** pour les erreurs temporaires, avec un backoff exponentiel.

4. **Journalisez les erreurs** avec suffisamment de contexte pour faciliter le débogage.

5. **Présentez des messages d'erreur conviviaux** à l'utilisateur final, sans exposer les détails techniques.

6. **Testez vos scénarios d'erreur** pour vous assurer que votre application les gère correctement.

7. **Mettez en place une surveillance** pour être alerté des erreurs récurrentes.

## Exemple complet

Voici un exemple complet combinant plusieurs techniques de gestion des erreurs :

```python
import time
import logging
from mvola_api import MVolaClient
from mvola_api.exceptions import (
    MVolaInvalidCredentialsError,
    MVolaTokenExpiredError,
    MVolaTransactionValidationError,
    MVolaConnectionError,
    MVolaRequestTimeoutError,
    MVolaServerError,
    MVolaError
)

# Configuration du logging
logger = logging.getLogger("mvola")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("mvola.log")
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

def process_payment(amount, debit_msisdn, credit_msisdn, description):
    """
    Traite un paiement MVola avec une gestion complète des erreurs.
    
    Args:
        amount: Montant du paiement
        debit_msisdn: Numéro du payeur
        credit_msisdn: Numéro du bénéficiaire
        description: Description du paiement
        
    Returns:
        dict: Résultat de la transaction ou information d'erreur
    """
    # Générer une référence unique
    from mvola_api.utils import generate_reference
    reference = generate_reference(prefix="PAY")
    
    # Initialiser le client
    try:
        client = MVolaClient(
            consumer_key="votre_consumer_key",
            consumer_secret="votre_consumer_secret",
            partner_name="Nom de votre application",
            partner_msisdn="0343500003",
            sandbox=True,
            logger=logger
        )
    except MVolaInvalidCredentialsError as e:
        logger.error(f"Erreur d'initialisation - identifiants invalides: {e}")
        return {"success": False, "message": "Configuration incorrecte du service de paiement"}
    except MVolaError as e:
        logger.error(f"Erreur d'initialisation: {e}")
        return {"success": False, "message": "Impossible d'initialiser le service de paiement"}
    
    # Validation des données
    try:
        from mvola_api.utils import validate_msisdn
        validate_msisdn(debit_msisdn)
        validate_msisdn(credit_msisdn)
        
        if amount <= 0:
            raise MVolaTransactionValidationError("Le montant doit être positif", field="amount")
    except MVolaTransactionValidationError as e:
        logger.error(f"Validation échouée: {e}")
        if e.field == "amount":
            return {"success": False, "message": "Le montant spécifié n'est pas valide"}
        else:
            return {"success": False, "message": "Le numéro de téléphone fourni n'est pas valide"}
    
    # Initier le paiement avec retry pour les erreurs temporaires
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            transaction_info = client.initiate_payment(
                amount=amount,
                debit_msisdn=debit_msisdn,
                credit_msisdn=credit_msisdn,
                reference=reference,
                description=description
            )
            
            # Transaction initiée avec succès
            transaction_id = transaction_info.get('server_correlation_id')
            logger.info(f"Transaction initiée avec succès. ID: {transaction_id}")
            
            # Vérification du statut initial
            status_info = client.get_transaction_status(
                transaction_id=transaction_id,
                msisdn=debit_msisdn
            )
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "reference": reference,
                "status": status_info.get('status'),
                "message": "Transaction initiée avec succès"
            }
            
        except (MVolaRequestTimeoutError, MVolaServerError) as e:
            # Erreurs temporaires - implémenter retry
            retry_count += 1
            wait_time = 2 ** retry_count
            
            logger.warning(f"Erreur temporaire: {e}. Tentative {retry_count}/{max_retries} dans {wait_time}s")
            
            if retry_count >= max_retries:
                logger.error(f"Échec après {max_retries} tentatives: {e}")
                return {"success": False, "message": "Le service de paiement est temporairement indisponible"}
            
            time.sleep(wait_time)
            
        except MVolaTokenExpiredError as e:
            # Token expiré - rafraîchir et réessayer
            logger.warning(f"Token expiré: {e}")
            try:
                client.refresh_token()
                # Continuer la boucle pour réessayer
            except MVolaError as e:
                logger.error(f"Erreur lors du rafraîchissement du token: {e}")
                return {"success": False, "message": "Erreur d'authentification avec le service de paiement"}
            
        except MVolaTransactionValidationError as e:
            # Erreur de validation - pas de retry
            logger.error(f"Validation échouée: {e}")
            if e.field == "amount":
                return {"success": False, "message": "Le montant spécifié n'est pas valide"}
            elif e.field in ["debit_msisdn", "credit_msisdn"]:
                return {"success": False, "message": "Le numéro de téléphone fourni n'est pas valide"}
            else:
                return {"success": False, "message": "Certaines informations de paiement ne sont pas valides"}
            
        except MVolaConnectionError as e:
            # Erreur de connexion
            logger.error(f"Erreur de connexion: {e}")
            return {"success": False, "message": "Problème de connexion au service MVola"}
            
        except MVolaError as e:
            # Autres erreurs MVola
            logger.error(f"Erreur MVola: {e}")
            return {"success": False, "message": "Une erreur s'est produite lors du traitement de votre paiement"}
            
        except Exception as e:
            # Erreur inattendue
            logger.error(f"Erreur inattendue: {e}", exc_info=True)
            return {"success": False, "message": "Une erreur inattendue s'est produite"}
    
    # Ne devrait jamais atteindre ce point à cause des returns dans la boucle
    return {"success": False, "message": "Erreur inattendue lors du traitement du paiement"}

# Exemple d'utilisation
result = process_payment(
    amount=1000,
    debit_msisdn="0343500003",
    credit_msisdn="0343500004",
    description="Paiement test"
)

if result["success"]:
    print(f"Paiement en cours: {result['transaction_id']}")
    print(f"Statut: {result['status']}")
else:
    print(f"Erreur: {result['message']}")
```

## Voir aussi

- [Référence des exceptions](../api-reference/exceptions.md) - Documentation technique détaillée de toutes les exceptions
- [Guide d'authentification](authentication.md) - Comment gérer l'authentification
- [Guide des transactions](transactions.md) - Comment effectuer des transactions
- [Exemples d'utilisation basique](../examples/basic-usage.md) - Exemples simples d'utilisation de la bibliothèque

## Prochaines étapes

- Consultez le [guide des transactions](transactions.md) pour en savoir plus sur l'initiation des paiements
- Explorez les [exemples d'intégration web](../examples/web-integration.md) pour voir comment gérer les erreurs dans un contexte d'application web 