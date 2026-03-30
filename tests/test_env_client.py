#!/usr/bin/env python
"""
Test de la fonctionnalité d'utilisation des variables d'environnement
"""

import os
import sys
import unittest
from unittest.mock import patch
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvola_api import MVolaClient
from mvola_api.constants import TEST_MSISDN_1, TEST_MSISDN_2, SANDBOX_URL


class TestEnvClient(unittest.TestCase):
    """
    Tests pour la fonctionnalité d'utilisation des variables d'environnement.

    Note: Credentials are now stored as private attributes (_consumer_key, etc.)
    and can only be verified through the sandbox/partner_name/partner_msisdn properties.
    """

    @patch.dict(os.environ, {
        "MVOLA_CONSUMER_KEY": "test_key_env",
        "MVOLA_CONSUMER_SECRET": "test_secret_env",
        "MVOLA_PARTNER_NAME": "Test Partner From Env",
        "MVOLA_PARTNER_MSISDN": "0343500004",
        "MVOLA_SANDBOX": "True"
    })
    def test_from_env_method(self):
        """Test la méthode from_env()"""
        client = MVolaClient.from_env()

        # Verify non-sensitive properties
        self.assertEqual(client.partner_name, "Test Partner From Env")
        self.assertEqual(client.partner_msisdn, "0343500004")
        self.assertTrue(client.sandbox)

        # Verify credentials are NOT exposed publicly
        self.assertFalse(hasattr(client, "consumer_key"))
        self.assertFalse(hasattr(client, "consumer_secret"))

    @patch.dict(os.environ, {
        "MVOLA_CONSUMER_KEY": "test_key_env",
        "MVOLA_CONSUMER_SECRET": "test_secret_env",
        "MVOLA_PARTNER_NAME": "Test Partner From Env",
        "MVOLA_PARTNER_MSISDN": "0343500004",
        "MVOLA_SANDBOX": "True"
    })
    def test_env_override(self):
        """Test la priorité des paramètres directs sur les variables d'environnement"""
        # Create client with explicit parameters that must take priority
        client = MVolaClient(
            consumer_key="direct_key",
            consumer_secret="direct_secret",
            partner_name="Direct Partner",
            partner_msisdn="0343500003",
            sandbox=False
        )

        # Verify explicit parameters take priority
        self.assertEqual(client.partner_name, "Direct Partner")
        self.assertEqual(client.partner_msisdn, "0343500003")
        self.assertEqual(client.sandbox, False)

        # Verify env client uses env vars
        env_client = MVolaClient.from_env()
        self.assertEqual(env_client.partner_name, "Test Partner From Env")
        self.assertEqual(env_client.partner_msisdn, "0343500004")
        self.assertEqual(env_client.sandbox, True)

    @patch.dict(os.environ, {
        "MVOLA_CONSUMER_KEY": "test_key_env",
        "MVOLA_CONSUMER_SECRET": "test_secret_env",
        "MVOLA_PARTNER_NAME": "Test Partner From Env",
        "MVOLA_PARTNER_MSISDN": "0343500004",
        "MVOLA_SANDBOX": "False"
    })
    def test_partial_override(self):
        """Test l'utilisation mixte de paramètres et variables d'environnement"""
        client = MVolaClient(
            partner_name="Mixed Partner",
            sandbox=True
        )

        # Verify mixed behavior
        self.assertEqual(client.partner_name, "Mixed Partner")  # Explicit
        self.assertEqual(client.partner_msisdn, "0343500004")  # From env
        self.assertEqual(client.sandbox, True)  # Explicit

    @patch.dict(os.environ, {
        "MVOLA_CONSUMER_KEY": "test_key",
        "MVOLA_CONSUMER_SECRET": "test_secret",
        "MVOLA_PARTNER_NAME": "Test",
        "MVOLA_SANDBOX": "invalid_value"
    })
    def test_sandbox_parsing(self):
        """Test l'interprétation des valeurs de sandbox"""
        # Invalid value → should be interpreted as False
        client1 = MVolaClient.from_env()
        self.assertEqual(client1.sandbox, False)

        # True values
        for value in ["true", "True", "TRUE", "1", "yes", "t"]:
            os.environ["MVOLA_SANDBOX"] = value
            client = MVolaClient.from_env()
            self.assertEqual(client.sandbox, True, f"Sandbox should be True for '{value}'")

        # False values
        for value in ["false", "False", "FALSE", "0", "no", "f"]:
            os.environ["MVOLA_SANDBOX"] = value
            client = MVolaClient.from_env()
            self.assertEqual(client.sandbox, False, f"Sandbox should be False for '{value}'")


if __name__ == "__main__":
    unittest.main()