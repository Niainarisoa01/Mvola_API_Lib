#!/usr/bin/env python
"""
Test de l'API MVola avec en-têtes HTTP supplémentaires

Ce script teste l'initiation de paiement MVola en incluant des en-têtes HTTP supplémentaires
qui ont été identifiés dans la documentation complète : CellIdA, GeoLocationA, CellIdB, 
GeoLocationB, Accept et Accept-Charset.
"""

import os
import sys
import json
import logging
from datetime import datetime
import uuid

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mvola_test")

# Ajouter le répertoire parent au chemin de recherche de modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer la bibliothèque MVola
from mvola_api.client import MVolaClient
from mvola_api.auth import MVolaAuth
from mvola_api.constants import SANDBOX_URL, TEST_MSISDN_1, TEST_MSISDN_2
from mvola_api.transaction import MVolaTransaction

# Identifiants pour l'API MVola
CONSUMER_KEY = "gwazRgSr3HIIgfzUchatsMbqwzUa"
CONSUMER_SECRET = "Ix1FR6_EHu1KN18G487VNcEWEgYa"
PARTNER_NAME = "Test Partner Company"
PARTNER_MSISDN = TEST_MSISDN_2  # 0343500004
CUSTOMER_MSISDN = TEST_MSISDN_1  # 0343500003

def test_with_transaction_module():
    """
    Test direct avec le module Transaction pour avoir plus de contrôle sur les en-têtes
    """
    logger.info("=== TEST AVEC MODULE TRANSACTION ET EN-TÊTES SUPPLÉMENTAIRES ===")
    
    # Créer les objets nécessaires
    auth = MVolaAuth(CONSUMER_KEY, CONSUMER_SECRET, SANDBOX_URL)
    transaction = MVolaTransaction(auth, SANDBOX_URL, PARTNER_NAME, PARTNER_MSISDN)
    
    # S'assurer que le token est valide
    auth.generate_token(force_refresh=True)
    
    # Paramètres de la transaction
    amount = "1000"
    description = "Test Transaction MVola API"
    correlation_id = str(uuid.uuid4())
    transaction_ref = f"ref{str(uuid.uuid4())[:8]}"
    
    # Valeurs fictives pour les en-têtes de localisation (à adapter selon le besoin)
    cell_id_a = "123456"
    geo_location_a = "-18.8792,47.5079"  # Coordonnées d'Antananarivo
    cell_id_b = "654321"
    geo_location_b = "-18.1667,49.4167"  # Coordonnées de Toamasina
    
    try:
        # Initier un paiement avec tous les en-têtes supplémentaires
        logger.info("Initiation de paiement avec en-têtes supplémentaires...")
        transaction_data = transaction.initiate_merchant_payment(
            amount=amount,
            debit_msisdn=CUSTOMER_MSISDN,
            credit_msisdn=PARTNER_MSISDN,
            description=description,
            correlation_id=correlation_id,
            callback_url="https://example.com/webhook/mvola-callback",
            requesting_organisation_transaction_reference=transaction_ref,
            cell_id_a=cell_id_a,
            geo_location_a=geo_location_a,
            cell_id_b=cell_id_b,
            geo_location_b=geo_location_b
        )
        
        # Afficher le résultat
        logger.info(f"✅ Paiement initié avec succès")
        logger.info(f"Status code: {transaction_data['status_code']}")
        logger.info(f"Correlation ID: {transaction_data.get('correlation_id', '')}")
        logger.info(f"Réponse: {json.dumps(transaction_data['response'], indent=2)}")
        
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

def test_with_client():
    """
    Test avec le client MVola
    Note: Le client MVolaClient n'expose pas directement les paramètres d'en-têtes supplémentaires,
    donc nous modifions le module transaction sous-jacent pour ce test.
    """
    logger.info("=== TEST AVEC CLIENT MVOLA ET EN-TÊTES SUPPLÉMENTAIRES ===")
    
    # Créer un client MVola
    client = MVolaClient(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        partner_name=PARTNER_NAME,
        partner_msisdn=PARTNER_MSISDN,
        sandbox=True
    )
    
    # Ajouter des valeurs fictives pour les en-têtes de localisation à l'objet transaction sous-jacent
    cell_id_a = "123456"
    geo_location_a = "-18.8792,47.5079"  # Coordonnées d'Antananarivo
    cell_id_b = "654321"
    geo_location_b = "-18.1667,49.4167"  # Coordonnées de Toamasina
    
    # Modifier la méthode _get_headers de l'objet transaction pour inclure les en-têtes supplémentaires
    original_get_headers = client.transaction._get_headers
    
    def enhanced_get_headers(*args, **kwargs):
        headers = original_get_headers(*args, **kwargs)
        headers["CellIdA"] = cell_id_a
        headers["GeoLocationA"] = geo_location_a
        headers["CellIdB"] = cell_id_b
        headers["GeoLocationB"] = geo_location_b
        headers["Accept"] = "*/*"
        headers["Accept-Charset"] = "UTF-8"
        return headers
    
    # Remplacer temporairement la méthode
    client.transaction._get_headers = enhanced_get_headers
    
    try:
        # Paramètres de la transaction
        amount = "1000"
        description = "Test Transaction MVola API"
        
        # Générer un token (pour être sûr qu'il est frais)
        token_data = client.generate_token(force_refresh=True)
        logger.info(f"Token généré: {token_data['access_token'][:30]}...")
        
        # Initier un paiement
        transaction_data = client.initiate_payment(
            amount=amount,
            debit_msisdn=CUSTOMER_MSISDN,
            credit_msisdn=PARTNER_MSISDN,
            description=description,
            callback_url="https://example.com/webhook/mvola-callback"
        )
        
        # Afficher le résultat
        logger.info(f"✅ Paiement initié avec succès")
        logger.info(f"Status code: {transaction_data['status_code']}")
        logger.info(f"Correlation ID: {transaction_data.get('correlation_id', '')}")
        logger.info(f"Réponse: {json.dumps(transaction_data['response'], indent=2)}")
        
        # Restaurer la méthode originale
        client.transaction._get_headers = original_get_headers
        
        return transaction_data
    except Exception as e:
        # Restaurer la méthode originale en cas d'erreur
        client.transaction._get_headers = original_get_headers
        
        logger.error(f"❌ Échec de l'initiation du paiement: {str(e)}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                logger.error(f"Détails de l'erreur: {json.dumps(error_data, indent=2)}")
            except:
                logger.error(f"Réponse brute: {e.response.text}")
        raise

def main():
    """Exécute les tests avec les en-têtes supplémentaires"""
    logger.info("=== DÉBUT DES TESTS AVEC EN-TÊTES SUPPLÉMENTAIRES ===")
    logger.info(f"Date et heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test avec le module Transaction
        transaction_result = test_with_transaction_module()
        
        print("\n" + "="*80 + "\n")
        
        # Test avec le client MVola
        client_result = test_with_client()
        
        logger.info("=== TOUS LES TESTS ONT RÉUSSI ===")
        return 0
    except Exception as e:
        logger.error(f"Erreur lors des tests: {str(e)}")
        logger.error("=== ÉCHEC DES TESTS ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 