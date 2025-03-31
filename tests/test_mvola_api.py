#!/usr/bin/env python
"""
Test suite for MVola API library
"""
import os
import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
import requests

# Import modules to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mvola_api import MVolaClient, MVolaAuth, MVolaTransaction
from mvola_api import MVolaError, MVolaAuthError, MVolaTransactionError


class TestMVolaAuth(unittest.TestCase):
    """Test the authentication module"""
    
    def setUp(self):
        """Set up test environment"""
        self.consumer_key = "test_key"
        self.consumer_secret = "test_secret"
        self.base_url = "https://example.com"
        self.auth = MVolaAuth(self.consumer_key, self.consumer_secret, self.base_url)
    
    def test_encode_credentials(self):
        """Test encoding of credentials for Basic Auth"""
        encoded = self.auth._encode_credentials()
        self.assertIsInstance(encoded, str)
        self.assertTrue(len(encoded) > 0)
    
    @patch('requests.post')
    def test_generate_token_success(self, mock_post):
        """Test successful token generation"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "scope": "EXT_INT_MVOLA_SCOPE",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response
        
        # Call method
        token_data = self.auth.generate_token()
        
        # Verify
        self.assertEqual(token_data["access_token"], "test_token")
        self.assertEqual(token_data["token_type"], "Bearer")
        self.assertEqual(token_data["expires_in"], 3600)
        
        # Verify request
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/x-www-form-urlencoded")
        self.assertTrue(kwargs["headers"]["Authorization"].startswith("Basic "))
    
    @patch('requests.post')
    def test_generate_token_failure(self, mock_post):
        """Test token generation failure"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Client Error")
        mock_response.json.return_value = {
            "error": "invalid_client",
            "error_description": "Invalid client credentials"
        }
        mock_post.return_value = mock_response
        
        # Call method and verify exception
        with self.assertRaises(MVolaAuthError):
            self.auth.generate_token()


class TestMVolaTransaction(unittest.TestCase):
    """Test the transaction module"""
    
    def setUp(self):
        """Set up test environment"""
        self.auth = MagicMock()
        self.auth.get_access_token.return_value = "test_token"
        
        self.base_url = "https://example.com"
        self.partner_name = "Test Partner"
        self.partner_msisdn = "0340000000"
        
        self.transaction = MVolaTransaction(
            self.auth, 
            self.base_url, 
            self.partner_name, 
            self.partner_msisdn
        )
    
    def test_generate_correlation_id(self):
        """Test generation of correlation ID"""
        correlation_id = self.transaction._generate_correlation_id()
        self.assertIsInstance(correlation_id, str)
        self.assertTrue(len(correlation_id) > 0)
    
    def test_get_current_datetime(self):
        """Test datetime formatting"""
        dt = self.transaction._get_current_datetime()
        self.assertIsInstance(dt, str)
        self.assertTrue("T" in dt)
        self.assertTrue("Z" in dt)
    
    def test_validate_transaction_params_success(self):
        """Test successful parameter validation"""
        # This should not raise an exception
        self.transaction._validate_transaction_params(
            amount="1000", 
            debit_msisdn="0340000001", 
            credit_msisdn="0340000002", 
            description="Test transaction"
        )
    
    def test_validate_transaction_params_invalid_amount(self):
        """Test validation with invalid amount"""
        with self.assertRaises(MVolaError):
            self.transaction._validate_transaction_params(
                amount="-100",  # Negative amount
                debit_msisdn="0340000001", 
                credit_msisdn="0340000002", 
                description="Test transaction"
            )
    
    def test_validate_transaction_params_invalid_description(self):
        """Test validation with invalid description"""
        with self.assertRaises(MVolaError):
            self.transaction._validate_transaction_params(
                amount="1000",
                debit_msisdn="0340000001", 
                credit_msisdn="0340000002", 
                description="Test transaction with special characters: #$%^"  # Invalid characters
            )
    
    @patch('requests.post')
    def test_initiate_merchant_payment_success(self, mock_post):
        """Test successful payment initiation"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "pending",
            "serverCorrelationId": "test-correlation-id",
            "notificationMethod": "callback"
        }
        mock_post.return_value = mock_response
        
        # Call method
        result = self.transaction.initiate_merchant_payment(
            amount="1000",
            debit_msisdn="0340000001",
            credit_msisdn="0340000002",
            description="Test transaction"
        )
        
        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["response"]["status"], "pending")
        self.assertIn("correlation_id", result)
        
        # Verify request
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_token")
        self.assertEqual(kwargs["json"]["amount"], "1000")
        self.assertEqual(kwargs["json"]["descriptionText"], "Test transaction")


class TestMVolaClient(unittest.TestCase):
    """Test the main client class"""
    
    @patch('mvola_api.client.MVolaAuth')
    @patch('mvola_api.client.MVolaTransaction')
    def setUp(self, mock_transaction, mock_auth):
        """Set up test environment"""
        # Mock auth
        self.mock_auth_instance = MagicMock()
        mock_auth.return_value = self.mock_auth_instance
        
        # Mock transaction
        self.mock_transaction_instance = MagicMock()
        mock_transaction.return_value = self.mock_transaction_instance
        
        # Create client
        self.client = MVolaClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            partner_name="Test Partner",
            partner_msisdn="0340000000",
            sandbox=True
        )
    
    def test_generate_token(self):
        """Test token generation via client"""
        # Mock response
        self.mock_auth_instance.generate_token.return_value = {
            "access_token": "test_token",
            "scope": "EXT_INT_MVOLA_SCOPE",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        # Call method
        token_data = self.client.generate_token()
        
        # Verify
        self.assertEqual(token_data["access_token"], "test_token")
        self.assertEqual(token_data["expires_in"], 3600)
        self.mock_auth_instance.generate_token.assert_called_once()
    
    def test_initiate_payment(self):
        """Test payment initiation via client"""
        # Mock response
        self.mock_transaction_instance.initiate_merchant_payment.return_value = {
            "success": True,
            "status_code": 200,
            "response": {
                "status": "pending",
                "serverCorrelationId": "test-correlation-id",
                "notificationMethod": "callback"
            },
            "correlation_id": "test-correlation-id"
        }
        
        # Call method
        result = self.client.initiate_payment(
            amount=1000,
            debit_msisdn="0340000001",
            credit_msisdn="0340000002",
            description="Test transaction"
        )
        
        # Verify
        self.assertTrue(result["success"])
        self.assertEqual(result["response"]["status"], "pending")
        
        # Verify transaction method was called with correct arguments
        args, kwargs = self.mock_transaction_instance.initiate_merchant_payment.call_args
        self.assertEqual(kwargs["amount"], "1000")  # Should be converted to string
        self.assertEqual(kwargs["debit_msisdn"], "0340000001")
        self.assertEqual(kwargs["credit_msisdn"], "0340000002")
        self.assertEqual(kwargs["description"], "Test transaction")


if __name__ == "__main__":
    unittest.main() 