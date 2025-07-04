#!/usr/bin/env python
"""
Script de débogage pour l'API MVola avec affichage détaillé des requêtes et réponses.
"""

import os
import sys
import json
import logging
import requests
import base64
from datetime import datetime, timezone
import uuid

# Configuration du logging avancé
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mvola_debug")

# Ajouter le répertoire parent au chemin de recherche de modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Identifiants pour l'API MVola
CONSUMER_KEY = "gwazRgSr3HIIgfzUchatsMbqwzUa"
CONSUMER_SECRET = "Ix1FR6_EHu1KN18G487VNcEWEgYa"
PARTNER_NAME = "Test Partner Company"
PARTNER_MSISDN = "0343500004"  # Numéro partenaire dans l'environnement sandbox
CUSTOMER_MSISDN = "0343500003"  # Numéro client dans l'environnement sandbox

# URLs et endpoints
SANDBOX_URL = "https://devapi.mvola.mg"
TOKEN_ENDPOINT = "/token"
MERCHANT_PAY_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/"

# Activer les logs HTTP pour les requêtes et réponses
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

def encode_credentials(key, secret):
    """Encode les credentials en base64 pour l'authentification Basic"""
    credentials = f"{key}:{secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return encoded

def get_access_token():
    """Obtenir un token d'accès avec journalisation détaillée"""
    logger.info("Obtention du token d'accès - DÉBUT")
    
    auth_url = f"{SANDBOX_URL}{TOKEN_ENDPOINT}"
    
    auth_headers = {
        "Authorization": f"Basic {encode_credentials(CONSUMER_KEY, CONSUMER_SECRET)}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache"
    }
    
    auth_data = {
        "grant_type": "client_credentials",
        "scope": "EXT_INT_MVOLA_SCOPE"
    }
    
    logger.debug(f"URL: {auth_url}")
    logger.debug(f"Headers: {json.dumps(auth_headers, indent=2)}")
    logger.debug(f"Data: {json.dumps(auth_data, indent=2)}")
    
    try:
        response = requests.post(auth_url, headers=auth_headers, data=auth_data)
        
        logger.debug(f"Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            token_data = response.json()
            logger.info(f"✅ Token obtenu avec succès")
            logger.debug(f"Token Data: {json.dumps(token_data, indent=2)}")
            return token_data["access_token"]
        else:
            logger.error(f"❌ Échec de l'obtention du token: {response.status_code}")
            try:
                error_data = response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Réponse brute: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Exception lors de l'obtention du token: {str(e)}")
        return None

def test_direct_api_call():
    """
    Test direct de l'API MVola avec requêtes HTTP brutes et journalisation maximale
    """
    logger.info("=== TEST DIRECT DE L'API MVOLA ===")
    
    # 1. Obtenir un token d'accès
    access_token = get_access_token()
    if not access_token:
        logger.error("Impossible de continuer sans token d'accès")
        return
    
    # 2. Initier un paiement
    logger.info("=== INITIATION DE PAIEMENT - DÉBUT ===")
    
    # Générer des données pour la requête
    correlation_id = str(uuid.uuid4())
    request_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    transaction_ref = f"ref{str(uuid.uuid4())[:8]}"
    
    # En-têtes selon la documentation exacte
    headers = {
        "Version": "1.0",
        "X-CorrelationID": correlation_id,
        "UserLanguage": "FR",
        "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
        "partnerName": PARTNER_NAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cache-Control": "no-cache",
        "X-Callback-URL": "https://example.com/webhook/mvola-callback"
    }
    
    # Corps de la requête selon la documentation exacte
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
                "value": CUSTOMER_MSISDN
            }
        ],
        "creditParty": [
            {
                "key": "msisdn",
                "value": PARTNER_MSISDN
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
    
    # Afficher les détails de la requête
    url = f"{SANDBOX_URL}{MERCHANT_PAY_ENDPOINT}"
    logger.debug(f"URL: {url}")
    logger.debug(f"Correlation ID: {correlation_id}")
    logger.debug(f"Headers: {json.dumps(headers, indent=2)}")
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Faire la requête
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        logger.debug(f"Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            logger.debug(f"Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            logger.debug(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            logger.info(f"✅ Paiement initié avec succès")
            if 'serverCorrelationId' in response_data:
                logger.info(f"Server Correlation ID: {response_data['serverCorrelationId']}")
        else:
            logger.error(f"❌ Échec de l'initiation du paiement: {response.status_code}")
            
            # Essayer d'extraire des détails d'erreur
            try:
                error_data = response.json()
                if 'errorCategory' in error_data and 'errorCode' in error_data:
                    logger.error(f"Catégorie d'erreur: {error_data['errorCategory']}")
                    logger.error(f"Code d'erreur: {error_data['errorCode']}")
                    logger.error(f"Description: {error_data['errorDescription']}")
                    
                    # Vérifier s'il y a des paramètres d'erreur plus spécifiques
                    if 'errorParameters' in error_data:
                        for param in error_data['errorParameters']:
                            logger.error(f"Paramètre d'erreur: {param['key']} = {param['value']}")
            except:
                logger.error(f"Impossible d'analyser les détails de l'erreur")
    
    except Exception as e:
        logger.error(f"❌ Exception lors de l'initiation du paiement: {str(e)}")

# Variante avec des champs de métadonnées supplémentaires pour résoudre le problème "Missing field"
def test_enhanced_metadata():
    """
    Test avec des métadonnées améliorées pour résoudre le problème de champ manquant
    """
    logger.info("=== TEST AVEC MÉTADONNÉES AMÉLIORÉES ===")
    
    # 1. Obtenir un token d'accès
    access_token = get_access_token()
    if not access_token:
        logger.error("Impossible de continuer sans token d'accès")
        return
    
    # 2. Initier un paiement
    logger.info("=== INITIATION DE PAIEMENT AVEC MÉTADONNÉES AMÉLIORÉES - DÉBUT ===")
    
    # Générer des données pour la requête
    correlation_id = str(uuid.uuid4())
    request_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    transaction_ref = f"ref{str(uuid.uuid4())[:8]}"
    
    # En-têtes selon la documentation exacte
    headers = {
        "Version": "1.0",
        "X-CorrelationID": correlation_id,
        "UserLanguage": "FR",
        "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
        "partnerName": PARTNER_NAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cache-Control": "no-cache",
        "X-Callback-URL": "https://example.com/webhook/mvola-callback"
    }
    
    # Corps de la requête avec métadonnées améliorées
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
                "value": CUSTOMER_MSISDN
            }
        ],
        "creditParty": [
            {
                "key": "msisdn",
                "value": PARTNER_MSISDN
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
            },
            # Métadonnées supplémentaires pour tester
            {
                "key": "reference",
                "value": transaction_ref
            },
            {
                "key": "service",
                "value": "payment"
            },
            {
                "key": "clientReference",
                "value": f"client-{str(uuid.uuid4())[:8]}"
            }
        ]
    }
    
    # Afficher les détails de la requête
    url = f"{SANDBOX_URL}{MERCHANT_PAY_ENDPOINT}"
    logger.debug(f"URL: {url}")
    logger.debug(f"Correlation ID: {correlation_id}")
    logger.debug(f"Headers: {json.dumps(headers, indent=2)}")
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Faire la requête
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        logger.debug(f"Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            logger.debug(f"Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            logger.debug(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            logger.info(f"✅ Paiement initié avec succès")
            if 'serverCorrelationId' in response_data:
                logger.info(f"Server Correlation ID: {response_data['serverCorrelationId']}")
        else:
            logger.error(f"❌ Échec de l'initiation du paiement: {response.status_code}")
            
            # Essayer d'extraire des détails d'erreur
            try:
                error_data = response.json()
                if 'errorCategory' in error_data and 'errorCode' in error_data:
                    logger.error(f"Catégorie d'erreur: {error_data['errorCategory']}")
                    logger.error(f"Code d'erreur: {error_data['errorCode']}")
                    logger.error(f"Description: {error_data['errorDescription']}")
                    
                    # Vérifier s'il y a des paramètres d'erreur plus spécifiques
                    if 'errorParameters' in error_data:
                        for param in error_data['errorParameters']:
                            logger.error(f"Paramètre d'erreur: {param['key']} = {param['value']}")
            except:
                logger.error(f"Impossible d'analyser les détails de l'erreur")
    
    except Exception as e:
        logger.error(f"❌ Exception lors de l'initiation du paiement: {str(e)}")

if __name__ == "__main__":
    # Test standard
    test_direct_api_call()
    
    print("\n" + "="*80 + "\n")
    
    # Test avec métadonnées améliorées
    test_enhanced_metadata()