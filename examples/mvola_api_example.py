#!/usr/bin/env python
"""
Exemple complet d'utilisation de la bibliothèque MVola API selon la documentation 2023-2024
"""
import os
import time
import logging
import uuid
from dotenv import load_dotenv

from mvola_api import MVolaClient, MVolaError

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement (à partir du fichier .env)
load_dotenv()

# Configuration des informations d'identification
CONSUMER_KEY = os.getenv("MVOLA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MVOLA_CONSUMER_SECRET")
PARTNER_NAME = os.getenv("MVOLA_PARTNER_NAME")
PARTNER_MSISDN = os.getenv("MVOLA_PARTNER_MSISDN")

# Vérifier que les informations d'identification sont présentes
if not CONSUMER_KEY or not CONSUMER_SECRET or not PARTNER_NAME or not PARTNER_MSISDN:
    logger.error("Informations d'identification manquantes. Assurez-vous de créer un fichier .env avec MVOLA_CONSUMER_KEY, MVOLA_CONSUMER_SECRET, MVOLA_PARTNER_NAME et MVOLA_PARTNER_MSISDN.")
    exit(1)

def main():
    """Fonction principale qui démontre les principales fonctionnalités de l'API MVola"""
    logger.info("Démarrage de l'exemple d'intégration MVola API")
    
    # 1. Initialisation du client MVola
    logger.info("1. Initialisation du client MVola")
    client = MVolaClient(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        partner_name=PARTNER_NAME,
        partner_msisdn=PARTNER_MSISDN,
        sandbox=True  # Utiliser l'environnement sandbox
    )
    
    # 2. Générer un token d'authentification
    logger.info("2. Génération du token d'authentification")
    try:
        token_data = client.generate_token()
        logger.info(f"Token généré avec succès : {token_data['access_token'][:10]}... (expire dans {token_data['expires_in']} secondes)")
    except MVolaError as e:
        logger.error(f"Erreur lors de la génération du token : {e}")
        return

    # 3. Initialiser une transaction
    logger.info("3. Initialisation d'une transaction de paiement")
    
    # Numéros de test pour l'environnement sandbox
    # IMPORTANT: Dans l'environnement sandbox MVola, utilisez ces numéros spécifiques
    debit_msisdn = "0343500003"  # Numéro du débiteur (celui qui paie)
    credit_msisdn = "0343500004"  # Numéro du créditeur (celui qui reçoit)
    
    # Générer une référence de transaction unique
    transaction_ref = f"MVOLA-TEST-{uuid.uuid4().hex[:8]}"
    logger.info(f"Référence de transaction : {transaction_ref}")
    
    # Montant et description
    amount = 1000  # 1000 Ar
    description = "Test de paiement MVola API"
    
    try:
        # Initier le paiement
        payment_result = client.initiate_payment(
            amount=amount,
            debit_msisdn=debit_msisdn,
            credit_msisdn=credit_msisdn,
            description=description,
            currency="Ar",
            callback_url="https://example.com/callback",  # URL où MVola enverra des notifications
            requesting_organisation_transaction_reference=transaction_ref,
            foreign_currency="USD",  # Optionnel - devise étrangère
            foreign_amount=0.25,     # Optionnel - montant en devise étrangère
            user_language="FR"       # FR ou MG
        )
        
        # Analyser le résultat
        if payment_result['success']:
            server_correlation_id = payment_result['response']['serverCorrelationId']
            status = payment_result['response']['status']
            notification_method = payment_result['response'].get('notificationMethod', 'N/A')
            
            logger.info(f"Paiement initié avec succès")
            logger.info(f"Server Correlation ID : {server_correlation_id}")
            logger.info(f"Statut initial : {status}")
            logger.info(f"Méthode de notification : {notification_method}")
        else:
            logger.error("Échec de l'initialisation du paiement")
            return
    except MVolaError as e:
        logger.error(f"Erreur lors de l'initialisation du paiement : {e}")
        return

    # 4. Vérifier le statut de la transaction
    logger.info("4. Vérification du statut de la transaction")
    
    # Boucle de vérification du statut
    max_attempts = 5
    attempt = 1
    transaction_id = None
    
    while attempt <= max_attempts:
        logger.info(f"Tentative {attempt}/{max_attempts} de vérification du statut")
        
        try:
            status_result = client.get_transaction_status(server_correlation_id)
            
            if status_result['success']:
                status = status_result['response']['status']
                logger.info(f"Statut : {status}")
                
                # Vérifier si la transaction est terminée
                if status == "completed":
                    transaction_id = status_result['response'].get('objectReference')
                    logger.info(f"Transaction complétée ! ID de transaction : {transaction_id}")
                    break
                elif status == "failed":
                    logger.error("La transaction a échoué")
                    break
                else:
                    logger.info("La transaction est toujours en attente")
                    
                    # Dans l'environnement sandbox, les transactions peuvent rester en état "pending"
                    if attempt == max_attempts:
                        logger.warning("Nombre maximum de tentatives atteint. La transaction est toujours en attente.")
                        logger.warning("Note: Dans l'environnement sandbox, les transactions restent souvent en état 'pending'")
                        logger.warning("Pour les tests, vous devriez approuver manuellement la transaction dans le portail développeur MVola")
            else:
                logger.error("Échec de la vérification du statut")
                break
                
        except MVolaError as e:
            logger.error(f"Erreur lors de la vérification du statut : {e}")
            break
            
        # Attendre avant la prochaine tentative
        if attempt < max_attempts:
            wait_time = 3  # 3 secondes
            logger.info(f"Attente de {wait_time} secondes avant la prochaine vérification...")
            time.sleep(wait_time)
            
        attempt += 1
    
    # 5. Obtenir les détails de la transaction si elle est complétée
    if transaction_id:
        logger.info("5. Obtention des détails de la transaction")
        
        try:
            details_result = client.get_transaction_details(transaction_id)
            
            if details_result['success']:
                details = details_result['response']
                logger.info(f"Détails de la transaction :")
                logger.info(f"  - Montant : {details.get('amount')} {details.get('currency')}")
                logger.info(f"  - Référence : {details.get('transactionReference')}")
                logger.info(f"  - Statut : {details.get('transactionStatus')}")
                logger.info(f"  - Date : {details.get('createDate')}")
                
                # Afficher les informations des parties
                debit_party = next((party for party in details.get('debitParty', []) if party.get('key') == 'msisdn'), {})
                credit_party = next((party for party in details.get('creditParty', []) if party.get('key') == 'msisdn'), {})
                
                logger.info(f"  - Débiteur : {debit_party.get('value', 'N/A')}")
                logger.info(f"  - Créditeur : {credit_party.get('value', 'N/A')}")
                
                # Afficher les frais si disponibles
                fee = next((f for f in details.get('fee', [])), {})
                logger.info(f"  - Frais : {fee.get('feeAmount', 'N/A')}")
                
                # Afficher les métadonnées
                for metadata in details.get('metadata', []):
                    logger.info(f"  - {metadata.get('key')}: {metadata.get('value')}")
            else:
                logger.error("Échec de l'obtention des détails de la transaction")
        except MVolaError as e:
            logger.error(f"Erreur lors de l'obtention des détails de la transaction : {e}")
    
    logger.info("Fin de l'exemple d'intégration MVola API")

if __name__ == "__main__":
    main() 