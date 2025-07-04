#!/usr/bin/env python
"""
Test de la bibliothèque MVola avec les modifications apportées pour résoudre le problème 
des champs manquants dans l'initiation de paiement.
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mvola_test")

# Ajouter le répertoire parent au chemin de recherche de modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer la bibliothèque MVola
from mvola_api.client import MVolaClient
from mvola_api.auth import MVolaAuth
from mvola_api.constants import SANDBOX_URL, TEST_MSISDN_1, TEST_MSISDN_2

# Identifiants pour l'API MVola
CONSUMER_KEY = "gwazRgSr3HIIgfzUchatsMbqwzUa"
CONSUMER_SECRET = "Ix1FR6_EHu1KN18G487VNcEWEgYa"
PARTNER_NAME = "Test Partner Company"
PARTNER_MSISDN = TEST_MSISDN_2  # 0343500004
CUSTOMER_MSISDN = TEST_MSISDN_1  # 0343500003

def test_authentication():
    """Test l'authentification à l'API MVola"""
    logger.info("=== TEST AUTHENTIFICATION ===")
    
    auth = MVolaAuth(CONSUMER_KEY, CONSUMER_SECRET, SANDBOX_URL)
    
    try:
        token_data = auth.generate_token()
        logger.info(f"✅ Authentification réussie")
        logger.info(f"Token: {token_data['access_token'][:30]}...")
        logger.info(f"Expire dans: {token_data['expires_in']} secondes")
        return token_data
    except Exception as e:
        logger.error(f"❌ Échec de l'authentification: {str(e)}")
        raise

def test_initiate_payment():
    """Test l'initiation d'un paiement avec la bibliothèque mise à jour"""
    logger.info("=== TEST INITIATION DE PAIEMENT ===")
    
    # Créer un client MVola
    client = MVolaClient(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        partner_name=PARTNER_NAME,
        partner_msisdn=PARTNER_MSISDN,
        sandbox=True
    )
    
    # Paramètres de la transaction
    amount = "1000"
    description = "Test Transaction MVola API"
    
    try:
        # Générer un token (pour être sûr qu'il est frais)
        token_data = client.generate_token(force_refresh=True)
        logger.info(f"Token généré: {token_data['access_token'][:30]}...")
        
        # Initier un paiement
        transaction_data = client.initiate_payment(
            amount=amount,
            debit_msisdn=CUSTOMER_MSISDN,  # Le client qui paie
            credit_msisdn=PARTNER_MSISDN,  # Le marchand qui reçoit
            description=description,
            callback_url="https://example.com/webhook/mvola-callback"
        )
        
        # Afficher le résultat
        logger.info(f"✅ Paiement initié avec succès")
        logger.info(f"Status code: {transaction_data['status_code']}")
        logger.info(f"Correlation ID: {transaction_data.get('correlation_id', '')}")
        logger.info(f"Réponse: {json.dumps(transaction_data['response'], indent=2)}")
        
        # Sauvegarder le server_correlation_id pour les tests futurs
        server_correlation_id = transaction_data['response'].get('serverCorrelationId', '')
        if server_correlation_id:
            with open("server_correlation_id.txt", "w") as f:
                f.write(server_correlation_id)
            logger.info(f"Server Correlation ID sauvegardé: {server_correlation_id}")
        
        return transaction_data
    except Exception as e:
        logger.error(f"❌ Échec de l'initiation du paiement: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Réponse brute: {e.response.text}")
        raise

def test_transaction_status(server_correlation_id=None):
    """Test la vérification du statut d'une transaction"""
    logger.info("=== TEST VÉRIFICATION DU STATUT ===")
    
    # Si aucun server_correlation_id n'est fourni, essayer de le charger du fichier
    if not server_correlation_id:
        try:
            with open("server_correlation_id.txt", "r") as f:
                server_correlation_id = f.read().strip()
        except FileNotFoundError:
            logger.error("Aucun server_correlation_id trouvé")
            return None
    
    # Créer un client MVola
    client = MVolaClient(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        partner_name=PARTNER_NAME,
        partner_msisdn=PARTNER_MSISDN,
        sandbox=True
    )
    
    try:
        # Vérifier le statut
        status_data = client.get_transaction_status(server_correlation_id)
        
        # Afficher le résultat
        logger.info(f"✅ Statut vérifié avec succès")
        logger.info(f"Status code: {status_data['status_code']}")
        logger.info(f"Réponse: {json.dumps(status_data['response'], indent=2)}")
        
        # Si la transaction est complétée et a une référence, la sauvegarder
        if 'objectReference' in status_data['response']:
            transaction_id = status_data['response']['objectReference']
            with open("transaction_id.txt", "w") as f:
                f.write(transaction_id)
            logger.info(f"Transaction ID sauvegardé: {transaction_id}")
        
        return status_data
    except Exception as e:
        logger.error(f"❌ Échec de la vérification du statut: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Réponse brute: {e.response.text}")
        raise

def test_transaction_details(transaction_id=None):
    """Test la récupération des détails d'une transaction"""
    logger.info("=== TEST DÉTAILS DE LA TRANSACTION ===")
    
    # Si aucun transaction_id n'est fourni, essayer de le charger du fichier
    if not transaction_id:
        try:
            with open("transaction_id.txt", "r") as f:
                transaction_id = f.read().strip()
        except FileNotFoundError:
            logger.error("Aucun transaction_id trouvé")
            return None
    
    # Créer un client MVola
    client = MVolaClient(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        partner_name=PARTNER_NAME,
        partner_msisdn=PARTNER_MSISDN,
        sandbox=True
    )
    
    try:
        # Récupérer les détails
        details_data = client.get_transaction_details(transaction_id)
        
        # Afficher le résultat
        logger.info(f"✅ Détails récupérés avec succès")
        logger.info(f"Status code: {details_data['status_code']}")
        logger.info(f"Réponse: {json.dumps(details_data['response'], indent=2)}")
        
        return details_data
    except Exception as e:
        logger.error(f"❌ Échec de la récupération des détails: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Réponse brute: {e.response.text}")
        raise

def run_test_sequence():
    """Exécute la séquence complète de test"""
    logger.info("=== DÉBUT DE LA SÉQUENCE DE TEST ===")
    
    try:
        # 1. Test d'authentification
        token_data = test_authentication()
        
        # 2. Test d'initiation de paiement
        transaction_data = test_initiate_payment()
        
        # Si l'initiation a réussi et renvoie un server_correlation_id
        if transaction_data and 'response' in transaction_data and 'serverCorrelationId' in transaction_data['response']:
            server_correlation_id = transaction_data['response']['serverCorrelationId']
            
            # 3. Test de vérification du statut
            status_data = test_transaction_status(server_correlation_id)
            
            # Si le statut est complété et contient un objectReference
            if status_data and 'response' in status_data and 'objectReference' in status_data['response']:
                transaction_id = status_data['response']['objectReference']
                
                # 4. Test de récupération des détails
                details_data = test_transaction_details(transaction_id)
        
        logger.info("=== FIN DE LA SÉQUENCE DE TEST ===")
    except Exception as e:
        logger.error(f"Erreur lors de la séquence de test: {str(e)}")

if __name__ == "__main__":
    run_test_sequence() 