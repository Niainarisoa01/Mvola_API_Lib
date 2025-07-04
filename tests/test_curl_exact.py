#!/usr/bin/env python
"""
Test d'initiation de paiement MVola basé sur la commande CURL exacte fournie dans la documentation.

Commande CURL originale:
curl --location --request POST 'https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/' \
--header 'Version: 1.0' \
--header 'X-CorrelationID: {{XCorrelationID}}' \
--header 'UserLanguage: mg' \
--header 'UserAccountIdentifier: msisdn;{{partnerMSISDN}} \
--header 'partnerName: {{partnerName}}' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <ACCESS_TOKEN> \
--header 'Cache-Control: no-cache' \
--data-raw '{ "amount": "{{amount}}", "currency": "Ar", "descriptionText": "{{description}}", 
"requestingOrganisationTransactionReference": "", "requestDate": "", 
"originalTransactionReference": "", "debitParty": [ { "key": "msisdn", "value": "{{customerMSISDN}}" } ], 
"creditParty": [ { "key": "msisdn", "value": "{{partnerMSISDN}}" } ], 
"metadata": [ { "key": "partnerName", "value": "{{partnerName}}" }, 
{ "key": "fc", "value": "USD" }, { "key": "amountFc", "value": "1" } ]}'
"""

import os
import sys
import json
import uuid
import requests
import logging
import base64
from datetime import datetime, timezone

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mvola_test")

# Identifiants pour l'API MVola
CONSUMER_KEY = "vmLAxEyX4MRbfbnqZOifGxUIOxoa"
CONSUMER_SECRET = "GW029VAsHRgb6ubNCMuyEb0SwIsa"
PARTNER_NAME = "Test Partner Company"
PARTNER_MSISDN = "0343500004"  # Numéro partenaire dans l'environnement sandbox
CUSTOMER_MSISDN = "0343500003"  # Numéro client dans l'environnement sandbox

def encode_credentials(key, secret):
    """Encode les credentials en base64 pour l'authentification Basic"""
    credentials = f"{key}:{secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return encoded

def get_token():
    """Obtient un token d'accès"""
    logger.info("Obtention du token d'accès")
    
    auth_url = "https://devapi.mvola.mg/token"
    
    auth_headers = {
        "Authorization": f"Basic {encode_credentials(CONSUMER_KEY, CONSUMER_SECRET)}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache"
    }
    
    auth_data = {
        "grant_type": "client_credentials",
        "scope": "EXT_INT_MVOLA_SCOPE"
    }
    
    try:
        response = requests.post(auth_url, headers=auth_headers, data=auth_data)
        response.raise_for_status()
        
        token_data = response.json()
        logger.info(f"Token généré avec succès")
        
        return token_data["access_token"]
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention du token: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Réponse brute: {e.response.text}")
        raise

def initiate_payment_curl_exact():
    """
    Initie un paiement en suivant exactement la commande CURL de la documentation
    """
    logger.info("Initiation du paiement (méthode CURL exacte)")
    
    # Obtention du token
    access_token = get_token()
    
    # Génération d'un ID de corrélation unique
    correlation_id = str(uuid.uuid4())
    
    # URL de l'API
    url = "https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/"
    
    # En-têtes exactement comme dans la commande CURL
    headers = {
        "Version": "1.0",
        "X-CorrelationID": correlation_id,
        "UserLanguage": "MG",  # La documentation utilise 'mg', mais nous utilisons 'FR' pour la cohérence
        "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
        "partnerName": PARTNER_NAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cache-Control": "no-cache"
    }
    
    # Données exactement comme dans la commande CURL
    # Note importante: dans l'exemple CURL, requestDate est une chaîne vide
    data = {
        "amount": "1000",
        "currency": "Ar",
        "descriptionText": "Test Transaction MVola API",
        "requestingOrganisationTransactionReference": "",
        "requestDate": "",  # Chaîne vide comme dans l'exemple
        "originalTransactionReference": "",
        "debitParty": [
            {
                "key": "msisdn",
                "value": CUSTOMER_MSISDN  # Dans l'exemple, c'est le customer qui est débiteur
            }
        ],
        "creditParty": [
            {
                "key": "msisdn",
                "value": PARTNER_MSISDN  # Dans l'exemple, c'est le partner qui est créditeur
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
    logger.info(f"URL: {url}")
    logger.info(f"Corrélation ID: {correlation_id}")
    logger.debug(f"En-têtes: {json.dumps(headers, indent=2)}")
    logger.debug(f"Corps: {json.dumps(data, indent=2)}")
    
    # Envoi de la requête
    try:
        response = requests.post(url, headers=headers, json=data)
        
        try:
            response_data = response.json()
        except:
            response_data = {"error": "Could not parse JSON response"}
        
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {json.dumps(response_data, indent=2)}")
        
        return response.status_code, response_data
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la requête: {str(e)}")
        raise

def initiate_payment_curl_updated():
    """
    Initie un paiement en suivant la commande CURL avec requestDate mise à jour
    """
    logger.info("Initiation du paiement (méthode CURL avec requestDate)")
    
    # Obtention du token
    access_token = get_token()
    
    # Génération d'un ID de corrélation unique
    correlation_id = str(uuid.uuid4())
    
    # Génération d'une référence de transaction
    transaction_ref = f"ref{str(uuid.uuid4())[:8]}"
    
    # Date de la requête au format requis
    request_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    # URL de l'API
    url = "https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/"
    
    # En-têtes exactement comme dans la commande CURL
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
    
    # Données comme dans la commande CURL mais avec requestDate remplie
    data = {
        "amount": "1000",
        "currency": "Ar",
        "descriptionText": "Test Transaction MVola API",
        "requestingOrganisationTransactionReference": transaction_ref,  # Ajout d'une référence
        "requestDate": request_date,  # Date de requête ajoutée
        "originalTransactionReference": "1234567890",
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
    
    # Affichage des détails de la requête
    logger.info(f"URL: {url}")
    logger.info(f"Corrélation ID: {correlation_id}")
    logger.info(f"Request Date: {request_date}")
    logger.info(f"Transaction Ref: {transaction_ref}")
    logger.debug(f"En-têtes: {json.dumps(headers, indent=2)}")
    logger.debug(f"Corps: {json.dumps(data, indent=2)}")
    
    # Envoi de la requête
    try:
        response = requests.post(url, headers=headers, json=data)
        
        try:
            response_data = response.json()
        except:
            response_data = {"error": "Could not parse JSON response"}
        
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {json.dumps(response_data, indent=2)}")
        
        return response.status_code, response_data
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la requête: {str(e)}")
        raise

def initiate_payment_working_example():
    """
    Initie un paiement en utilisant l'exemple CURL fonctionnel fourni par l'utilisateur
    """
    logger.info("Initiation du paiement (exemple CURL fonctionnel)")
    
    # URL de l'API
    url = "https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/"
    
    # Token d'accès fixe pour le test (à remplacer par get_token() dans un environnement réel)
    # Dans l'exemple, le token est fourni directement
    access_token = get_token()  # Utilisez cette ligne pour générer un token dynamique
    # access_token = "eyJ4NXQiOiJaREUzWW1RNFkyRmtZekprTmpNMk5EVmtZVE5oTkRSak16azFObVEyWXprelkyUTFaVFZqWVEiLCJraWQiOiJNVGRsTXpneFpqZGtNakk4WmpKbVlUZ3dNRFJpWWpNMU1tUmhOamxoTUdNME1XTmtPV05tT1RobU16VXlNMlUxTkRZNE5UWXhOMk01TW1SbU5XUTRPQV9SUzI1NiIsInR5cCI6ImF0K2p3dCIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJsb3ZhNjdAcHJvdG9ubWFpbC5jb20iLCJhdXQiOiJBUFBMSUNBVElPTiIsImF1ZCI6InlMdmVSdVVPc09scmNqUEVZMlVnZjhMOGhVa2EiLCJuYmYiOjE3NTE2MTIzNTUsImF6cCI6InlMdmVSdVVPc09scmNqUEVZMlVnZjhMOGhVa2EiLCJzY29wZSI6IkVYVF9JTlRfTVZPTEFfU0NPUEUiLCJpc3MiOiJodHRwczpcL1wvZGV2ZWxvcGVyLm12b2xhLm1nXC9vYXV0aDJcL3Rva2VuIiwicmVhbG0iOnsic2lnbmluZ190ZW5hbnQiOiJjYXJib24uc3VwZXIifSwiZXhwIjoxNzUxNjE1OTU1LCJpYXQiOjE3NTE2MTIzNTUsImp0aSI6Ijk4MmIxMzMwLTEyMTItNDk5Yi1iMWUxLTNkYjhjNDllNjc5OSJ9.LttlOyFFdpVwlIWA0aMThiEnVdMLy-zTbNgm81yVrIZkyNR9fs8qbXolg6v1cGs6pOndZrOAUge7d3rS2c2V_vwGchaVd-7ctwcgBa5tt1Qxo7pwfm7otzqiOvLElKsLypXBDfZUMeKrOIDEu5QrFYerqj97b2uUn17RJhvQ4TXsAMlXnkRxkoeBttouCEIxoXuTfC2CaiZNcc_UgHWPIkICu9WRP-0mDqnln33vy8yPI-sG5fVUGAS7cEN6Fd9tb88xVP-f3KWW5gAbQ8OcmZk1KYk8y4N8YTvwrjuthKrN_V4jx5z-1ElEMcUZbQhnrMHtDEku_BMheGVNrE2W6A"  # Décommentez pour utiliser le token fixe
    
    # En-têtes exactement comme dans la commande CURL fonctionnelle
    headers = {
        "version": "1.0",
        "UserLanguage": "MG",
        "X-CorrelationID": "123",  # ID fixe pour tester
        "X-Callback-URL": "https://fastapi-slev.onrender.com/debug",
        "Accept-Charset": "utf-8",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    # Données exactement comme dans la commande CURL fonctionnelle
    data = {
        "amount": "1000",
        "currency": "Ar",
        "descriptionText": "Client test 0349262379 Tasty Plastic Bacon",
        "requestingOrganisationTransactionReference": "61120259",
        "requestDate": "2025-07-04T09:55:39.458Z",
        "originalTransactionReference": "MVOLA_123",
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
                "value": "0343500004"
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
    logger.info(f"URL: {url}")
    logger.info(f"Corrélation ID: {headers['X-CorrelationID']}")
    logger.debug(f"En-têtes: {json.dumps(headers, indent=2)}")
    logger.debug(f"Corps: {json.dumps(data, indent=2)}")
    
    # Envoi de la requête
    try:
        response = requests.post(url, headers=headers, json=data)
        
        try:
            response_data = response.json()
        except:
            response_data = {"error": "Could not parse JSON response"}
        
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {json.dumps(response_data, indent=2)}")
        
        return response.status_code, response_data
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la requête: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("=== TEST DE LA COMMANDE CURL EXACTE ===")
    
    try:
        # Test avec la commande CURL exacte (requestDate vide)
        logger.info("\n=== TEST 1: CURL EXACT ===")
        status_code_1, response_data_1 = initiate_payment_curl_exact()
        
        # Test avec la commande CURL modifiée (requestDate remplie)
        logger.info("\n=== TEST 2: CURL AVEC requestDate ===")
        status_code_2, response_data_2 = initiate_payment_curl_updated()
        
        # Test avec l'exemple CURL fonctionnel fourni par l'utilisateur
        logger.info("\n=== TEST 3: EXEMPLE CURL FONCTIONNEL ===")
        status_code_3, response_data_3 = initiate_payment_working_example()
        
        # Résumé
        logger.info("\n=== RÉSUMÉ DES TESTS ===")
        logger.info(f"Test 1 (CURL exact): {status_code_1}")
        logger.info(f"Test 2 (CURL avec requestDate): {status_code_2}")
        logger.info(f"Test 3 (Exemple CURL fonctionnel): {status_code_3}")
        
    except Exception as e:
        logger.error(f"Erreur lors des tests: {str(e)}") 