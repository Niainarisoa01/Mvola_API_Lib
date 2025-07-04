#!/usr/bin/env python
"""
Test complet de l'API MVola

Ce script teste de manière exhaustive l'intégration avec l'API MVola:
1. Authentification et génération de token
2. Initiation de paiement marchand
3. Vérification du statut de transaction
4. Récupération des détails de transaction

Basé sur la documentation officielle de l'API MVola v1.0
"""

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock
import json
import base64
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvola_api import MVolaClient
from mvola_api.auth import MVolaAuth
from mvola_api.transaction import MVolaTransaction
from mvola_api.exceptions import MVolaError, MVolaAuthError, MVolaTransactionError
from mvola_api.constants import SANDBOX_URL, PRODUCTION_URL, TEST_MSISDN_1, TEST_MSISDN_2

# Charger les variables d'environnement
load_dotenv()


class TestMVolaComplete(unittest.TestCase):
    """
    Suite de tests complète pour l'API MVola
    """

    def setUp(self):
        """Configuration des tests"""
        # Récupérer les identifiants depuis les variables d'environnement
        self.consumer_key = os.environ.get("MVOLA_CONSUMER_KEY")
        self.consumer_secret = os.environ.get("MVOLA_CONSUMER_SECRET")
        self.partner_name = os.environ.get("MVOLA_PARTNER_NAME", "Test Partner Company")
        self.partner_msisdn = os.environ.get("MVOLA_PARTNER_MSISDN", TEST_MSISDN_2)  # 0343500004 dans l'environnement sandbox
        
        # Vérifier que les identifiants sont disponibles
        if not self.consumer_key or not self.consumer_secret:
            self.skipTest("Les identifiants MVola n'ont pas été trouvés dans les variables d'environnement. "
                         "Assurez-vous que le fichier .env est configuré correctement.")
        
        # Création du client pour les tests
        self.client = MVolaClient(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            partner_name=self.partner_name,
            partner_msisdn=self.partner_msisdn,
            sandbox=True
        )
        
        # Montant de test
        self.test_amount = 1000
        
        # Numéros MVola sandbox pour les tests
        self.debit_msisdn = TEST_MSISDN_2  # 0343500004
        self.credit_msisdn = TEST_MSISDN_1  # 0343500003
        
        # Description du paiement test (max 50 caractères)
        self.test_description = "Test Transaction Payment via API"
        
        # URL de callback (optionnelle)
        self.callback_url = "https://example.com/webhook/mvola-callback"
        
        # Références d'organisation et de transaction
        self.requesting_org_transaction_ref = f"ref-{str(uuid.uuid4())[:8]}"
        self.original_transaction_ref = "MVOLA_123"  # Utilisé le format du test fonctionnel
        
        # Corrélation ID pour le suivi de requête
        self.correlation_id = "123"  # Utiliser un ID fixe comme dans l'exemple fonctionnel
        
        # Langage utilisateur
        self.user_language = "MG"  # Utiliser MG comme dans l'exemple fonctionnel

    def test_0_client_from_env(self):
        """Test la création du client à partir des variables d'environnement"""
        print("\n===== TEST 0: CRÉATION DU CLIENT DEPUIS ENV =====")
        
        # Créer un client avec la méthode from_env
        env_client = MVolaClient.from_env()
        
        # Vérifications
        self.assertEqual(env_client.consumer_key, self.consumer_key)
        self.assertEqual(env_client.consumer_secret, self.consumer_secret)
        self.assertEqual(env_client.partner_name, self.partner_name)
        self.assertEqual(env_client.partner_msisdn, self.partner_msisdn)
        
        print(f"✅ Test de création du client depuis variables d'environnement réussi")

    def test_1_authentication(self):
        """Test l'authentification et génération de token"""
        print("\n===== TEST 1: AUTHENTIFICATION =====")
        
        # Appel de la méthode de génération de token
        token_data = self.client.generate_token()
        
        # Vérifications
        self.assertEqual(token_data["token_type"], "Bearer")
        self.assertEqual(token_data["scope"], "EXT_INT_MVOLA_SCOPE")
        self.assertTrue("access_token" in token_data)
        self.assertTrue("expires_in" in token_data)
        
        print(f"✅ Test d'authentification réussi: Token obtenu")
        print(f"Token type: {token_data['token_type']}")
        print(f"Scope: {token_data['scope']}")
        print(f"Expiration: {token_data['expires_in']} secondes")
        print(f"Access Token: {token_data['access_token'][:20]}...")

    def test_2_initiate_payment(self):
        """Test l'initiation d'un paiement marchand"""
        print("\n===== TEST 2: INITIATION DE PAIEMENT =====")
        
        # Appel de la méthode d'initiation de paiement
        result = self.client.initiate_payment(
            amount=self.test_amount,
            debit_msisdn=self.debit_msisdn,
            credit_msisdn=self.credit_msisdn,
            description=self.test_description,
            callback_url=self.callback_url,
            requesting_organisation_transaction_reference=self.requesting_org_transaction_ref,
            original_transaction_reference=self.original_transaction_ref,
            correlation_id=self.correlation_id,
            user_language=self.user_language
        )
        
        # Vérifications de la structure de la réponse (les codes peuvent varier)
        self.assertTrue("success" in result)
        self.assertTrue("status_code" in result)
        self.assertTrue("response" in result)
        
        print(f"✅ Test d'initiation de paiement terminé")
        print(f"Status Code: {result['status_code']}")
        if "status" in result["response"]:
            print(f"Status: {result['response']['status']}")
        if "serverCorrelationId" in result["response"]:
            print(f"Server Correlation ID: {result['response']['serverCorrelationId']}")
            # Sauvegarde du serverCorrelationId pour les tests suivants
            self.server_correlation_id = result["response"]["serverCorrelationId"]
            # Sauvegarde du serverCorrelationId dans un fichier pour d'autres tests
            with open("tests/server_correlation_id.txt", "w") as f:
                f.write(self.server_correlation_id)

    def test_3_transaction_status(self):
        """Test la vérification du statut d'une transaction"""
        print("\n===== TEST 3: VÉRIFICATION DU STATUT DE TRANSACTION =====")
        
        # Récupération du serverCorrelationId du test précédent
        try:
            with open("tests/server_correlation_id.txt", "r") as f:
                self.server_correlation_id = f.read().strip()
        except FileNotFoundError:
            self.skipTest("Server correlation ID non disponible. Exécutez d'abord le test d'initiation de paiement.")
        
        # Affichage du serverCorrelationId utilisé
        print(f"Vérification du statut avec serverCorrelationId: {self.server_correlation_id}")
        
        # Appel de la méthode de vérification de statut
        status_result = self.client.get_transaction_status(
            self.server_correlation_id,
            user_language=self.user_language
        )
        
        # Vérifications
        self.assertTrue("status_code" in status_result)
        self.assertTrue("response" in status_result)
        
        print(f"✅ Test de vérification de statut terminé")
        print(f"Status Code: {status_result['status_code']}")
        
        if "status" in status_result["response"]:
            print(f"Status: {status_result['response']['status']}")
        
        if "serverCorrelationId" in status_result["response"]:
            print(f"Server Correlation ID: {status_result['response']['serverCorrelationId']}")
        
        # Si la transaction est complétée et possède un objectReference, sauvegardez-le
        if (status_result.get("response", {}).get("status") == "completed" and 
            "objectReference" in status_result["response"] and 
            status_result["response"]["objectReference"]):
            
            self.transaction_id = status_result["response"]["objectReference"]
            print(f"Transaction complétée avec ID: {self.transaction_id}")
            
            # Sauvegarde du transaction_id dans un fichier pour le test suivant
            with open("tests/transaction_id.txt", "w") as f:
                f.write(self.transaction_id)

    def test_4_transaction_details(self):
        """Test la récupération des détails d'une transaction"""
        print("\n===== TEST 4: DÉTAILS DE TRANSACTION =====")
        
        # Récupération du transaction_id du test précédent (si disponible)
        try:
            with open("tests/transaction_id.txt", "r") as f:
                self.transaction_id = f.read().strip()
        except FileNotFoundError:
            self.skipTest("Transaction ID non disponible. La transaction doit être complétée pour obtenir les détails.")
        
        # Affichage du transaction_id utilisé
        print(f"Récupération des détails avec transaction_id: {self.transaction_id}")
        
        # Appel de la méthode de récupération des détails
        details_result = self.client.get_transaction_details(
            self.transaction_id,
            user_language=self.user_language
        )
        
        # Vérifications
        self.assertTrue("status_code" in details_result)
        self.assertTrue("response" in details_result)
        
        print(f"✅ Test de récupération des détails terminé")
        print(f"Status Code: {details_result['status_code']}")
        
        response = details_result.get("response", {})
        print(f"Transaction ID: {response.get('transactionReference', 'N/A')}")
        print(f"Montant: {response.get('amount', 'N/A')} {response.get('currency', 'Ar')}")
        print(f"Statut: {response.get('transactionStatus', 'N/A')}")
        if 'fee' in response and response['fee']:
            print(f"Frais: {response['fee'][0].get('feeAmount', 'N/A')} Ar")
        print(f"Date de création: {response.get('createDate', 'N/A')}")


class TestErrorHandling(unittest.TestCase):
    """
    Tests pour vérifier la gestion des erreurs
    """
    
    def setUp(self):
        """Configuration des tests"""
        # Récupérer les identifiants depuis les variables d'environnement
        self.consumer_key = os.environ.get("MVOLA_CONSUMER_KEY")
        self.consumer_secret = os.environ.get("MVOLA_CONSUMER_SECRET")
        self.partner_name = os.environ.get("MVOLA_PARTNER_NAME", "Test Partner Company")
        self.partner_msisdn = os.environ.get("MVOLA_PARTNER_MSISDN", TEST_MSISDN_2)
        
        # Vérifier que les identifiants sont disponibles
        if not self.consumer_key or not self.consumer_secret:
            self.skipTest("Les identifiants MVola n'ont pas été trouvés dans les variables d'environnement. "
                         "Assurez-vous que le fichier .env est configuré correctement.")
        
        self.client = MVolaClient(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            partner_name=self.partner_name,
            partner_msisdn=self.partner_msisdn,
            sandbox=True
        )

    @patch('mvola_api.auth.requests.post')
    def test_auth_error_handling(self, mock_post):
        """Test la gestion des erreurs d'authentification"""
        print("\n===== TEST 5: GESTION DES ERREURS D'AUTHENTIFICATION =====")
        
        # Configurer le mock pour simuler une erreur d'authentification
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "fault": {
                "code": 900901,
                "message": "Invalid Credentials",
                "description": "Invalid Credentials. Make sure you have given the correct access token"
            }
        }
        # Utiliser un objet requests.exceptions.HTTPError pour simuler l'erreur
        from requests.exceptions import HTTPError
        mock_http_error = HTTPError("401 Client Error")
        mock_http_error.response = mock_response
        mock_response.raise_for_status.side_effect = mock_http_error
        mock_post.return_value = mock_response
        
        # Vérifier que l'exception est levée
        with self.assertRaises(MVolaAuthError):
            # Utilisation d'identifiants incorrects pour tester l'erreur
            auth = MVolaAuth("invalid_key", "invalid_secret", SANDBOX_URL)
            auth.generate_token()
        
        print("✅ Test de gestion d'erreur d'authentification réussi")

    def test_validation_error_handling(self):
        """Test la validation des paramètres d'entrée"""
        print("\n===== TEST 7: VALIDATION DES PARAMÈTRES =====")
        
        # Test avec un montant négatif
        with self.assertRaises(MVolaError):
            self.client.initiate_payment(
                amount=-100,
                debit_msisdn=TEST_MSISDN_2,
                credit_msisdn=TEST_MSISDN_1,
                description="Test de validation"
            )
        
        # Test avec une description trop longue (> 50 caractères)
        with self.assertRaises(MVolaError):
            self.client.initiate_payment(
                amount=1000,
                debit_msisdn=TEST_MSISDN_2,
                credit_msisdn=TEST_MSISDN_1,
                description="Cette description est beaucoup trop longue et dépasse les 50 caractères autorisés par l'API MVola"
            )
        
        # Test avec des caractères spéciaux non autorisés
        with self.assertRaises(MVolaError):
            self.client.initiate_payment(
                amount=1000,
                debit_msisdn=TEST_MSISDN_2,
                credit_msisdn=TEST_MSISDN_1,
                description="Test avec caractères spéciaux @#$%^&*"
            )
        
        # Test avec un format de numéro incorrect
        with self.assertRaises(MVolaError):
            self.client.initiate_payment(
                amount=1000,
                debit_msisdn="123456",  # Format incorrect
                credit_msisdn=TEST_MSISDN_1,
                description="Test de validation"
            )
        
        print("✅ Test de validation des paramètres réussi")


if __name__ == "__main__":
    print("\n========================================")
    print("TESTS COMPLETS DE L'API MVOLA")
    print("========================================\n")
    unittest.main() 