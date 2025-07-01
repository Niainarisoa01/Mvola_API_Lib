# Gestion des Webhooks

Ce guide explique comment configurer et gérer les webhooks pour les notifications de transactions MVola dans votre application.

## Qu'est-ce qu'un webhook?

Un webhook est un mécanisme qui permet à MVola d'envoyer automatiquement des notifications à votre application lorsqu'un événement se produit, comme un changement de statut de transaction. Au lieu de vérifier périodiquement le statut d'une transaction (polling), votre serveur reçoit une notification dès que le statut change.

## Architecture des webhooks

Voici comment les webhooks fonctionnent avec MVola:

1. Lors de l'initiation d'une transaction, vous fournissez une URL de callback
2. Le client confirme la transaction sur son téléphone mobile
3. MVola traite la transaction et met à jour son statut
4. MVola envoie une notification à votre URL de callback avec les détails de la transaction
5. Votre serveur traite cette notification et met à jour vos systèmes

```
┌─────────┐         ┌─────────┐         ┌─────────┐
│  Votre  │         │  API    │         │ Mobile  │
│ Serveur │◄────────│  MVola  │◄────────│ Client  │
└────┬────┘         └─────────┘         └─────────┘
     │                                        ▲
     │                                        │
     │                                        │
     └────────────────────────────────────────┘
            Notification par webhook
```

## Configuration d'un callback URL

Lorsque vous initiez un paiement, vous pouvez spécifier une URL de callback avec l'en-tête `X-Callback-URL` ou le paramètre `callback_url` dans la méthode :

```python
from mvola_api import MVolaClient

client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="NOM_DU_PARTENAIRE",
    partner_msisdn="0343500003",
    base_url="https://devapi.mvola.mg"  # URL de l'API sandbox
)

transaction_info = client.initiate_merchant_payment(
    amount="1000",
    debit_msisdn="0343500003",
    credit_msisdn="0343500004",
    description="Paiement produit",
    requesting_organisation_transaction_reference="REF123456",
    callback_url="https://votre-domaine.com/webhooks/mvola/callback"
)
```

Cette URL doit être accessible publiquement sur Internet pour que MVola puisse y envoyer des requêtes.

## Format des notifications de webhook

MVola envoie des notifications au format JSON via une requête PUT à votre URL de callback. Voici les formats typiques:

### Notification de succès

```json
{
  "transactionStatus": "completed",
  "serverCorrelationId": "421a22a2-ef1d-42bc-9452-f4939a3d5cdf",
  "transactionReference": "641235",
  "requestDate": "2021-02-24T03:28:00.567Z",
  "debitParty": [
    {
      "key": "msisdn",
      "value": "0343500003"
    }
  ],
  "creditParty": [
    {
      "key": "msisdn",
      "value": "0343500004"
    }
  ],
  "fees": [
    {
      "feeAmount": "20"
    }
  ],
  "metadata": [
    {
      "key": "partnerName",
      "value": "NomPartenaire"
    }
  ]
}
```

### Notification d'échec

```json
{
  "transactionStatus": "failed",
  "serverCorrelationId": "421a22a2-ef1d-42bc-9452-f4939a3d5cdf",
  "transactionReference": "641235",
  "requestDate": "2021-02-24T03:28:00.567Z",
  "debitParty": [
    {
      "key": "msisdn",
      "value": "0343500003"
    }
  ],
  "creditParty": [
    {
      "key": "msisdn",
      "value": "0343500004"
    }
  ],
  "metadata": [
    {
      "key": "partnerName",
      "value": "NomPartenaire"
    }
  ]
}
```

Les statuts possibles incluent:
- `pending`: La transaction est en attente de confirmation
- `completed`: La transaction a été traitée avec succès
- `failed`: La transaction a échoué

## Création d'un endpoint de webhook

### Avec Flask

Voici un exemple d'endpoint pour recevoir les notifications avec Flask:

```python
from flask import Blueprint, request, jsonify
import logging
import json

webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhooks')
logger = logging.getLogger('webhook')

@webhook_bp.route('/mvola/callback', methods=['PUT'])  # MVola utilise PUT pour les callbacks
def mvola_callback():
    # Récupérer les données du webhook
    webhook_data = request.get_json()
    
    if not webhook_data:
        logger.error("Données de webhook invalides ou vides")
        return jsonify({"status": "error", "message": "Invalid data"}), 400
    
    # Enregistrer les données pour débogage
    logger.info(f"Webhook reçu: {json.dumps(webhook_data)}")
    
    # Extraire les informations importantes
    server_correlation_id = webhook_data.get('serverCorrelationId')
    transaction_status = webhook_data.get('transactionStatus')
    transaction_reference = webhook_data.get('transactionReference')
    
    # Récupérer les numéros MSISDN
    debit_party = webhook_data.get('debitParty', [])
    debit_msisdn = next((item.get('value') for item in debit_party 
                         if item.get('key') == 'msisdn'), None)
    
    credit_party = webhook_data.get('creditParty', [])
    credit_msisdn = next((item.get('value') for item in credit_party 
                          if item.get('key') == 'msisdn'), None)
    
    # Récupérer les frais si disponibles
    fees = webhook_data.get('fees', [])
    fee_amount = next((fee.get('feeAmount') for fee in fees), None)
    
    # Traiter selon le statut
    if transaction_status == 'completed':
        # La transaction a réussi
        logger.info(f"Transaction {transaction_reference} complétée avec succès")
        # Mettre à jour votre base de données, envoyer un email, etc.
        update_transaction_status(server_correlation_id, transaction_status, transaction_reference)
        send_confirmation_email(debit_msisdn, webhook_data)
        
    elif transaction_status == 'failed':
        # La transaction a échoué
        logger.warning(f"Transaction {server_correlation_id} a échoué")
        update_transaction_status(server_correlation_id, transaction_status, transaction_reference)
        send_failure_notification(debit_msisdn, webhook_data)
    
    # Toujours retourner un succès (HTTP 200) pour indiquer que vous avez reçu la notification
    return jsonify({"status": "success"}), 200

def update_transaction_status(server_correlation_id, status, transaction_reference=None):
    # Implémentez la mise à jour de votre base de données
    pass

def send_confirmation_email(msisdn, webhook_data):
    # Envoyez un email de confirmation
    pass

def send_failure_notification(msisdn, webhook_data):
    # Envoyez une notification d'échec
    pass
```

### Avec Django

Voici un exemple avec Django:

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('webhooks/mvola/callback', views.mvola_callback, name='mvola_callback'),
]

# views.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger('mvola_webhooks')

@csrf_exempt  # Important: les webhooks externes ne peuvent pas fournir de token CSRF
@require_http_methods(["PUT"])  # MVola utilise PUT pour les callbacks
def mvola_callback(request):
    try:
        webhook_data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Données JSON invalides")
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    
    # Extraire les informations importantes
    server_correlation_id = webhook_data.get('serverCorrelationId')
    transaction_status = webhook_data.get('transactionStatus')
    transaction_reference = webhook_data.get('transactionReference')
    
    # Traiter les données selon le statut...
    
    return JsonResponse({"status": "success"})
```

## Sécurisation des webhooks

Pour sécuriser vos webhooks:

### Validation de la source

Vous pouvez valider que les requêtes proviennent bien de MVola en vérifiant les adresses IP ou en implémentant une authentification:

```python
def is_valid_mvola_request(request):
    # Liste des IPs autorisées (exemple fictif - à remplacer par les vraies IPs de MVola)
    allowed_ips = ['203.0.113.1', '203.0.113.2']
    client_ip = request.remote_addr
    
    return client_ip in allowed_ips

@webhook_bp.route('/mvola/callback', methods=['PUT'])
def mvola_callback():
    if not is_valid_mvola_request(request):
        logger.warning(f"Tentative d'accès non autorisée depuis {request.remote_addr}")
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    # Suite du traitement...
```

### Vérification des transactions

Validez systématiquement les données reçues en les comparant avec vos enregistrements:

```python
def validate_transaction(server_correlation_id, transaction_reference, debit_msisdn):
    # Récupérer la transaction depuis votre base de données
    stored_transaction = get_transaction_from_db(server_correlation_id)
    
    if not stored_transaction:
        logger.warning(f"Transaction inconnue: {server_correlation_id}")
        return False
    
    # Vérifier que les détails correspondent
    if stored_transaction.debit_msisdn != debit_msisdn:
        logger.warning(f"Détails de transaction non concordants: {server_correlation_id}")
        return False
    
    return True
```

## Gestion des erreurs et retransmissions

MVola peut retransmettre les notifications en cas d'échec. Votre endpoint doit être idempotent, c'est-à-dire qu'il doit pouvoir recevoir plusieurs fois la même notification sans causer de problèmes:

```python
def process_transaction_completion(server_correlation_id, transaction_status, transaction_reference):
    # Vérifier si la transaction a déjà été traitée
    if is_transaction_already_processed(server_correlation_id, transaction_reference):
        logger.info(f"Transaction {server_correlation_id} déjà traitée, ignorée")
        return
    
    # Traiter la transaction et marquer comme traitée
    mark_transaction_as_processed(server_correlation_id, transaction_status, transaction_reference)
    # Déclencher les actions correspondantes
    trigger_post_payment_actions(server_correlation_id, transaction_reference)
```

## Test des webhooks en développement

Pour tester les webhooks en développement local:

### Utilisation de ngrok

[ngrok](https://ngrok.com/) vous permet d'exposer votre serveur local à Internet:

```bash
# Installer ngrok
pip install pyngrok

# Exposer votre serveur local (ex: port 5000)
ngrok http 5000
```

ngrok vous fournira une URL publique (ex: `https://abc123.ngrok.io`) que vous pourrez utiliser comme URL de callback.

### Utilisation de requestbin

[RequestBin](https://requestbin.com/) permet de capturer et d'inspecter les requêtes HTTP:

1. Créez un nouveau bin sur RequestBin
2. Utilisez l'URL fournie comme URL de callback
3. Visualisez les requêtes reçues dans l'interface web

## Simulation de webhooks

Vous pouvez simuler des webhooks pour tester votre logique de traitement:

```python
# test_webhooks.py
import requests
import json
import uuid
from datetime import datetime

def simulate_webhook(callback_url, server_correlation_id, status):
    # Créer un payload de test
    webhook_data = {
        "transactionStatus": status,
        "serverCorrelationId": server_correlation_id,
        "transactionReference": f"REF-{uuid.uuid4().hex[:8].upper()}",
        "requestDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "debitParty": [
            {
                "key": "msisdn",
                "value": "0343500003"
            }
        ],
        "creditParty": [
            {
                "key": "msisdn",
                "value": "0343500004"
            }
        ]
    }
    
    # Ajouter les frais pour les transactions réussies
    if status == "completed":
        webhook_data["fees"] = [
            {
                "feeAmount": "20"
            }
        ]
    
    # Ajouter des métadonnées
    webhook_data["metadata"] = [
        {
            "key": "partnerName",
            "value": "NomPartenaire"
        }
    ]
    
    # Envoyer la requête PUT (MVola utilise PUT pour les callbacks)
    response = requests.put(
        callback_url,
        json=webhook_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Statut: {response.status_code}")
    print(f"Réponse: {response.text}")

# Simuler différents statuts
simulate_webhook("http://localhost:5000/webhooks/mvola/callback", 
                 "corr-" + str(uuid.uuid4()), "pending")
simulate_webhook("http://localhost:5000/webhooks/mvola/callback", 
                 "corr-" + str(uuid.uuid4()), "completed")
simulate_webhook("http://localhost:5000/webhooks/mvola/callback", 
                 "corr-" + str(uuid.uuid4()), "failed")
```

## Journalisation et monitoring

Implémentez une journalisation complète pour faciliter le débogage:

```python
import logging

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhooks.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('mvola_webhooks')

# Dans le handler de webhook
@webhook_bp.route('/mvola/callback', methods=['PUT'])
def mvola_callback():
    webhook_data = request.get_json()
    
    # Journalisation complète
    logger.info(f"Webhook reçu: {json.dumps(webhook_data)}")
    
    # Traitement...
    
    # Journalisation du résultat
    logger.info(f"Webhook traité avec succès pour la transaction {webhook_data.get('serverCorrelationId')}")
    
    return jsonify({"status": "success"}), 200
```

## Webhooks dans un environnement de production

Pour un environnement de production:

1. **Utiliser HTTPS**: Assurez-vous que votre endpoint est accessible en HTTPS
2. **Ajouter une surveillance**: Mettez en place des alertes en cas d'erreur de traitement
3. **Implémenter des retries**: Si votre logique interne échoue, mettez en place un mécanisme de retry
4. **Configurer des timeouts**: Limitez le temps de traitement des webhooks pour éviter les longues opérations
5. **Utiliser des queues**: Enregistrez les notifications dans une queue pour un traitement asynchrone

## Exemple complet d'intégration

Voici un exemple complet qui intègre toutes les bonnes pratiques:

```python
import json
import logging
import time
from flask import Blueprint, request, jsonify
from threading import Thread
from queue import Queue

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('mvola_webhooks')

# File d'attente pour le traitement asynchrone
webhook_queue = Queue()

webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhooks')

@webhook_bp.route('/mvola/callback', methods=['PUT'])
def mvola_callback():
    start_time = time.time()
    
    # 1. Validation de base
    if not request.is_json:
        logger.error("Content-Type non JSON")
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    
    webhook_data = request.get_json()
    
    if not webhook_data:
        logger.error("Données de webhook vides")
        return jsonify({"status": "error", "message": "Empty payload"}), 400
    
    # 2. Validation minimale des données requises
    server_correlation_id = webhook_data.get('serverCorrelationId')
    transaction_status = webhook_data.get('transactionStatus')
    
    if not server_correlation_id or not transaction_status:
        logger.error(f"Données incomplètes: {json.dumps(webhook_data)}")
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    
    # 3. Journalisation
    logger.info(f"Webhook reçu pour transaction {server_correlation_id}, statut: {transaction_status}")
    
    # 4. Traitement asynchrone pour éviter de bloquer la réponse
    webhook_queue.put(webhook_data)
    
    # 5. Répondre rapidement
    processing_time = time.time() - start_time
    logger.info(f"Webhook mis en file d'attente en {processing_time:.3f}s")
    
    return jsonify({
        "status": "success", 
        "message": "Webhook received and queued for processing",
        "server_correlation_id": server_correlation_id
    }), 200

# Traitement des webhooks en arrière-plan
def process_webhook_queue():
    while True:
        try:
            # Récupérer le prochain webhook à traiter
            webhook_data = webhook_queue.get()
            
            if not webhook_data:
                continue
                
            server_correlation_id = webhook_data.get('serverCorrelationId')
            transaction_status = webhook_data.get('transactionStatus')
            transaction_reference = webhook_data.get('transactionReference')
            
            logger.info(f"Traitement du webhook pour transaction {server_correlation_id}")
            
            # Vérifier si la transaction existe et n'a pas déjà été traitée
            transaction = get_transaction(server_correlation_id)
            
            if not transaction:
                logger.warning(f"Transaction inconnue: {server_correlation_id}")
                webhook_queue.task_done()
                continue
            
            if transaction.status == transaction_status:
                logger.info(f"Transaction {server_correlation_id} déjà dans l'état {transaction_status}, ignorée")
                webhook_queue.task_done()
                continue
            
            # Traiter selon le statut
            if transaction_status == 'completed':
                # Marquer la commande comme payée, envoyer confirmation, etc.
                complete_order(transaction, transaction_reference)
                logger.info(f"Transaction {server_correlation_id} complétée et traitée")
                
            elif transaction_status == 'failed':
                # Marquer la commande comme échouée
                fail_order(transaction)
                logger.info(f"Transaction {server_correlation_id} échouée")
                
            # Mettre à jour le statut dans la base de données
            update_transaction_status(server_correlation_id, transaction_status, transaction_reference)
            
            # Signaler que le traitement est terminé
            webhook_queue.task_done()
            
        except Exception as e:
            logger.exception(f"Erreur lors du traitement du webhook: {e}")
            # Continuer à traiter les autres webhooks même en cas d'erreur

# Démarrer le thread de traitement
webhook_processor = Thread(target=process_webhook_queue, daemon=True)
webhook_processor.start()

# Fonctions fictives à implémenter selon votre application
def get_transaction(server_correlation_id):
    # Récupérer la transaction depuis la base de données
    pass

def update_transaction_status(server_correlation_id, status, transaction_reference=None):
    # Mettre à jour le statut dans la base de données
    pass

def complete_order(transaction, transaction_reference):
    # Marquer la commande comme payée
    pass

def fail_order(transaction):
    # Marquer la commande comme échouée
    pass
```

## Conclusion

Les webhooks sont un mécanisme puissant pour construire des intégrations robustes avec MVola. En suivant ces bonnes pratiques, vous pourrez:

1. Recevoir des notifications en temps réel sur les changements de statut des transactions
2. Traiter ces notifications de manière fiable et sécurisée
3. Automatiser vos processus métier en fonction des paiements

## Prochaines étapes

- Consultez le guide [Intégration Web](web-integration.md) pour voir comment implémenter une solution de paiement complète
- Explorez la [gestion des erreurs](../guides/error-handling.md) pour rendre votre système encore plus robuste 