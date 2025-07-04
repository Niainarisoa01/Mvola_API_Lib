"""
MVola API Client
"""

import logging
import os
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

from .auth import MVolaAuth
from .constants import PRODUCTION_URL, SANDBOX_URL, TEST_MSISDN_1, TEST_MSISDN_2, DEFAULT_CURRENCY, DEFAULT_LANGUAGE
from .exceptions import MVolaError, MVolaValidationError
from .transaction import MVolaTransaction

# Configure logging
logger = logging.getLogger("mvola_api")

# Load environment variables from .env file
load_dotenv()


class MVolaClient:
    """
    Main client for MVola API
    """

    def __init__(
        self,
        consumer_key=None,
        consumer_secret=None,
        partner_name=None,
        partner_msisdn=None,
        sandbox=None,
        logger=None,
    ):
        """
        Initialize the MVola client

        Args:
            consumer_key (str, optional): Consumer key from MVola Developer Portal. If None, will load from env var MVOLA_CONSUMER_KEY
            consumer_secret (str, optional): Consumer secret from MVola Developer Portal. If None, will load from env var MVOLA_CONSUMER_SECRET
            partner_name (str, optional): Name of your application/merchant. If None, will load from env var MVOLA_PARTNER_NAME
            partner_msisdn (str, optional): Partner MSISDN for identifiers. If None, will load from env var MVOLA_PARTNER_MSISDN
            sandbox (bool, optional): Use sandbox environment. If None, will load from env var MVOLA_SANDBOX
            logger (logging.Logger, optional): Custom logger
        """
        # Load credentials from environment variables if not provided
        self.consumer_key = consumer_key or os.environ.get("MVOLA_CONSUMER_KEY")
        self.consumer_secret = consumer_secret or os.environ.get("MVOLA_CONSUMER_SECRET")
        self.partner_name = partner_name or os.environ.get("MVOLA_PARTNER_NAME")
        self.partner_msisdn = partner_msisdn or os.environ.get("MVOLA_PARTNER_MSISDN")
        
        # Determine sandbox mode from environment if not provided
        if sandbox is None:
            sandbox_env = os.environ.get("MVOLA_SANDBOX", "True")
            self.sandbox = sandbox_env.lower() in ("true", "1", "t", "yes")
        else:
            self.sandbox = sandbox

        if not self.consumer_key or not self.consumer_secret:
            raise MVolaValidationError("Consumer key and secret are required. Set them in .env file or pass them directly.")

        if not self.partner_name:
            raise MVolaValidationError("Partner name is required. Set it in .env file or pass it directly.")

        self.base_url = SANDBOX_URL if self.sandbox else PRODUCTION_URL
        self.logger = logger or logging.getLogger("mvola_api")

        # Use test MSISDN if in sandbox mode and no MSISDN provided
        if self.sandbox and not self.partner_msisdn:
            self.partner_msisdn = TEST_MSISDN_2  # Sandbox default: 0343500004

        # Initialize auth module
        self.auth = MVolaAuth(self.consumer_key, self.consumer_secret, self.base_url)

        # Initialize transaction module
        self.transaction = MVolaTransaction(
            self.auth, self.base_url, self.partner_name, self.partner_msisdn
        )

    @classmethod
    def from_env(cls):
        """
        Create a client instance using environment variables
        
        Returns:
            MVolaClient: Client instance configured from environment variables
        """
        return cls()

    def generate_token(self, force_refresh=False):
        """
        Generate an access token

        Args:
            force_refresh (bool, optional): Force token refresh

        Returns:
            dict: Token response data

        Raises:
            MVolaAuthError: If token generation fails
        """
        try:
            self.logger.info("Generating MVola API token")
            token_data = self.auth.generate_token(force_refresh)
            self.logger.info("Token generated successfully")
            return token_data
        except MVolaError as e:
            self.logger.error(f"Token generation failed: {str(e)}")
            raise

    def get_access_token(self):
        """
        Get the current access token, generating a new one if needed

        Returns:
            str: Access token
        """
        return self.auth.get_access_token()

    def initiate_payment(
        self,
        amount,
        debit_msisdn,
        credit_msisdn,
        description,
        currency=DEFAULT_CURRENCY,
        foreign_currency="USD",  # Default to USD per working example
        foreign_amount="1",      # Default to 1 per working example
        correlation_id=None,
        user_language="MG",      # Default to MG per working example
        callback_url=None,
        requesting_organisation_transaction_reference=None,
        original_transaction_reference="MVOLA_123",  # Default value from working example
        cell_id_a=None,
        geo_location_a=None,
        cell_id_b=None,
        geo_location_b=None,
    ):
        """
        Initiate a merchant payment
        
        Note: Based on testing, the MG language code and the specific headers/payload format
        in this implementation have been shown to work reliably with the MVola API.

        Args:
            amount (str|float|int): Payment amount
            debit_msisdn (str): MSISDN of the payer
            credit_msisdn (str): MSISDN of the merchant
            description (str): Payment description
            currency (str, optional): Currency code, default "Ar"
            foreign_currency (str, optional): Foreign currency code, default "USD"
            foreign_amount (str|float|int, optional): Amount in foreign currency, default "1"
            correlation_id (str, optional): Custom correlation ID
            user_language (str, optional): User language, use "MG" for best results (default)
            callback_url (str, optional): Callback URL for notifications - strongly recommended
            requesting_organisation_transaction_reference (str, optional): Transaction ID on client side
            original_transaction_reference (str, optional): Reference number, default "MVOLA_123"
            cell_id_a (str, optional): Cell ID A from MVola API documentation
            geo_location_a (str, optional): Geo Location A from MVola API documentation
            cell_id_b (str, optional): Cell ID B from MVola API documentation
            geo_location_b (str, optional): Geo Location B from MVola API documentation

        Returns:
            dict: Transaction response

        Raises:
            MVolaTransactionError: If transaction fails
            MVolaValidationError: If parameters are invalid
        """
        try:
            self.logger.info(
                f"Initiating MVola payment of {amount} from {debit_msisdn} to {credit_msisdn}"
            )

            # Convert amount to string if needed
            amount_str = str(amount)
            foreign_amount_str = (
                str(foreign_amount) if foreign_amount is not None else "1"
            )

            result = self.transaction.initiate_merchant_payment(
                amount=amount_str,
                debit_msisdn=debit_msisdn,
                credit_msisdn=credit_msisdn,
                description=description,
                currency=currency,
                foreign_currency=foreign_currency,
                foreign_amount=foreign_amount_str,
                correlation_id=correlation_id,
                user_language=user_language,
                callback_url=callback_url,
                requesting_organisation_transaction_reference=requesting_organisation_transaction_reference,
                original_transaction_reference=original_transaction_reference,
                cell_id_a=cell_id_a,
                geo_location_a=geo_location_a,
                cell_id_b=cell_id_b,
                geo_location_b=geo_location_b,
            )

            self.logger.info(f"Payment initiated: {result.get('correlation_id', '')}")
            return result

        except MVolaError as e:
            self.logger.error(f"Payment initiation failed: {str(e)}")
            raise

    def get_transaction_status(
        self,
        server_correlation_id,
        correlation_id=None,
        user_language="MG",  # Updated to MG for consistency
    ):
        """
        Get transaction status

        Args:
            server_correlation_id (str): Server correlation ID from payment initiation
            correlation_id (str, optional): Custom correlation ID for request
            user_language (str, optional): User language, use "MG" for best results (default)

        Returns:
            dict: Transaction status response

        Raises:
            MVolaTransactionError: If status request fails
        """
        try:
            self.logger.info(f"Getting status for transaction: {server_correlation_id}")
            result = self.transaction.get_transaction_status(
                server_correlation_id=server_correlation_id,
                correlation_id=correlation_id,
                user_language=user_language
            )
            self.logger.info(
                f"Got transaction status: {result.get('response', {}).get('status', 'unknown')}"
            )
            return result
        except MVolaError as e:
            self.logger.error(f"Failed to get transaction status: {str(e)}")
            raise

    def get_transaction_details(
        self,
        transaction_id,
        correlation_id=None,
        user_language="MG",  # Updated to MG for consistency
    ):
        """
        Get transaction details

        Args:
            transaction_id (str): Transaction ID
            correlation_id (str, optional): Custom correlation ID for request
            user_language (str, optional): User language, use "MG" for best results (default)

        Returns:
            dict: Transaction details response

        Raises:
            MVolaTransactionError: If details request fails
        """
        try:
            self.logger.info(f"Getting details for transaction: {transaction_id}")
            result = self.transaction.get_transaction_details(
                transaction_id=transaction_id,
                correlation_id=correlation_id,
                user_language=user_language
            )
            self.logger.info(f"Got transaction details")
            return result
        except MVolaError as e:
            self.logger.error(f"Failed to get transaction details: {str(e)}")
            raise
