#!/usr/bin/env python
"""
Test d'intégration avec l'API MVola basé strictement sur la documentation officielle.
Suit exactement le format des requêtes tel que spécifié dans la documentation MVola.
"""

import os
import sys
import json
import uuid
import requests
import logging
from datetime import datetime, timezone

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mvola_test")

# Ajouter le répertoire parent au chemin de recherche de modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Paramètres MVola selon la documentation
SANDBOX_URL = "https://devapi.mvola.mg"
PRODUCTION_URL = "https://api.mvola.mg"
MERCHANT_PAY_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/"
STATUS_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/status/"
DETAILS_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/"

# Identifiants pour l'API MVola
CONSUMER_KEY = "gwazRgSr3HIIgfzUchatsMbqwzUa"
CONSUMER_SECRET = "Ix1FR6_EHu1KN18G487VNcEWEgYa"
PARTNER_NAME = "Test Partner Company"
PARTNER_MSISDN = "0343500004"  # Numéro partenaire dans l'environnement sandbox

# Numéros MVola sandbox pour les tests
DEBIT_MSISDN = "0343500004"  # Numéro du débiteur
CREDIT_MSISDN = "0343500003"  # Numéro du créditeur

def get_access_token():
    """Obtient un token d'accès selon la documentation"""
    logger.info("Génération du token d'accès")
    
    # Construction des en-têtes pour la requête d'authentification
    auth_headers = {
        "Authorization": f"Basic {encode_credentials(CONSUMER_KEY, CONSUMER_SECRET)}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache"
    }
    
    # Corps de la requête d'authentification
    auth_data = {
        "grant_type": "client_credentials",
        "scope": "EXT_INT_MVOLA_SCOPE"
    }
    
    # URL d'authentification
    auth_url = f"{SANDBOX_URL}/token"
    
    try:
        response = requests.post(auth_url, headers=auth_headers, data=auth_data)
        response.raise_for_status()
        
        token_data = response.json()
        logger.info(f"Token généré avec succès (expire dans {token_data['expires_in']} secondes)")
        
        return token_data["access_token"]
    except Exception as e:
        logger.error(f"Erreur lors de la génération du token: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Réponse brute: {e.response.text}")
        raise

def encode_credentials(key, secret):
    """Encode les credentials en base64 pour l'authentification Basic"""
    import base64
    credentials = f"{key}:{secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return encoded

def initiate_transaction(access_token):
    """
    Initie une transaction de paiement marchand exactement selon la documentation MVola
    """
    logger.info("Initiation d'une transaction de paiement marchand")
    
    # Générer un ID de corrélation unique
    correlation_id = str(uuid.uuid4())
    
    # Date de la requête au format requis
    request_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    # Référence de transaction
    transaction_ref = f"ref{str(uuid.uuid4())[:8]}"
    
    # URL de callback (optionnelle)
    callback_url = "https://example.com/webhook/mvola-callback"
    
    # Construction des en-têtes exactement selon la documentation
    headers = {
        "Version": "1.0",
        "X-CorrelationID": correlation_id,
        "UserLanguage": "FR",
        "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
        "partnerName": PARTNER_NAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cache-Control": "no-cache"
    }
    
    # Ajouter le header de callback si nécessaire
    if callback_url:
        headers["X-Callback-URL"] = callback_url
    
    # Construction du corps de la requête exactement selon la documentation
    payload = {
        "amount": "1000",
        "currency": "Ar",
        "descriptionText": "Test Transaction MVola API",
        "requestDate": request_date,
        "requestingOrganisationTransactionReference": transaction_ref,
        "originalTransactionReference": "",
        "debitParty": [
            {
                "key": "msisdn",
                "value": DEBIT_MSISDN
            }
        ],
        "creditParty": [
            {
                "key": "msisdn",
                "value": CREDIT_MSISDN
            }
        ],
        "metadata": [
            {
                "key": "partnerName",
                "value": PARTNER_NAME
            },
            {
                "key": "fc",
                "value": "USD"
            },
            {
                "key": "amountFc",
                "value": "1"
            }
        ]
    }
    
    # Affichage des détails de la requête
    logger.info(f"URL: {SANDBOX_URL}{MERCHANT_PAY_ENDPOINT}")
    logger.info(f"Corrélation ID: {correlation_id}")
    logger.info(f"Montant: 1000 Ar")
    logger.info(f"Description: Test Transaction MVola API")
    logger.info(f"Date de la requête: {request_date}")
    logger.info(f"Référence de transaction: {transaction_ref}")
    logger.info(f"Débiteur: {DEBIT_MSISDN}")
    logger.info(f"Créditeur: {CREDIT_MSISDN}")
    
    logger.debug(f"En-têtes complets: {json.dumps(headers, indent=2)}")
    logger.debug(f"Corps complet: {json.dumps(payload, indent=2)}")
    
    # Envoi de la requête
    try:
        response = requests.post(f"{SANDBOX_URL}{MERCHANT_PAY_ENDPOINT}", headers=headers, json=payload)
        
        # Traitement de la réponse
        try:
            response_data = response.json()
        except:
            response_data = {"error": "Could not parse JSON response"}
        
        # Affichage de la réponse
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {json.dumps(response_data, indent=2)}")
        
        # Vérification du succès
        if response.status_code == 200:
            logger.info(f"✅ Transaction initiée avec succès")
            logger.info(f"Status: {response_data.get('status', 'N/A')}")
            logger.info(f"Server Correlation ID: {response_data.get('serverCorrelationId', 'N/A')}")
            logger.info(f"Notification Method: {response_data.get('notificationMethod', 'N/A')}")
            
            # Sauvegarde du serverCorrelationId pour les tests suivants
            server_correlation_id = response_data.get('serverCorrelationId', '')
            with open("server_correlation_id.txt", "w") as f:
                f.write(server_correlation_id)
            
            return response_data, server_correlation_id
        else:
            logger.error(f"❌ Erreur {response.status_code} lors de l'initiation de la transaction")
            return None, None
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {str(e)}")
        raise

def check_transaction_status(access_token, server_correlation_id):
    """
    Vérifie le statut d'une transaction selon la documentation MVola
    """
    logger.info("Vérification du statut de la transaction")
    
    # Générer un ID de corrélation unique
    correlation_id = str(uuid.uuid4())
    
    # Construction des en-têtes exactement selon la documentation
    headers = {
        "Version": "1.0",
        "X-CorrelationID": correlation_id,
        "UserLanguage": "FR",
        "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
        "partnerName": PARTNER_NAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cache-Control": "no-cache"
    }
    
    # URL pour la vérification du statut
    status_url = f"{SANDBOX_URL}{STATUS_ENDPOINT}{server_correlation_id}"
    
    logger.info(f"URL: {status_url}")
    logger.info(f"Server Correlation ID: {server_correlation_id}")
    
    # Envoi de la requête
    try:
        response = requests.get(status_url, headers=headers)
        
        # Traitement de la réponse
        try:
            response_data = response.json()
        except:
            response_data = {"error": "Could not parse JSON response"}
        
        # Affichage de la réponse
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {json.dumps(response_data, indent=2)}")
        
        # Vérification du succès
        if response.status_code == 200:
            logger.info(f"✅ Vérification du statut réussie")
            logger.info(f"Status: {response_data.get('status', 'N/A')}")
            
            # Si la transaction est complétée et a une objectReference, la sauvegarder
            if 'objectReference' in response_data and response_data['objectReference']:
                transaction_id = response_data['objectReference']
                with open("transaction_id.txt", "w") as f:
                    f.write(transaction_id)
                logger.info(f"Transaction ID sauvegardé: {transaction_id}")
            
            return response_data
        else:
            logger.error(f"❌ Erreur {response.status_code} lors de la vérification du statut")
            return None
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {str(e)}")
        raise

def get_transaction_details(access_token, transaction_id):
    """
    Récupère les détails d'une transaction selon la documentation MVola
    """
    logger.info("Récupération des détails de la transaction")
    
    # Générer un ID de corrélation unique
    correlation_id = str(uuid.uuid4())
    
    # Construction des en-têtes exactement selon la documentation
    headers = {
        "Version": "1.0",
        "X-CorrelationID": correlation_id,
        "UserLanguage": "FR",
        "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
        "partnerName": PARTNER_NAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cache-Control": "no-cache"
    }
    
    # URL pour les détails de la transaction
    details_url = f"{SANDBOX_URL}{DETAILS_ENDPOINT}{transaction_id}"
    
    logger.info(f"URL: {details_url}")
    logger.info(f"Transaction ID: {transaction_id}")
    
    # Envoi de la requête
    try:
        response = requests.get(details_url, headers=headers)
        
        # Traitement de la réponse
        try:
            response_data = response.json()
        except:
            response_data = {"error": "Could not parse JSON response"}
        
        # Affichage de la réponse
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {json.dumps(response_data, indent=2)}")
        
        # Vérification du succès
        if response.status_code == 200:
            logger.info(f"✅ Récupération des détails réussie")
            logger.info(f"Montant: {response_data.get('amount', 'N/A')} {response_data.get('currency', 'N/A')}")
            logger.info(f"Statut: {response_data.get('transactionStatus', 'N/A')}")
            logger.info(f"Date de création: {response_data.get('createDate', 'N/A')}")
            
            return response_data
        else:
            logger.error(f"❌ Erreur {response.status_code} lors de la récupération des détails")
            return None
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {str(e)}")
        raise

def run_test_sequence():
    """Exécute la séquence complète de test"""
    logger.info("=== DÉBUT DE LA SÉQUENCE DE TEST ===")
    
    try:
        # 1. Obtention du token d'accès
        logger.info("\n=== 1. AUTHENTIFICATION ===")
        access_token = get_access_token()
        
        # 2. Initiation de la transaction
        logger.info("\n=== 2. INITIATION DE TRANSACTION ===")
        transaction_data, server_correlation_id = initiate_transaction(access_token)
        
        if not server_correlation_id:
            logger.error("Impossible de continuer sans server_correlation_id")
            return
        
        # 3. Vérification du statut de la transaction
        logger.info("\n=== 3. VÉRIFICATION DU STATUT ===")
        status_data = check_transaction_status(access_token, server_correlation_id)
        
        # Si la transaction est complétée et a un ID de transaction, obtenir les détails
        if status_data and status_data.get('status') == 'completed' and 'objectReference' in status_data and status_data['objectReference']:
            transaction_id = status_data['objectReference']
            
            # 4. Récupération des détails de la transaction
            logger.info("\n=== 4. DÉTAILS DE LA TRANSACTION ===")
            details_data = get_transaction_details(access_token, transaction_id)
        else:
            logger.info("La transaction n'est pas complétée ou n'a pas d'ID, impossible d'obtenir les détails")
        
        logger.info("\n=== FIN DE LA SÉQUENCE DE TEST ===")
    except Exception as e:
        logger.error(f"Erreur lors de la séquence de test: {str(e)}")

if __name__ == "__main__":
    run_test_sequence() 