#!/usr/bin/env python
"""
Tentative finale de test de l'API MVola avec plusieurs variations des paramètres.
Ce script essaie plusieurs combinaisons de formats et champs pour identifier la cause
de l'erreur "Missing field" dans l'API MVola.
"""

import os
import sys
import json
import uuid
import requests
import logging
import base64
from datetime import datetime, timezone
import time

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mvola_test")

# Identifiants pour l'API MVola
CONSUMER_KEY = "gwazRgSr3HIIgfzUchatsMbqwzUa"
CONSUMER_SECRET = "Ix1FR6_EHu1KN18G487VNcEWEgYa"
PARTNER_NAME = "Test Partner Company"
PARTNER_MSISDN = "0343500004"  # Numéro partenaire dans l'environnement sandbox
CUSTOMER_MSISDN = "0343500003"  # Numéro client dans l'environnement sandbox

# URLs et endpoints
SANDBOX_URL = "https://devapi.mvola.mg"
MERCHANT_PAY_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/"

def encode_credentials(key, secret):
    """Encode les credentials en base64 pour l'authentification Basic"""
    credentials = f"{key}:{secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return encoded

def get_token():
    """Obtient un token d'accès"""
    logger.info("Obtention du token d'accès")
    
    auth_url = f"{SANDBOX_URL}/token"
    
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

def test_payment_variation(variation_name, headers, payload):
    """
    Teste une variation spécifique des paramètres de paiement
    """
    logger.info(f"=== TEST VARIATION: {variation_name} ===")
    
    url = f"{SANDBOX_URL}{MERCHANT_PAY_ENDPOINT}"
    
    logger.info(f"URL: {url}")
    logger.debug(f"En-têtes: {json.dumps(headers, indent=2)}")
    logger.debug(f"Corps: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        try:
            response_data = response.json()
        except:
            response_data = {"error": "Could not parse JSON response"}
        
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {json.dumps(response_data, indent=2)}")
        
        if response.status_code == 200:
            logger.info(f"✅ SUCCÈS pour la variation: {variation_name}")
        else:
            logger.info(f"❌ ÉCHEC pour la variation: {variation_name}")
        
        return response.status_code, response_data
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la requête: {str(e)}")
        raise

def run_test_variations():
    """
    Exécute plusieurs variations de tests pour trouver le format correct
    """
    # Obtention d'un token unique pour tous les tests
    access_token = get_token()
    
    # ID de corrélation pour les tests
    correlation_id = str(uuid.uuid4())
    
    # Date de la requête
    request_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    # Référence de transaction
    transaction_ref = f"ref{str(uuid.uuid4())[:8]}"
    
    # Headers de base pour tous les tests
    base_headers = {
        "Version": "1.0",
        "X-CorrelationID": correlation_id,
        "UserLanguage": "FR",
        "UserAccountIdentifier": f"msisdn;{PARTNER_MSISDN}",
        "partnerName": PARTNER_NAME,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Cache-Control": "no-cache"
    }
    
    # Liste des variations à tester
    variations = []
    
    # Variation 1: Exactement comme dans la documentation avec champs vides
    variations.append({
        "name": "Documentation exacte",
        "headers": base_headers.copy(),
        "payload": {
            "amount": "1000",
            "currency": "Ar",
            "descriptionText": "Test Transaction MVola API",
            "requestingOrganisationTransactionReference": "",
            "requestDate": "",
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
    })
    
    # Variation 2: Avec requestDate et requestingOrganisationTransactionReference remplis
    variations.append({
        "name": "Avec dates et références",
        "headers": base_headers.copy(),
        "payload": {
            "amount": "1000",
            "currency": "Ar",
            "descriptionText": "Test Transaction MVola API",
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
    })
    
    # Variation 3: Avec valeurs minimum requises et requestDate formatée comme dans le callback
    callback_date_format = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    variations.append({
        "name": "Format minimal avec date callback",
        "headers": base_headers.copy(),
        "payload": {
            "amount": "1000",
            "currency": "Ar",
            "descriptionText": "Test Transaction MVola API",
            "requestDate": callback_date_format,
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
    })
    
    # Variation 4: Avec différentes langues
    variation4_headers = base_headers.copy()
    variation4_headers["UserLanguage"] = "MG"  # Changer à MG comme dans la documentation
    variations.append({
        "name": "Avec langue MG",
        "headers": variation4_headers,
        "payload": {
            "amount": "1000",
            "currency": "Ar",
            "descriptionText": "Test Transaction MVola API",
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
    })
    
    # Variation 5: Avec des headers complémentaires et metadata supplémentaires
    variation5_headers = base_headers.copy()
    variation5_headers["X-Callback-URL"] = "https://example.com/webhook/mvola-callback"
    variations.append({
        "name": "Avec callback et metadata supplémentaires",
        "headers": variation5_headers,
        "payload": {
            "amount": "1000",
            "currency": "Ar",
            "descriptionText": "Test Transaction MVola API",
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
                },
                {
                    "key": "note",
                    "value": "Additional information"
                }
            ]
        }
    })
    
    # Variation 6: En inversant débiteur et créditeur (peut-être que la documentation est ambiguë)
    variations.append({
        "name": "Débiteur et créditeur inversés",
        "headers": base_headers.copy(),
        "payload": {
            "amount": "1000",
            "currency": "Ar",
            "descriptionText": "Test Transaction MVola API",
            "requestingOrganisationTransactionReference": transaction_ref,
            "requestDate": request_date,
            "originalTransactionReference": "",
            "debitParty": [
                {
                    "key": "msisdn",
                    "value": PARTNER_MSISDN  # Inverser ici
                }
            ],
            "creditParty": [
                {
                    "key": "msisdn",
                    "value": CUSTOMER_MSISDN  # Inverser ici
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
    })
    
    # Variation 7: Avec une structure simplifiée
    variations.append({
        "name": "Structure simplifiée",
        "headers": base_headers.copy(),
        "payload": {
            "amount": "1000",
            "currency": "Ar",
            "descriptionText": "Test Transaction MVola API",
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
    })
    
    # Exécuter chaque variation
    results = []
    for variation in variations:
        try:
            status_code, response_data = test_payment_variation(
                variation["name"], 
                variation["headers"], 
                variation["payload"]
            )
            results.append({
                "name": variation["name"],
                "status_code": status_code,
                "success": status_code == 200,
                "response": response_data
            })
            
            # Pause entre les requêtes pour éviter les limites de taux
            time.sleep(1)
        except Exception as e:
            logger.error(f"Erreur lors du test de la variation {variation['name']}: {str(e)}")
            results.append({
                "name": variation["name"],
                "status_code": None,
                "success": False,
                "error": str(e)
            })
    
    # Afficher le résumé des résultats
    logger.info("\n=== RÉSUMÉ DES TESTS ===")
    for result in results:
        status = "✅ SUCCÈS" if result["success"] else "❌ ÉCHEC"
        logger.info(f"{status} - {result['name']} (Code: {result['status_code']})")
        
    # Afficher les détails des succès (si présents)
    success_results = [r for r in results if r["success"]]
    if success_results:
        logger.info("\n=== DÉTAILS DES SUCCÈS ===")
        for success in success_results:
            logger.info(f"Variation: {success['name']}")
            logger.info(f"Response: {json.dumps(success['response'], indent=2)}")
    else:
        logger.info("\nAucun test n'a réussi. Vérifiez les détails des erreurs ci-dessus.")

if __name__ == "__main__":
    logger.info("=== DÉBUT DES TESTS DE VARIATIONS ===")
    run_test_variations() 