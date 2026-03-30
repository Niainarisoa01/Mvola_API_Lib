#!/usr/bin/env python
"""
Test de transaction réél sur l'environnement Sandbox MVola.

Ce script effectue les requêtes en temps réel avec vos credentials
pour valider l'intégrité de la librairie MVola API.

ATTENTION: Ce fichier contient des identifiants et ne doit
pas être commité sur un dépôt Git public.
"""

import logging
import os
import sys
import time
import json

# Ensure we import the local package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvola_api import MVolaClient, MVolaError
from mvola_api.constants import TEST_MSISDN_1, TEST_MSISDN_2

# Configuration du logging pour y voir clair dans le terminal
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

# Vos credentials Sandbox
CONSUMER_KEY = "vmLAxEyX4MRbfbnqZOifGxUIOxoa"
CONSUMER_SECRET = "GW029VAsHRgb6ubNCMuyEb0SwIsa"


def run_live_test():
    """Exécute un cycle complet de transaction sur l'API."""
    try:
        logging.info("1. Initialisation du client MVolaClient...")
        client = MVolaClient(
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            partner_name="Mvola Test App",
            sandbox=True  # Force l'utilisation des URLs sandbox (devapi.mvola.mg)
        )

        logging.info("2. Génération du Token d'accès...")
        # Client générera le token automatiquement, mais nous testons explicitement
        token_data = client.generate_token()
        logging.info(f"✔ Token généré! Expire dans: {token_data.get('expires_in')}s")

        logging.info("3. Initiation du paiement marchand...")
        logging.info(f"   Débit: {TEST_MSISDN_1} | Crédit: {TEST_MSISDN_2} | Montant: 1000 Ar")
        
        # Déclenchement du paiement 
        payment_result = client.initiate_payment(
            amount=1000,
            debit_msisdn=TEST_MSISDN_1,   # "0343500003" par défaut sandbox
            credit_msisdn=TEST_MSISDN_2,  # "0343500004" par défaut sandbox
            description="Test de paiement sandbox API v2",
        )
        
        logging.info("✔ Réponse API (Paiement Initié):")
        print(json.dumps(payment_result, indent=2))

        # Récupération de l'identifiant pour interroger le statut
        server_correlation_id = payment_result.get("response", {}).get("serverCorrelationId")
        
        if server_correlation_id:
            logging.info(f"4. Vérification du statut de la transaction ({server_correlation_id})...")
            # Une pause s'impose pour laisser MVola traiter la transaction
            logging.info("   Attente de 3 secondes...")
            time.sleep(3)
            
            status_result = client.get_transaction_status(server_correlation_id)
            logging.info("✔ Réponse API (Statut):")
            print(json.dumps(status_result, indent=2))

            # S'il y a un objectReference, on peut tester les détails finaux
            object_ref = status_result.get("response", {}).get("objectReference")
            if object_ref:
                logging.info(f"5. Récupération des détails de {object_ref}...")
                details_result = client.get_transaction_details(object_ref)
                logging.info("✔ Réponse API (Détails):")
                print(json.dumps(details_result, indent=2))
            else:
                logging.info("   Aucun 'objectReference' trouvé (le statut est peut-être en attente).")

        logging.info("✨ TEST SANDBOX VALIDÉ AVEC SUCCÈS ✨")

    except MVolaError as e:
        logging.error(f"❌ Erreur MVola API (Code HTTP: {e.code})")
        logging.error(f"   Message: {e.message}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                logging.error(f"   Détails bruts: {e.response.text}")
            except Exception:
                pass
    except Exception as e:
        logging.error(f"❌ Erreur inattendue: {str(e)}")


if __name__ == "__main__":
    run_live_test()
