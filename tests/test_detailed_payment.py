#!/usr/bin/env python
"""
Test détaillé d'initiation de paiement avec l'API MVola
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime, timezone

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mvola_test")

# Ajouter le répertoire parent au chemin de recherche de modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvola_api import MVolaClient
from mvola_api.constants import TEST_MSISDN_1, TEST_MSISDN_2, SANDBOX_URL
from mvola_api.exceptions import MVolaError, MVolaAuthError, MVolaTransactionError

# Identifiants pour l'API MVola
CONSUMER_KEY = "gwazRgSr3HIIgfzUchatsMbqwzUa"
CONSUMER_SECRET = "Ix1FR6_EHu1KN18G487VNcEWEgYa"
PARTNER_NAME = "Test Partner Company"
PARTNER_MSISDN = TEST_MSISDN_2  # 0343500004 dans l'environnement sandbox

# Numéros MVola sandbox pour les tests
DEBIT_MSISDN = TEST_MSISDN_2  # 0343500004
CREDIT_MSISDN = TEST_MSISDN_1  # 0343500003

def test_authentication():
    """Test l'authentification et la génération de token"""
    logger.info("===== TEST D'AUTHENTIFICATION =====")
    
    try:
        client = MVolaClient(
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            partner_name=PARTNER_NAME,
            partner_msisdn=PARTNER_MSISDN,
            sandbox=True
        )
        
        token_data = client.generate_token()
        
        logger.info(f"✅ Token généré avec succès")
        logger.info(f"Token type: {token_data['token_type']}")
        logger.info(f"Scope: {token_data['scope']}")
        logger.info(f"Expiration: {token_data['expires_in']} secondes")
        logger.info(f"Access Token: {token_data['access_token'][:20]}...")
        
        return client, token_data['access_token']
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'authentification: {str(e)}")
        raise

def test_manual_payment_initiation(access_token):
    """Test d'initiation de paiement avec contrôle manuel des paramètres"""
    logger.info("===== TEST D'INITIATION DE PAIEMENT MANUEL =====")
    
    try:
        # Générer un ID de corrélation unique
        import uuid
        correlation_id = str(uuid.uuid4())
        
        # Paramètres de transaction
        amount = 1000
        description = "Test Transaction Payment"
        callback_url = "https://example.com/webhook/mvola-callback"
        request_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        transaction_ref = f"ref{str(uuid.uuid4())[:8]}"
        
        # Afficher les paramètres utilisés
        logger.info(f"Montant: {amount} Ar")
        logger.info(f"Description: {description}")
        logger.info(f"Débiteur (msisdn): {DEBIT_MSISDN}")
        logger.info(f"Créditeur (msisdn): {CREDIT_MSISDN}")
        logger.info(f"URL de callback: {callback_url}")
        logger.info(f"Request Date: {request_date}")
        logger.info(f"Transaction Ref: {transaction_ref}")
        logger.info(f"Correlation ID: {correlation_id}")
        
        # Construction manuelle des en-têtes selon la documentation
        headers = {
            "accept": "*/*",
            "Version": "1.0",
            "X-CorrelationID": correlation_id,
            "UserLanguage": "FR",
            "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
            "partnerName": PARTNER_NAME,
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        if callback_url:
            headers["X-Callback-URL"] = callback_url
        
        # Construction manuelle du corps de la requête selon la documentation
        payload = {
            "amount": str(amount),
            "currency": "Ar",
            "descriptionText": description,
            "requestDate": request_date,
            "requestingOrganisationTransactionReference": transaction_ref,
            "originalTransactionReference": "",
            "debitParty": [{"key": "msisdn", "value": DEBIT_MSISDN}],
            "creditParty": [{"key": "msisdn", "value": CREDIT_MSISDN}],
            "metadata": [
                {"key": "partnerName", "value": PARTNER_NAME},
                {"key": "fc", "value": "EUR"},
                {"key": "amountFc", "value": "2"}
            ]
        }
        
        # Affichage des en-têtes et du corps pour debug
        logger.debug(f"En-têtes: {json.dumps(headers, indent=2)}")
        logger.debug(f"Corps: {json.dumps(payload, indent=2)}")
        
        # URL complète
        url = f"{SANDBOX_URL}/mvola/mm/transactions/type/merchantpay/1.0.0/"
        logger.info(f"URL: {url}")
        
        # Envoi de la requête
        response = requests.post(url, headers=headers, json=payload)
        
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
            logger.info(f"✅ Paiement initié avec succès")
            logger.info(f"Server Correlation ID: {response_data.get('serverCorrelationId', 'N/A')}")
            logger.info(f"Status: {response_data.get('status', 'N/A')}")
            logger.info(f"Notification Method: {response_data.get('notificationMethod', 'N/A')}")
            
            # Sauvegarde du serverCorrelationId pour les tests suivants
            with open("server_correlation_id.txt", "w") as f:
                f.write(response_data.get('serverCorrelationId', ''))
                
            return response_data
        else:
            logger.error(f"❌ Erreur {response.status_code} lors de l'initiation du paiement")
            return None
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {str(e)}")
        raise

def test_payment_status(access_token, server_correlation_id):
    """Vérifie le statut d'une transaction en cours"""
    logger.info("===== TEST DE VÉRIFICATION DE STATUT =====")
    
    try:
        # Générer un ID de corrélation unique
        import uuid
        correlation_id = str(uuid.uuid4())
        
        # Construction des en-têtes
        headers = {
            "accept": "*/*",
            "Version": "1.0",
            "X-CorrelationID": correlation_id,
            "UserLanguage": "FR",
            "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
            "partnerName": PARTNER_NAME,
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        # URL complète
        url = f"{SANDBOX_URL}/mvola/mm/transactions/type/merchantpay/1.0.0/status/{server_correlation_id}"
        logger.info(f"URL: {url}")
        
        # Envoi de la requête
        response = requests.get(url, headers=headers)
        
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
            logger.info(f"✅ Vérification de statut réussie")
            logger.info(f"Status: {response_data.get('status', 'N/A')}")
            return response_data
        else:
            logger.error(f"❌ Erreur {response.status_code} lors de la vérification du statut")
            return None
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {str(e)}")
        raise

def test_payment_initiation(client):
    """Test l'initiation d'un paiement marchand avec journalisation détaillée"""
    logger.info("===== TEST D'INITIATION DE PAIEMENT VIA CLIENT =====")
    
    try:
        # Activer le logging des requêtes HTTP
        import http.client as http_client
        http_client.HTTPConnection.debuglevel = 1
        
        # Afficher tous les headers de requête et réponse
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        
        # Paramètres de transaction
        amount = 1000
        description = "Test Transaction Payment"
        callback_url = "https://example.com/webhook/mvola-callback"
        
        # Afficher les paramètres utilisés
        logger.info(f"Montant: {amount} Ar")
        logger.info(f"Description: {description}")
        logger.info(f"Débiteur (msisdn): {DEBIT_MSISDN}")
        logger.info(f"Créditeur (msisdn): {CREDIT_MSISDN}")
        logger.info(f"URL de callback: {callback_url}")
        
        # Tenter d'initier le paiement
        result = client.initiate_payment(
            amount=amount,
            debit_msisdn=DEBIT_MSISDN,
            credit_msisdn=CREDIT_MSISDN,
            description=description,
            callback_url=callback_url,
            foreign_currency="EUR",
            foreign_amount=2
        )
        
        # Afficher le résultat
        logger.info(f"✅ Paiement initié avec succès")
        logger.info(f"Status code: {result['status_code']}")
        logger.info(f"Status: {result['response']['status']}")
        logger.info(f"Server Correlation ID: {result['response']['serverCorrelationId']}")
        logger.info(f"Notification Method: {result['response']['notificationMethod']}")
        
        return result
    except MVolaTransactionError as e:
        logger.error(f"❌ Erreur de transaction: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Réponse brute: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Test d'authentification
        client, access_token = test_authentication()
        
        # Test d'initiation de paiement manuel (pour mieux contrôler et déboguer)
        logger.info("\n")
        manual_result = test_manual_payment_initiation(access_token)
        
        # Si le test manuel réussit, vérifier le statut et essayer avec le client
        if manual_result:
            server_correlation_id = manual_result.get('serverCorrelationId')
            logger.info("\n")
            
            # Vérification du statut
            if server_correlation_id:
                status_result = test_payment_status(access_token, server_correlation_id)
                
                # Essai avec le client
                logger.info("\n")
                payment_result = test_payment_initiation(client)
                
                # Affichage du résumé final
                logger.info("===== RÉSUMÉ DES TESTS =====")
                logger.info("✅ Authentification: Réussie")
                logger.info("✅ Initiation de paiement manuel: Réussie")
                logger.info(f"✅ Vérification de statut: {status_result.get('status', 'N/A')}")
                if payment_result:
                    logger.info("✅ Initiation de paiement via client: Réussie")
                else:
                    logger.info("❌ Initiation de paiement via client: Échouée")
            else:
                logger.info("===== RÉSUMÉ DES TESTS =====")
                logger.info("✅ Authentification: Réussie")
                logger.info("✅ Initiation de paiement manuel: Réussie")
                logger.info("❌ Vérification de statut: Non effectuée (pas de serverCorrelationId)")
                logger.info("❌ Initiation de paiement via client: Non tentée")
        else:
            logger.info("===== RÉSUMÉ DES TESTS =====")
            logger.info("✅ Authentification: Réussie")
            logger.info("❌ Initiation de paiement manuel: Échouée")
            logger.info("❌ Initiation de paiement via client: Non tentée")
    except Exception as e:
        logger.error(f"❌ Test échoué: {str(e)}") 