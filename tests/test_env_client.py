#!/usr/bin/env python
"""
Test de la fonctionnalité d'utilisation des variables d'environnement
"""

import os
import sys
import unittest
from unittest.mock import patch
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvola_api import MVolaClient
from mvola_api.constants import TEST_MSISDN_1, TEST_MSISDN_2, SANDBOX_URL

# Charger les variables d'environnement
load_dotenv()


class TestEnvClient(unittest.TestCase):
    """
    Tests pour la fonctionnalité d'utilisation des variables d'environnement
    """

    def setUp(self):
        """Configuration des tests"""
        # Sauvegarder les variables d'environnement actuelles
        self.original_env = {
            "MVOLA_CONSUMER_KEY": os.environ.get("MVOLA_CONSUMER_KEY"),
            "MVOLA_CONSUMER_SECRET": os.environ.get("MVOLA_CONSUMER_SECRET"),
            "MVOLA_PARTNER_NAME": os.environ.get("MVOLA_PARTNER_NAME"),
            "MVOLA_PARTNER_MSISDN": os.environ.get("MVOLA_PARTNER_MSISDN"),
            "MVOLA_SANDBOX": os.environ.get("MVOLA_SANDBOX")
        }

    def tearDown(self):
        """Nettoyage après les tests"""
        # Restaurer les variables d'environnement originales
        for key, value in self.original_env.items():
            if value:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_from_env_method(self):
        """Test la méthode from_env()"""
        print("\n===== TEST: CRÉATION DU CLIENT AVEC FROM_ENV() =====")
        
        # Créer un client avec la méthode from_env
        client = MVolaClient.from_env()
        
        # Vérifications
        self.assertEqual(client.consumer_key, os.environ.get("MVOLA_CONSUMER_KEY"))
        self.assertEqual(client.consumer_secret, os.environ.get("MVOLA_CONSUMER_SECRET"))
        self.assertEqual(client.partner_name, os.environ.get("MVOLA_PARTNER_NAME"))
        self.assertEqual(client.partner_msisdn, os.environ.get("MVOLA_PARTNER_MSISDN"))
        
        # Vérifier que le sandbox est correctement interprété depuis l'environnement
        sandbox_env = os.environ.get("MVOLA_SANDBOX", "True")
        expected_sandbox = sandbox_env.lower() in ("true", "1", "t", "yes")
        self.assertEqual(client.sandbox, expected_sandbox)
        
        print(f"✅ Test de création du client depuis variables d'environnement réussi")

    @patch.dict(os.environ, {
        "MVOLA_CONSUMER_KEY": "test_key_env",
        "MVOLA_CONSUMER_SECRET": "test_secret_env",
        "MVOLA_PARTNER_NAME": "Test Partner From Env",
        "MVOLA_PARTNER_MSISDN": "0343500004",
        "MVOLA_SANDBOX": "True"
    })
    def test_env_override(self):
        """Test la priorité des paramètres directs sur les variables d'environnement"""
        print("\n===== TEST: PRIORITÉ DES PARAMÈTRES =====")
        
        # Créer un client avec des paramètres explicites qui doivent avoir priorité
        client = MVolaClient(
            consumer_key="direct_key",
            consumer_secret="direct_secret",
            partner_name="Direct Partner",
            partner_msisdn="0343500003",
            sandbox=False
        )
        
        # Vérifier que les paramètres directs ont priorité
        self.assertEqual(client.consumer_key, "direct_key")
        self.assertEqual(client.consumer_secret, "direct_secret")
        self.assertEqual(client.partner_name, "Direct Partner")
        self.assertEqual(client.partner_msisdn, "0343500003")
        self.assertEqual(client.sandbox, False)
        
        # Vérifier que le client créé depuis l'environnement utilise les variables d'environnement
        env_client = MVolaClient.from_env()
        self.assertEqual(env_client.consumer_key, "test_key_env")
        self.assertEqual(env_client.consumer_secret, "test_secret_env")
        self.assertEqual(env_client.partner_name, "Test Partner From Env")
        self.assertEqual(env_client.partner_msisdn, "0343500004")
        self.assertEqual(env_client.sandbox, True)
        
        print(f"✅ Test de priorité des paramètres réussi")

    @patch.dict(os.environ, {
        "MVOLA_CONSUMER_KEY": "test_key_env",
        "MVOLA_CONSUMER_SECRET": "test_secret_env",
        "MVOLA_PARTNER_NAME": "Test Partner From Env",
        "MVOLA_PARTNER_MSISDN": "0343500004",
        "MVOLA_SANDBOX": "False"
    })
    def test_partial_override(self):
        """Test l'utilisation mixte de paramètres et variables d'environnement"""
        print("\n===== TEST: UTILISATION MIXTE =====")
        
        # Créer un client avec seulement certains paramètres explicites
        client = MVolaClient(
            partner_name="Mixed Partner",
            sandbox=True
        )
        
        # Vérifier que les paramètres explicites ont priorité
        self.assertEqual(client.consumer_key, "test_key_env")  # De l'environnement
        self.assertEqual(client.consumer_secret, "test_secret_env")  # De l'environnement
        self.assertEqual(client.partner_name, "Mixed Partner")  # Explicite
        self.assertEqual(client.partner_msisdn, "0343500004")  # De l'environnement
        self.assertEqual(client.sandbox, True)  # Explicite
        
        print(f"✅ Test d'utilisation mixte réussi")

    @patch.dict(os.environ, {
        "MVOLA_SANDBOX": "invalid_value"
    })
    def test_sandbox_parsing(self):
        """Test l'interprétation des valeurs de sandbox"""
        print("\n===== TEST: INTERPRÉTATION DE SANDBOX =====")
        
        # Tester différentes valeurs pour le paramètre sandbox
        
        # 1. Valeur invalide dans l'environnement - doit être interprétée comme False
        client1 = MVolaClient.from_env()
        self.assertEqual(client1.sandbox, False)
        
        # 2. Valeurs True explicites
        for value in ["true", "True", "TRUE", "1", "yes", "t"]:
            os.environ["MVOLA_SANDBOX"] = value
            client = MVolaClient.from_env()
            self.assertEqual(client.sandbox, True, f"Sandbox devrait être True pour '{value}'")
        
        # 3. Valeurs False explicites
        for value in ["false", "False", "FALSE", "0", "no", "f"]:
            os.environ["MVOLA_SANDBOX"] = value
            client = MVolaClient.from_env()
            self.assertEqual(client.sandbox, False, f"Sandbox devrait être False pour '{value}'")
        
        print(f"✅ Test d'interprétation de sandbox réussi")


if __name__ == "__main__":
    print("\n========================================")
    print("TESTS D'UTILISATION DES VARIABLES D'ENVIRONNEMENT")
    print("========================================\n")
    unittest.main() 