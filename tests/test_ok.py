"""
MVola API Library - Guide de démarrage rapide

Ce script démontre comment utiliser la bibliothèque MVola API pour:
1. Initialiser un client MVola
2. Générer un token d'authentification
3. Initier un paiement
4. Suivre l'état d'une transaction
5. Obtenir les détails d'une transaction

Pour plus d'informations, consultez la documentation complète: 
https://github.com/Niainarisoa01/Mvlola_API_Lib
"""

from mvola_api import MVolaClient
import time

# ======================================================
# 1. INITIALISATION DU CLIENT
# ======================================================
# Remplacez ces valeurs par vos propres credentials
# Pour le mode production, définissez sandbox=False
client = MVolaClient(
    consumer_key="your_consumer_key",  # Obtenu du portail développeur MVola
    consumer_secret="your_consumer_secret",  # Obtenu du portail développeur MVola
    partner_name="CNTEMAD",  # Nom de votre application/entreprise
    partner_msisdn="0343500004",  # Numéro marchand (IMPORTANT: en environnement sandbox, utilisez uniquement 0343500003 ou 0343500004)
    sandbox=True  # Utilise l'environnement de test (pre-api.mvola.mg)
)

# ======================================================
# 2. AUTHENTIFICATION - GÉNÉRATION DE TOKEN
# ======================================================
# Un token est valide pendant 1 heure
# La bibliothèque gère automatiquement le renouvellement
token_data = client.generate_token()
print(f"Token généré: {token_data['access_token'][:10]}...")

# ======================================================
# 3. INITIER UN PAIEMENT
# ======================================================
# REMARQUE IMPORTANTE: Dans l'environnement sandbox MVola:
# - Le débiteur (debit_msisdn) doit être le 0343500004
# - Le créditeur (credit_msisdn) doit être le 0343500003
# C'est l'inverse de ce qu'on pourrait attendre, mais c'est une spécificité de l'environnement de test
result = client.initiate_payment(
    amount=1000,  # Montant en Ariary (minimum 100)
    debit_msisdn="0343500004",  # Numéro du débiteur (celui qui paie)
    credit_msisdn="0343500003",  # Numéro du créditeur (celui qui reçoit)
    description="Test Transaction",  # Description de la transaction (max 50 caractères)
    callback_url="https://example.com/callback"  # URL où MVola enverra des notifications (optionnel)
)

# ======================================================
# 4. SUIVI DE LA TRANSACTION
# ======================================================
# L'ID de corrélation est nécessaire pour suivre l'état de la transaction
server_correlation_id = result['response']['serverCorrelationId']
print(f"Transaction initiée avec l'ID de corrélation: {server_correlation_id}")

# 4.1 Vérification initiale du statut
print("\n=== Test de get_transaction_status (statut initial) ===")
status_result = client.get_transaction_status(server_correlation_id)
print(f"Statut HTTP: {status_result['status_code']}")
print(f"Statut initial de la transaction: {status_result['response']['status']}")
print(f"Détails complets: {status_result['response']}")

# 4.2 Suivi automatique du statut - boucle de vérification
# La transaction peut prendre du temps pour être traitée
print("\n=== Boucle de vérification du statut ===")
max_attempts = 70  # Maximum d'essais
waiting_time = 1   # Secondes entre chaque vérification
current_attempt = 1
transaction_status = status_result['response']['status']

# La boucle continue jusqu'à ce que le statut change ou le nombre max de tentatives soit atteint
while transaction_status == "pending" and current_attempt <= max_attempts:
    print(f"Tentative {current_attempt}/{max_attempts} - Statut actuel: {transaction_status}")
    print(f"Attente de {waiting_time} secondes avant nouvelle vérification...")
    time.sleep(waiting_time)
    
    # Vérification périodique du statut
    status_result = client.get_transaction_status(server_correlation_id)
    transaction_status = status_result['response']['status']
    current_attempt += 1

print(f"\nStatut final après {current_attempt-1} vérifications: {transaction_status}")

# 4.3 Interprétation du statut final
# Les statuts possibles sont: pending, completed, failed
if transaction_status == "pending":
    print("En attente d'approbation")
    print("La transaction est toujours en attente après toutes les tentatives de vérification.")
    print("Vous devrez peut-être l'approuver manuellement dans le portail développeur MVola.")
elif transaction_status == "completed":
    print("La transaction est Réussie")
    print("Le paiement a été approuvé et traité avec succès.")
elif transaction_status == "failed":
    print("Échec de transaction")
    print("Le paiement a été rejeté ou a échoué pendant le traitement.")
else:
    print(f"Statut final: {transaction_status}")
    print("Statut non reconnu ou en cours de traitement.")

# ======================================================
# 5. DÉTAILS DE LA TRANSACTION
# ======================================================
# Obtient des informations complètes sur la transaction
print("\n=== Test de get_transaction_details ===")

# L'objectReference est l'ID unique de la transaction, nécessaire pour obtenir les détails
transaction_id = status_result['response'].get('objectReference')

if transaction_id and transaction_id.strip():
    print(f"ID de transaction obtenu: {transaction_id}")
    
    try:
        # Récupération des détails complets
        details_result = client.get_transaction_details(transaction_id)
        print(f"Statut HTTP: {details_result['status_code']}")
        print(f"Détails de la transaction: {details_result['response']}")
    except Exception as e:
        print(f"Erreur lors de la récupération des détails: {str(e)}")
else:
    print("L'objectReference est vide ou non disponible")
    
    # Explication selon le statut actuel
    if transaction_status == "pending":
        print("La transaction est encore en attente d'approbation")
        print("\nNote: Dans l'environnement sandbox, les transactions restent souvent en état 'pending'")
        print("Pour les tests, vous devriez approuver manuellement la transaction dans le portail développeur MVola")
    elif transaction_status == "completed":
        print("La transaction est complétée mais l'ID de référence n'est pas disponible")
        print("C'est inhabituel - vérifiez dans le portail développeur MVola")
    elif transaction_status == "failed":
        print("La transaction a échoué. Aucun ID de référence n'est généré pour les transactions échouées")
        print("Vérifiez les détails de l'échec dans le portail développeur MVola")
    else:
        print(f"La transaction a un statut inhabituel: {transaction_status}")
        print("Vérifiez le portail développeur MVola pour plus de détails")

# ======================================================
# REMARQUES SUPPLÉMENTAIRES
# ======================================================
# 1. En environnement sandbox, vous devrez approuver manuellement les transactions
#    dans le portail développeur MVola pour qu'elles passent à l'état "completed"
# 
# 2. Cette bibliothèque gère automatiquement:
#    - Le renouvellement du token d'authentification
#    - Le formatage des requêtes selon les attentes de l'API MVola
#    - La gestion des erreurs et exceptions
#
# 3. Pour l'environnement de production:
#    - Utilisez sandbox=False lors de l'initialisation du client
#    - Utilisez vos véritables numéros de téléphone MVola
#    - Assurez-vous d'avoir les autorisations nécessaires 