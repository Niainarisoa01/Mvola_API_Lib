"""
MVola API Client
"""

import logging

from .auth import MVolaAuth
from .constants import PRODUCTION_URL, SANDBOX_URL
from .exceptions import MVolaError, MVolaValidationError
from .transaction import MVolaTransaction

# Configure logging
logger = logging.getLogger("api-mvola")


class MVolaClient:
    """
    Main client for MVola API
    """

    def __init__(
        self,
        consumer_key,
        consumer_secret,
        partner_name,
        partner_msisdn=None,
        sandbox=True,
        logger=None,
    ):
        """
        Initialize the MVola client

        Args:
            consumer_key (str): Consumer key from MVola Developer Portal
            consumer_secret (str): Consumer secret from MVola Developer Portal
            partner_name (str): Name of your application/merchant
            partner_msisdn (str, optional): Partner MSISDN for identifiers
            sandbox (bool, optional): Use sandbox environment (default: True)
            logger (logging.Logger, optional): Custom logger
        """
        if not consumer_key or not consumer_secret:
            raise MVolaValidationError("Consumer key and secret are required")

        if not partner_name:
            raise MVolaValidationError("Partner name is required")

        self.base_url = SANDBOX_URL if sandbox else PRODUCTION_URL
        self.sandbox = sandbox
        self.logger = logger or logging.getLogger("api-mvola")

        # Initialize auth module
        self.auth = MVolaAuth(consumer_key, consumer_secret, self.base_url)

        # Initialize transaction module
        self.transaction = MVolaTransaction(
            self.auth, self.base_url, partner_name, partner_msisdn
        )

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

    def initiate_payment(
        self,
        amount,
        debit_msisdn,
        credit_msisdn,
        description,
        currency="Ar",
        foreign_currency=None,
        foreign_amount=None,
        callback_url=None,
        user_language="FR",
    ):
        """
        Initiate a merchant payment

        Args:
            amount (str|float|int): Payment amount
            debit_msisdn (str): MSISDN of the payer
            credit_msisdn (str): MSISDN of the merchant
            description (str): Payment description
            currency (str, optional): Currency code, default "Ar"
            foreign_currency (str, optional): Foreign currency code
            foreign_amount (str|float|int, optional): Amount in foreign currency
            callback_url (str, optional): Callback URL for notifications
            user_language (str, optional): User language (FR or MG)

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
                str(foreign_amount) if foreign_amount is not None else None
            )

            result = self.transaction.initiate_merchant_payment(
                amount=amount_str,
                debit_msisdn=debit_msisdn,
                credit_msisdn=credit_msisdn,
                description=description,
                currency=currency,
                foreign_currency=foreign_currency,
                foreign_amount=foreign_amount_str,
                callback_url=callback_url,
                user_language=user_language,
            )

            self.logger.info(f"Payment initiated: {result.get('correlation_id', '')}")
            return result

        except MVolaError as e:
            self.logger.error(f"Payment initiation failed: {str(e)}")
            raise

    def get_transaction_status(self, server_correlation_id, user_language="FR"):
        """
        Get transaction status

        Args:
            server_correlation_id (str): Server correlation ID from payment initiation
            user_language (str, optional): User language (FR or MG)

        Returns:
            dict: Transaction status response

        Raises:
            MVolaTransactionError: If status request fails
        """
        try:
            self.logger.info(f"Getting status for transaction: {server_correlation_id}")
            result = self.transaction.get_transaction_status(
                server_correlation_id=server_correlation_id, user_language=user_language
            )
            self.logger.info(
                f"Got transaction status: {result.get('response', {}).get('status', 'unknown')}"
            )
            return result
        except MVolaError as e:
            self.logger.error(f"Failed to get transaction status: {str(e)}")
            raise

    def get_transaction_details(self, transaction_id, user_language="FR"):
        """
        Get transaction details

        Args:
            transaction_id (str): Transaction ID
            user_language (str, optional): User language (FR or MG)

        Returns:
            dict: Transaction details response

        Raises:
            MVolaTransactionError: If details request fails
        """
        try:
            self.logger.info(f"Getting details for transaction: {transaction_id}")
            result = self.transaction.get_transaction_details(
                transaction_id=transaction_id, user_language=user_language
            )
            self.logger.info(f"Got transaction details")
            return result
        except MVolaError as e:
            self.logger.error(f"Failed to get transaction details: {str(e)}")
            raise
