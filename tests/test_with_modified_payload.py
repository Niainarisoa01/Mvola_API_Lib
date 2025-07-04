#!/usr/bin/env python
"""
Test de l'API MVola avec une structure de payload modifiée

Ce script teste l'initiation de paiement MVola en modifiant directement la structure du payload
pour correspondre exactement au format dans la documentation partagée par l'utilisateur.
"""

import os
import sys
import json
import logging
from datetime import datetime
import uuid
import requests
from urllib.parse import urljoin

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mvola_test")

# Ajouter le répertoire parent au chemin de recherche de modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer la bibliothèque MVola
from mvola_api.auth import MVolaAuth
from mvola_api.constants import (
    SANDBOX_URL,
    API_VERSION,
    TEST_MSISDN_1,
    TEST_MSISDN_2,
    MERCHANT_PAY_ENDPOINT
)

# Identifiants pour l'API MVola
CONSUMER_KEY = "gwazRgSr3HIIgfzUchatsMbqwzUa"
CONSUMER_SECRET = "Ix1FR6_EHu1KN18G487VNcEWEgYa"
PARTNER_NAME = "Test Partner Company"
PARTNER_MSISDN = TEST_MSISDN_2  # 0343500004
CUSTOMER_MSISDN = TEST_MSISDN_1  # 0343500003

def get_current_datetime():
    """
    Get current datetime in ISO 8601 format

    Returns:
        str: Formatted datetime
    """
    # Use timezone-aware UTC datetime
    from datetime import timezone
    return (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        + "Z"
    )

def test_direct_api_call():
    """
    Test direct avec l'API MVola sans utiliser les modules de la bibliothèque
    pour avoir un contrôle complet sur le format du payload et des en-têtes
    """
    logger.info("=== TEST DIRECT AVEC API MVOLA (CONTOURNEMENT DE LA BIBLIOTHÈQUE) ===")
    
    # Créer l'objet d'authentification et générer un token
    auth = MVolaAuth(CONSUMER_KEY, CONSUMER_SECRET, SANDBOX_URL)
    auth.generate_token(force_refresh=True)
    access_token = auth.get_access_token()
    
    # Paramètres de la transaction
    amount = "1000"
    description = "Test Transaction MVola API"
    correlation_id = str(uuid.uuid4())
    transaction_ref = f"ref{str(uuid.uuid4())[:8]}"
    request_date = get_current_datetime()
    
    # Valeurs fictives pour les en-têtes de localisation (à adapter selon le besoin)
    cell_id_a = "123456"
    geo_location_a = "-18.8792,47.5079"  # Coordonnées d'Antananarivo
    cell_id_b = "654321"
    geo_location_b = "-18.1667,49.4167"  # Coordonnées de Toamasina
    
    # En-têtes exactement comme dans la documentation
    headers = {
        "Version": API_VERSION,
        "X-CorrelationID": correlation_id,
        "UserLanguage": "FR",
        "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
        "partnerName": PARTNER_NAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cache-Control": "no-cache",
        "Accept": "*/*",
        "Accept-Charset": "UTF-8",
        "CellIdA": cell_id_a,
        "GeoLocationA": geo_location_a,
        "CellIdB": cell_id_b,
        "GeoLocationB": geo_location_b,
        "X-Callback-URL": "https://example.com/webhook/mvola-callback"
    }
    
    # Payload exactement comme dans la documentation
    payload = {
        "amount": amount,
        "currency": "Ar",
        "descriptionText": description,
        "requestingOrganisationTransactionReference": transaction_ref,
        "requestDate": request_date,
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
    
    # URL de l'API
    url = urljoin(SANDBOX_URL, MERCHANT_PAY_ENDPOINT)
    
    # Afficher les détails de la requête pour le débogage
    logger.info(f"URL: {url}")
    logger.info(f"Headers: {json.dumps(headers, indent=2)}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Envoi de la requête
        logger.info("Envoi de la requête à l'API MVola...")
        response = requests.post(url, headers=headers, json=payload)
        
        # Tenter de récupérer les détails de la réponse, qu'elle soit réussie ou non
        try:
            response_data = response.json()
        except:
            response_data = {"raw_text": response.text}
        
        # Vérifier si la requête a réussi
        if response.status_code < 400:
            logger.info(f"✅ Paiement initié avec succès")
            logger.info(f"Status code: {response.status_code}")
            logger.info(f"Réponse: {json.dumps(response_data, indent=2)}")
            return {
                "success": True,
                "status_code": response.status_code,
                "response": response_data,
                "correlation_id": correlation_id
            }
        else:
            logger.error(f"❌ Échec de l'initiation du paiement")
            logger.error(f"Status code: {response.status_code}")
            logger.error(f"Réponse d'erreur: {json.dumps(response_data, indent=2)}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response_data,
                "correlation_id": correlation_id
            }
    except Exception as e:
        logger.error(f"❌ Exception lors de l'envoi de la requête: {str(e)}")
        raise

def test_with_minimal_payload():
    """
    Test avec un payload minimal pour voir quels champs sont réellement requis
    """
    logger.info("=== TEST AVEC PAYLOAD MINIMAL ===")
    
    # Créer l'objet d'authentification et générer un token
    auth = MVolaAuth(CONSUMER_KEY, CONSUMER_SECRET, SANDBOX_URL)
    auth.generate_token(force_refresh=True)
    access_token = auth.get_access_token()
    
    # Paramètres de la transaction
    amount = "1000"
    description = "Test Transaction MVola API"
    correlation_id = str(uuid.uuid4())
    request_date = get_current_datetime()
    
    # En-têtes HTTP minimaux mais essentiels
    headers = {
        "Version": API_VERSION,
        "X-CorrelationID": correlation_id,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cache-Control": "no-cache"
    }
    
    # Payload minimal avec uniquement les champs qui semblent essentiels
    payload = {
        "amount": amount,
        "currency": "Ar",
        "descriptionText": description,
        "requestDate": request_date,
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
        ]
    }
    
    # URL de l'API
    url = urljoin(SANDBOX_URL, MERCHANT_PAY_ENDPOINT)
    
    try:
        # Envoi de la requête
        logger.info("Envoi de la requête minimale à l'API MVola...")
        response = requests.post(url, headers=headers, json=payload)
        
        # Tenter de récupérer les détails de la réponse, qu'elle soit réussie ou non
        try:
            response_data = response.json()
        except:
            response_data = {"raw_text": response.text}
        
        # Afficher la réponse indépendamment du résultat
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Réponse: {json.dumps(response_data, indent=2)}")
        
        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "response": response_data,
            "correlation_id": correlation_id
        }
    except Exception as e:
        logger.error(f"❌ Exception lors de l'envoi de la requête: {str(e)}")
        raise

def main():
    """Exécute les tests avec différentes approches de payload"""
    logger.info("=== DÉBUT DES TESTS AVEC PAYLOAD MODIFIÉ ===")
    logger.info(f"Date et heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test direct avec l'API MVola
        direct_result = test_direct_api_call()
        
        print("\n" + "="*80 + "\n")
        
        # Test avec un payload minimal
        minimal_result = test_with_minimal_payload()
        
        # Vérifier si l'un des tests a réussi
        if direct_result.get("success") or minimal_result.get("success"):
            logger.info("=== AU MOINS UN TEST A RÉUSSI ===")
            return 0
        else:
            logger.error("=== TOUS LES TESTS ONT ÉCHOUÉ ===")
            return 1
    except Exception as e:
        logger.error(f"Erreur lors des tests: {str(e)}")
        logger.error("=== ÉCHEC DES TESTS ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 