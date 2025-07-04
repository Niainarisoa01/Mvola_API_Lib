#!/usr/bin/env python
"""
Exemple simple d'authentification avec l'API MVola

Ce script démontre comment initialiser un client MVola et générer un token d'authentification.
L'authentification est la partie de l'API MVola qui fonctionne de manière fiable.
"""

import os
import sys
import logging
from datetime import datetime

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mvola_example")

# Ajouter le répertoire parent au chemin de recherche de modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer les modules MVola API
from mvola_api.client import MVolaClient
from mvola_api.auth import MVolaAuth
from mvola_api.constants import SANDBOX_URL, TEST_MSISDN_1, TEST_MSISDN_2

# Remplacer par vos credentials MVola
CONSUMER_KEY = "gwazRgSr3HIIgfzUchatsMbqwzUa"
CONSUMER_SECRET = "Ix1FR6_EHu1KN18G487VNcEWEgYa"
PARTNER_NAME = "Test Partner Company"
PARTNER_MSISDN = TEST_MSISDN_2  # 0343500004

def test_auth_with_auth_module():
    """
    Test de l'authentification en utilisant directement le module Auth
    """
    logger.info("=== TEST AUTHENTIFICATION AVEC MODULE AUTH ===")
    
    try:
        # Créer un objet Auth
        auth = MVolaAuth(CONSUMER_KEY, CONSUMER_SECRET, SANDBOX_URL)
        
        # Générer un token
        token_data = auth.generate_token()
        
        # Afficher les résultats
        logger.info(f"✅ Authentification réussie")
        logger.info(f"Access Token: {token_data['access_token'][:30]}...")
        logger.info(f"Scope: {token_data['scope']}")
        logger.info(f"Type de Token: {token_data['token_type']}")
        logger.info(f"Expire dans: {token_data['expires_in']} secondes")
        
        # Récupérer le token
        token = auth.get_access_token()
        logger.info(f"Token récupéré: {token[:30]}...")
        
        # Forcer le rafraîchissement du token
        logger.info("Forçage du rafraîchissement du token...")
        refreshed_token = auth.get_access_token(force_refresh=True)
        logger.info(f"Token rafraîchi: {refreshed_token[:30]}...")
        
        return token_data
    except Exception as e:
        logger.error(f"❌ Échec de l'authentification: {str(e)}")
        raise

def test_auth_with_client():
    """
    Test de l'authentification en utilisant le client MVola
    """
    logger.info("=== TEST AUTHENTIFICATION AVEC CLIENT MVOLA ===")
    
    try:
        # Créer un client MVola
        client = MVolaClient(
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            partner_name=PARTNER_NAME,
            partner_msisdn=PARTNER_MSISDN,
            sandbox=True
        )
        
        # Générer un token
        token_data = client.generate_token()
        
        # Afficher les résultats
        logger.info(f"✅ Authentification réussie via le client")
        logger.info(f"Access Token: {token_data['access_token'][:30]}...")
        logger.info(f"Expire dans: {token_data['expires_in']} secondes")
        
        # Forcer le rafraîchissement du token
        logger.info("Forçage du rafraîchissement du token...")
        refreshed_token_data = client.generate_token(force_refresh=True)
        logger.info(f"✅ Token rafraîchi avec succès")
        logger.info(f"Nouveau token: {refreshed_token_data['access_token'][:30]}...")
        
        return token_data
    except Exception as e:
        logger.error(f"❌ Échec de l'authentification via le client: {str(e)}")
        raise

def main():
    """
    Fonction principale qui exécute les exemples d'authentification
    """
    logger.info("=== DÉBUT DES TESTS D'AUTHENTIFICATION MVOLA ===")
    logger.info(f"Date et heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Environnement: Sandbox ({SANDBOX_URL})")
    logger.info(f"Consumer Key: {CONSUMER_KEY[:5]}...{CONSUMER_KEY[-5:]}")
    logger.info(f"Partner MSISDN: {PARTNER_MSISDN}")
    
    try:
        # Test avec le module Auth
        auth_token = test_auth_with_auth_module()
        
        print("\n" + "="*80 + "\n")
        
        # Test avec le client MVola
        client_token = test_auth_with_client()
        
        logger.info("=== TOUS LES TESTS D'AUTHENTIFICATION ONT RÉUSSI ===")
        
    except Exception as e:
        logger.error(f"Erreur lors des tests: {str(e)}")
        logger.error("=== ÉCHEC DES TESTS D'AUTHENTIFICATION ===")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 