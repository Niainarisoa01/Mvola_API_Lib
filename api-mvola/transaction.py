"""
MVola API Transaction Module
"""

import datetime
import uuid
from urllib.parse import urljoin

import requests

from .constants import (
    API_VERSION,
    DEFAULT_CURRENCY,
    DEFAULT_LANGUAGE,
    MERCHANT_PAY_ENDPOINT,
    TRANSACTION_DETAILS_ENDPOINT,
    TRANSACTION_STATUS_ENDPOINT,
)
from .exceptions import MVolaTransactionError, MVolaValidationError


class MVolaTransaction:
    """
    Class for managing MVola transactions
    """

    def __init__(self, auth, base_url, partner_name, partner_msisdn=None):
        """
        Initialize the transaction module

        Args:
            auth (MVolaAuth): Authentication object
            base_url (str): Base URL for the API
            partner_name (str): Name of your application
            partner_msisdn (str, optional): Partner MSISDN used for UserAccountIdentifier
        """
        self.auth = auth
        self.base_url = base_url
        self.partner_name = partner_name
        self.partner_msisdn = partner_msisdn

    def _generate_correlation_id(self):
        """
        Generate a unique correlation ID

        Returns:
            str: UUID string
        """
        return str(uuid.uuid4())

    def _get_current_datetime(self):
        """
        Get current datetime in ISO 8601 format

        Returns:
            str: Formatted datetime
        """
        # Use timezone-aware UTC datetime instead of deprecated utcnow()
        try:
            # For Python 3.11+ where datetime.UTC is available
            return (
                datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[
                    :-3
                ]
                + "Z"
            )
        except AttributeError:
            # Fallback for older Python versions
            return (
                datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%S.%f"
                )[:-3]
                + "Z"
            )

    def _validate_transaction_params(
        self, amount, debit_msisdn, credit_msisdn, description
    ):
        """
        Validate transaction parameters

        Args:
            amount (str): Transaction amount
            debit_msisdn (str): MSISDN of the payer
            credit_msisdn (str): MSISDN of the merchant
            description (str): Transaction description

        Raises:
            MVolaValidationError: If validation fails
        """
        errors = []

        # Check amount
        try:
            float_amount = float(amount)
            if float_amount <= 0:
                errors.append("Amount must be positive")
        except ValueError:
            errors.append("Amount must be a valid number")

        # Check MSISDNs
        if not debit_msisdn or not isinstance(debit_msisdn, str):
            errors.append("Debit MSISDN is required")

        if not credit_msisdn or not isinstance(credit_msisdn, str):
            errors.append("Credit MSISDN is required")

        # Check description
        if not description:
            errors.append("Description is required")
        elif len(description) > 40:
            errors.append("Description must be less than 40 characters")
        elif any(c in description for c in "#$%^&*+={}[]|\\:;\"'<>?/"):
            errors.append("Description contains invalid characters")

        if errors:
            raise MVolaValidationError(message="; ".join(errors))

    def _get_headers(
        self, correlation_id=None, user_language=DEFAULT_LANGUAGE, callback_url=None
    ):
        """
        Get standard headers for API requests

        Args:
            correlation_id (str, optional): Correlation ID
            user_language (str, optional): User language (FR or MG)
            callback_url (str, optional): Callback URL for notifications

        Returns:
            dict: Headers for API request
        """
        access_token = self.auth.get_access_token()

        if not correlation_id:
            correlation_id = self._generate_correlation_id()

        if not self.partner_msisdn:
            raise MVolaValidationError(
                message="Partner MSISDN is required for transaction requests"
            )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Version": API_VERSION,
            "X-CorrelationID": correlation_id,
            "UserLanguage": user_language,
            "UserAccountIdentifier": f"msisdn;{self.partner_msisdn}",
            "partnerName": self.partner_name,
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

        if callback_url:
            headers["X-Callback-URL"] = callback_url

        return headers

    def initiate_merchant_payment(
        self,
        amount,
        debit_msisdn,
        credit_msisdn,
        description,
        currency=DEFAULT_CURRENCY,
        foreign_currency=None,
        foreign_amount=None,
        correlation_id=None,
        user_language=DEFAULT_LANGUAGE,
        callback_url=None,
    ):
        """
        Initiate a merchant payment transaction

        Args:
            amount (str): Transaction amount
            debit_msisdn (str): MSISDN of the payer
            credit_msisdn (str): MSISDN of the merchant
            description (str): Transaction description
            currency (str, optional): Currency code, default is "Ar"
            foreign_currency (str, optional): Foreign currency code for conversion
            foreign_amount (str, optional): Amount in foreign currency
            correlation_id (str, optional): Custom correlation ID
            user_language (str, optional): User language (FR or MG)
            callback_url (str, optional): Callback URL for notifications

        Returns:
            dict: Transaction response

        Raises:
            MVolaTransactionError: If transaction initiation fails
            MVolaValidationError: If parameters are invalid
        """
        # Validate parameters
        self._validate_transaction_params(
            amount, debit_msisdn, credit_msisdn, description
        )

        # Create correlation ID if not provided
        if not correlation_id:
            correlation_id = self._generate_correlation_id()

        # Set up headers
        headers = self._get_headers(
            correlation_id=correlation_id,
            user_language=user_language,
            callback_url=callback_url,
        )

        # Set up request body
        request_date = self._get_current_datetime()

        payload = {
            "amount": str(amount),
            "currency": currency,
            "descriptionText": description,
            "requestDate": request_date,
            "debitParty": [{"key": "msisdn", "value": debit_msisdn}],
            "creditParty": [{"key": "msisdn", "value": credit_msisdn}],
            "metadata": [{"key": "partnerName", "value": self.partner_name}],
        }

        # Add foreign currency information if provided
        if foreign_currency and foreign_amount:
            payload["metadata"].extend(
                [
                    {"key": "fc", "value": foreign_currency},
                    {"key": "amountFc", "value": str(foreign_amount)},
                ]
            )

        # Send request
        url = urljoin(self.base_url, MERCHANT_PAY_ENDPOINT)

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json(),
                "correlation_id": correlation_id,  # Return correlation_id for tracking
            }

        except requests.exceptions.RequestException as e:
            error_message = "Failed to initiate transaction"

            # Try to extract error details if available
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    if "fault" in error_data:
                        error_message = (
                            f"{error_message}: {error_data['fault'].get('message', '')}"
                        )
                    elif "ErrorDescription" in error_data:
                        error_message = (
                            f"{error_message}: {error_data['ErrorDescription']}"
                        )
                except (ValueError, KeyError):
                    pass

            raise MVolaTransactionError(
                message=error_message,
                code=(
                    e.response.status_code
                    if hasattr(e, "response") and e.response
                    else None
                ),
                response=e.response if hasattr(e, "response") else None,
            ) from e

    def get_transaction_status(
        self, server_correlation_id, correlation_id=None, user_language=DEFAULT_LANGUAGE
    ):
        """
        Get the status of a transaction

        Args:
            server_correlation_id (str): Server correlation ID from initiate_transaction response
            correlation_id (str, optional): Custom correlation ID for request
            user_language (str, optional): User language (FR or MG)

        Returns:
            dict: Transaction status response

        Raises:
            MVolaTransactionError: If status request fails
        """
        # Create correlation ID if not provided
        if not correlation_id:
            correlation_id = self._generate_correlation_id()

        # Set up headers
        headers = self._get_headers(
            correlation_id=correlation_id, user_language=user_language
        )

        # Send request
        url = urljoin(
            self.base_url, f"{TRANSACTION_STATUS_ENDPOINT}{server_correlation_id}"
        )

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json(),
            }

        except requests.exceptions.RequestException as e:
            error_message = "Failed to get transaction status"

            # Try to extract error details if available
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    if "fault" in error_data:
                        error_message = (
                            f"{error_message}: {error_data['fault'].get('message', '')}"
                        )
                    elif "ErrorDescription" in error_data:
                        error_message = (
                            f"{error_message}: {error_data['ErrorDescription']}"
                        )
                except (ValueError, KeyError):
                    pass

            raise MVolaTransactionError(
                message=error_message,
                code=(
                    e.response.status_code
                    if hasattr(e, "response") and e.response
                    else None
                ),
                response=e.response if hasattr(e, "response") else None,
            ) from e

    def get_transaction_details(
        self, transaction_id, correlation_id=None, user_language=DEFAULT_LANGUAGE
    ):
        """
        Get details of a transaction

        Args:
            transaction_id (str): Transaction ID
            correlation_id (str, optional): Custom correlation ID for request
            user_language (str, optional): User language (FR or MG)

        Returns:
            dict: Transaction details response

        Raises:
            MVolaTransactionError: If details request fails
        """
        # Create correlation ID if not provided
        if not correlation_id:
            correlation_id = self._generate_correlation_id()

        # Set up headers
        headers = self._get_headers(
            correlation_id=correlation_id, user_language=user_language
        )

        # Send request
        url = urljoin(self.base_url, f"{TRANSACTION_DETAILS_ENDPOINT}{transaction_id}")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json(),
            }

        except requests.exceptions.RequestException as e:
            error_message = "Failed to get transaction details"

            # Try to extract error details if available
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    if "fault" in error_data:
                        error_message = (
                            f"{error_message}: {error_data['fault'].get('message', '')}"
                        )
                    elif "ErrorDescription" in error_data:
                        error_message = (
                            f"{error_message}: {error_data['ErrorDescription']}"
                        )
                except (ValueError, KeyError):
                    pass

            raise MVolaTransactionError(
                message=error_message,
                code=(
                    e.response.status_code
                    if hasattr(e, "response") and e.response
                    else None
                ),
                response=e.response if hasattr(e, "response") else None,
            ) from e
