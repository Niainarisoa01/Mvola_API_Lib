"""
MVola API Client

Main entry point for the MVola payment integration library.
All credentials are stored privately and never exposed publicly.
"""

import logging
import os
from typing import Any, Dict, Optional, Union

from dotenv import load_dotenv

from .auth import MVolaAuth
from .constants import (
    ALLOWED_BASE_URLS,
    DEFAULT_CURRENCY,
    PRODUCTION_URL,
    SANDBOX_URL,
    TEST_MSISDN_2,
)
from .exceptions import MVolaError, MVolaValidationError
from .transaction import MVolaTransaction
from .utils import mask_msisdn

# Configure logging
logger = logging.getLogger("mvola_api")

# Note: load_dotenv() is called in the constructor, not at module level,
# to avoid unintended side effects when importing the module.


class MVolaClient:
    """
    Main client for MVola API.

    Credentials are stored as private attributes and never
    exposed through properties, repr, str, or logging.

    Usage:
        # From environment variables
        client = MVolaClient.from_env()

        # Direct initialization
        client = MVolaClient(
            consumer_key="...",
            consumer_secret="...",
            partner_name="My App",
        )
    """

    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        partner_name: Optional[str] = None,
        partner_msisdn: Optional[str] = None,
        sandbox: Optional[bool] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize the MVola client.

        Args:
            consumer_key: Consumer key from MVola Developer Portal.
                If None, loads from env var MVOLA_CONSUMER_KEY
            consumer_secret: Consumer secret from MVola Developer Portal.
                If None, loads from env var MVOLA_CONSUMER_SECRET
            partner_name: Name of your application/merchant.
                If None, loads from env var MVOLA_PARTNER_NAME
            partner_msisdn: Partner MSISDN for identifiers.
                If None, loads from env var MVOLA_PARTNER_MSISDN
            sandbox: Use sandbox environment.
                If None, loads from env var MVOLA_SANDBOX
            logger: Custom logger instance

        Raises:
            MVolaValidationError: If required credentials are missing
        """
        # Load environment variables from .env (only in constructor, not at import time)
        # override=False ensures existing env vars are not overwritten
        load_dotenv(override=False)

        # Load credentials — store as PRIVATE attributes
        self._consumer_key = consumer_key or os.environ.get("MVOLA_CONSUMER_KEY")
        self._consumer_secret = consumer_secret or os.environ.get("MVOLA_CONSUMER_SECRET")
        self._partner_name = partner_name or os.environ.get("MVOLA_PARTNER_NAME")
        self._partner_msisdn = partner_msisdn or os.environ.get("MVOLA_PARTNER_MSISDN")

        # Determine sandbox mode from environment if not provided
        if sandbox is None:
            sandbox_env = os.environ.get("MVOLA_SANDBOX", "True")
            self._sandbox = sandbox_env.lower() in ("true", "1", "t", "yes")
        else:
            self._sandbox = sandbox

        # Validate required credentials
        if not self._consumer_key or not self._consumer_secret:
            raise MVolaValidationError(
                "Consumer key and secret are required. "
                "Set them in .env file or pass them directly."
            )

        if not self._partner_name:
            raise MVolaValidationError(
                "Partner name is required. Set it in .env file or pass it directly."
            )

        self._base_url = SANDBOX_URL if self._sandbox else PRODUCTION_URL
        self._logger = logger or logging.getLogger("mvola_api")

        # Use test MSISDN if in sandbox mode and no MSISDN provided
        if self._sandbox and not self._partner_msisdn:
            self._partner_msisdn = TEST_MSISDN_2  # Sandbox default: 0343500004

        # Initialize auth module
        self._auth = MVolaAuth(self._consumer_key, self._consumer_secret, self._base_url)

        # Initialize transaction module
        self._transaction = MVolaTransaction(
            self._auth, self._base_url, self._partner_name, self._partner_msisdn
        )

    def __repr__(self) -> str:
        """Secure repr — never leaks any credential information."""
        return (
            f"MVolaClient(sandbox={self._sandbox}, "
            f"partner_name='{self._partner_name}', "
            f"has_credentials=True)"
        )

    def __str__(self) -> str:
        """Secure str representation."""
        return f"MVolaClient(sandbox={self._sandbox})"

    def __del__(self) -> None:
        """Securely clear credentials from memory on deletion."""
        try:
            self._consumer_key = None
            self._consumer_secret = None
        except Exception:
            pass

    # --- Read-only properties (only non-sensitive data) ---

    @property
    def sandbox(self) -> bool:
        """Whether the client is in sandbox mode."""
        return self._sandbox

    @property
    def partner_name(self) -> str:
        """Partner name (non-sensitive)."""
        return self._partner_name

    @property
    def partner_msisdn(self) -> Optional[str]:
        """Partner MSISDN (non-sensitive)."""
        return self._partner_msisdn

    @property
    def base_url(self) -> str:
        """Base URL being used."""
        return self._base_url

    @classmethod
    def from_env(cls):
        """
        Create a client instance using environment variables.

        Returns:
            MVolaClient: Client instance configured from environment variables
        """
        return cls()

    def generate_token(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Generate an access token.

        Args:
            force_refresh: Force token refresh

        Returns:
            Token response data

        Raises:
            MVolaAuthError: If token generation fails
        """
        try:
            self._logger.info("Generating MVola API token")
            token_data = self._auth.generate_token(force_refresh)
            self._logger.info("Token generated successfully")
            return token_data
        except MVolaError as e:
            self._logger.error("Token generation failed: %s", str(e))
            raise

    def get_access_token(self) -> str:
        """
        Get the current access token, generating a new one if needed.

        Returns:
            Access token
        """
        return self._auth.get_access_token()

    def initiate_merchant_payment(
        self,
        amount: Union[str, int, float],
        debit_msisdn: str,
        credit_msisdn: str,
        description: str,
        currency: str = DEFAULT_CURRENCY,
        foreign_currency: str = "USD",
        foreign_amount: Union[str, int, float] = "1",
        correlation_id: Optional[str] = None,
        user_language: str = "MG",
        callback_url: Optional[str] = None,
        requesting_organisation_transaction_reference: Optional[str] = None,
        original_transaction_reference: str = "MVOLA_123",
        cell_id_a: Optional[str] = None,
        geo_location_a: Optional[str] = None,
        cell_id_b: Optional[str] = None,
        geo_location_b: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiate a merchant payment (alias for initiate_payment).

        Args:
            amount: Payment amount (must be a positive integer)
            debit_msisdn: MSISDN of the payer
            credit_msisdn: MSISDN of the merchant
            description: Payment description (max 50 chars)
            currency: Currency code, default "Ar"
            foreign_currency: Foreign currency code, default "USD"
            foreign_amount: Amount in foreign currency, default "1"
            correlation_id: Custom correlation ID
            user_language: User language, default "MG"
            callback_url: Callback URL for notifications
            requesting_organisation_transaction_reference: Your transaction ID
            original_transaction_reference: Reference number, default "MVOLA_123"
            cell_id_a: Cell ID A
            geo_location_a: Geo Location A
            cell_id_b: Cell ID B
            geo_location_b: Geo Location B

        Returns:
            Transaction response dict
        """
        return self.initiate_payment(
            amount=amount,
            debit_msisdn=debit_msisdn,
            credit_msisdn=credit_msisdn,
            description=description,
            currency=currency,
            foreign_currency=foreign_currency,
            foreign_amount=foreign_amount,
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

    def initiate_payment(
        self,
        amount: Union[str, int, float],
        debit_msisdn: str,
        credit_msisdn: str,
        description: str,
        currency: str = DEFAULT_CURRENCY,
        foreign_currency: str = "USD",
        foreign_amount: Union[str, int, float] = "1",
        correlation_id: Optional[str] = None,
        user_language: str = "MG",
        callback_url: Optional[str] = None,
        requesting_organisation_transaction_reference: Optional[str] = None,
        original_transaction_reference: str = "MVOLA_123",
        cell_id_a: Optional[str] = None,
        geo_location_a: Optional[str] = None,
        cell_id_b: Optional[str] = None,
        geo_location_b: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiate a merchant payment.

        Args:
            amount: Payment amount (must be a positive integer)
            debit_msisdn: MSISDN of the payer
            credit_msisdn: MSISDN of the merchant
            description: Payment description (max 50 chars)
            currency: Currency code, default "Ar"
            foreign_currency: Foreign currency code, default "USD"
            foreign_amount: Amount in foreign currency, default "1"
            correlation_id: Custom correlation ID
            user_language: User language, default "MG"
            callback_url: Callback URL for notifications
            requesting_organisation_transaction_reference: Your transaction ID
            original_transaction_reference: Reference number, default "MVOLA_123"
            cell_id_a: Cell ID A
            geo_location_a: Geo Location A
            cell_id_b: Cell ID B
            geo_location_b: Geo Location B

        Returns:
            Transaction response dict

        Raises:
            MVolaTransactionError: If transaction fails
            MVolaValidationError: If parameters are invalid
        """
        try:
            self._logger.info(
                "Initiating MVola payment from %s to %s",
                mask_msisdn(debit_msisdn),
                mask_msisdn(credit_msisdn),
            )

            # Convert amount to string if needed
            amount_str = str(amount)
            foreign_amount_str = (
                str(foreign_amount) if foreign_amount is not None else "1"
            )

            result = self._transaction.initiate_merchant_payment(
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

            self._logger.info(
                "Payment initiated: %s", result.get("correlation_id", "")
            )
            return result

        except MVolaError as e:
            self._logger.error("Payment initiation failed: %s", str(e))
            raise

    def get_transaction_status(
        self,
        server_correlation_id: str,
        correlation_id: Optional[str] = None,
        user_language: str = "MG",
    ) -> Dict[str, Any]:
        """
        Get transaction status.

        Args:
            server_correlation_id: Server correlation ID from payment initiation
            correlation_id: Custom correlation ID for request
            user_language: User language, default "MG"

        Returns:
            Transaction status response

        Raises:
            MVolaTransactionError: If status request fails
        """
        try:
            self._logger.info(
                "Getting status for transaction: %s", server_correlation_id
            )
            result = self._transaction.get_transaction_status(
                server_correlation_id=server_correlation_id,
                correlation_id=correlation_id,
                user_language=user_language,
            )
            self._logger.info(
                "Got transaction status: %s",
                result.get("response", {}).get("status", "unknown"),
            )
            return result
        except MVolaError as e:
            self._logger.error("Failed to get transaction status: %s", str(e))
            raise

    def get_transaction_details(
        self,
        transaction_id: str,
        correlation_id: Optional[str] = None,
        user_language: str = "MG",
    ) -> Dict[str, Any]:
        """
        Get transaction details.

        Args:
            transaction_id: Transaction ID
            correlation_id: Custom correlation ID for request
            user_language: User language, default "MG"

        Returns:
            Transaction details response

        Raises:
            MVolaTransactionError: If details request fails
        """
        try:
            self._logger.info(
                "Getting details for transaction: %s", transaction_id
            )
            result = self._transaction.get_transaction_details(
                transaction_id=transaction_id,
                correlation_id=correlation_id,
                user_language=user_language,
            )
            self._logger.info("Got transaction details")
            return result
        except MVolaError as e:
            self._logger.error("Failed to get transaction details: %s", str(e))
            raise
