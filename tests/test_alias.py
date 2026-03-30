import pytest
from unittest.mock import MagicMock
from mvola_api import MVolaClient

def test_initiate_merchant_payment_alias():
    """Test that initiate_merchant_payment is an alias for initiate_payment."""
    # Mock dependencies to avoid real API calls
    mock_auth = MagicMock()
    mock_transaction = MagicMock()
    
    # We initialize the client with dummy credentials
    client = MVolaClient(
        consumer_key="test_key",
        consumer_secret="test_secret",
        partner_name="test_partner",
        sandbox=True
    )
    
    # Inject our mock transaction
    client._transaction = mock_transaction
    
    # Mock the return value
    expected_result = {"success": True, "status_code": 202, "response": {"status": "pending"}}
    mock_transaction.initiate_merchant_payment.return_value = expected_result
    
    # Call the alias
    result = client.initiate_merchant_payment(
        amount="1000",
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Test alias"
    )
    
    # Verify the results
    assert result == expected_result
    mock_transaction.initiate_merchant_payment.assert_called_once()
    
    # Verify arguments were passed correctly to the internal transaction module
    args, kwargs = mock_transaction.initiate_merchant_payment.call_args
    assert kwargs["amount"] == "1000"
    assert kwargs["debit_msisdn"] == "0343500003"
    assert kwargs["credit_msisdn"] == "0343500004"
    assert kwargs["description"] == "Test alias"
