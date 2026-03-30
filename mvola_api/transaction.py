"""
MVola API Transaction Module

Secure transaction management with input validation,
amount safety checks, and hardened HTTP communication.
"""

import datetime
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from .constants import (
    API_VERSION,
    DEFAULT_CURRENCY,
    DEFAULT_LANGUAGE,
    DEFAULT_TIMEOUT,
    MAX_TRANSACTION_AMOUNT,
    MERCHANT_PAY_ENDPOINT,
    MIN_TRANSACTION_AMOUNT,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_REFILL_RATE,
    TRANSACTION_DETAILS_ENDPOINT,
    TRANSACTION_STATUS_ENDPOINT,
)
from .exceptions import MVolaTransactionError, MVolaValidationError
from .http_client import SecureHTTPClient
from .rate_limiter import TokenBucketRateLimiter
from .utils import get_mvola_headers, sanitize_id, validate_description, validate_msisdn


class MVolaTransaction:
    """
    Class for managing MVola transactions.

    Uses Decimal for amount validation to prevent floating-point
    precision errors. All HTTP calls go through SecureHTTPClient
    with TLS enforcement and response size limits.
    """

    def __init__(self, auth, base_url: str, partner_name: str, partner_msisdn: str = None):
        """
        Initialize the transaction module.

        Args:
            auth: MVolaAuth authentication object
            base_url: Base URL for the API
            partner_name: Name of your application
            partner_msisdn: Partner MSISDN used for UserAccountIdentifier
        """
        self._auth = auth
        self._base_url = base_url
        self._partner_name = partner_name
        self._partner_msisdn = partner_msisdn

        # Each transaction module gets its own HTTP client and rate limiter
        self._http_client = SecureHTTPClient()
        self._rate_limiter = TokenBucketRateLimiter(
            max_tokens=RATE_LIMIT_MAX_REQUESTS,
            refill_rate=RATE_LIMIT_REFILL_RATE,
            name="transaction",
        )

    def __del__(self) -> None:
        """Clean up HTTP client resources."""
        try:
            if hasattr(self, "_http_client") and self._http_client:
                self._http_client.close()
        except Exception:
            pass

    @property
    def is_sandbox(self) -> bool:
        """Check if we're in sandbox mode based on the base URL."""
        return "devapi" in self._base_url

    def _generate_correlation_id(self) -> str:
        """
        Generate a unique correlation ID.

        Returns:
            UUID string
        """
        return str(uuid.uuid4())

    def _get_current_datetime(self) -> str:
        """
        Get current datetime in ISO 8601 format.

        Returns:
            Formatted datetime (YYYY-MM-DDThh:mm:ss.sssZ)
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
        self, amount: str, debit_msisdn: str, credit_msisdn: str, description: str
    ) -> None:
        """
        Validate transaction parameters with strict security checks.

        Uses Decimal for amount validation to prevent floating-point errors.
        Enforces configurable min/max amount limits.

        Args:
            amount: Transaction amount
            debit_msisdn: MSISDN of the payer
            credit_msisdn: MSISDN of the merchant
            description: Transaction description

        Raises:
            MVolaValidationError: If validation fails
        """
        errors = []

        # Check amount using Decimal for precision (not float!)
        try:
            decimal_amount = Decimal(str(amount))
            if decimal_amount <= 0:
                errors.append("Amount must be positive")
            elif decimal_amount < MIN_TRANSACTION_AMOUNT:
                errors.append(f"Amount must be at least {MIN_TRANSACTION_AMOUNT} Ar")
            elif decimal_amount > MAX_TRANSACTION_AMOUNT:
                errors.append(
                    f"Amount exceeds maximum limit of {MAX_TRANSACTION_AMOUNT:,} Ar. "
                    "Contact support for higher limits."
                )
            # Check that amount is a whole number (MVola doesn't support centimes)
            if decimal_amount != int(decimal_amount):
                errors.append("Amount must be a whole number (no decimals)")
        except (InvalidOperation, ValueError):
            errors.append("Amount must be a valid number")

        # Check MSISDNs
        if not debit_msisdn or not isinstance(debit_msisdn, str):
            errors.append("Debit MSISDN is required")
        elif not validate_msisdn(debit_msisdn):
            errors.append("Debit MSISDN format is invalid (must be 03XXXXXXXX)")

        if not credit_msisdn or not isinstance(credit_msisdn, str):
            errors.append("Credit MSISDN is required")
        elif not validate_msisdn(credit_msisdn):
            errors.append("Credit MSISDN format is invalid (must be 03XXXXXXXX)")

        # Check that debit and credit are different
        if debit_msisdn and credit_msisdn and debit_msisdn == credit_msisdn:
            errors.append("Debit and credit MSISDN must be different")

        # Check description using the centralized validator
        is_valid, error_msg = validate_description(description)
        if not is_valid:
            errors.append(error_msg)

        if errors:
            raise MVolaValidationError(message="; ".join(errors))

    def _get_headers(
        self,
        correlation_id: Optional[str] = None,
        user_language: str = DEFAULT_LANGUAGE,
        callback_url: Optional[str] = None,
        cell_id_a: Optional[str] = None,
        geo_location_a: Optional[str] = None,
        cell_id_b: Optional[str] = None,
        geo_location_b: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get standard headers for API requests.

        Args:
            correlation_id: Correlation ID
            user_language: User language (FR or MG)
            callback_url: Callback URL for notifications
            cell_id_a: Cell ID A
            geo_location_a: Geo Location A
            cell_id_b: Cell ID B
            geo_location_b: Geo Location B

        Returns:
            Headers dict for API request
        """
        access_token = self._auth.get_access_token()

        if not correlation_id:
            correlation_id = self._generate_correlation_id()

        if not self._partner_msisdn:
            raise MVolaValidationError(
                message="Partner MSISDN is required for transaction requests"
            )

        # Use the utility function to get headers
        headers = get_mvola_headers(
            access_token=access_token,
            correlation_id=correlation_id,
            user_language=user_language,
            callback_url=callback_url,
            partner_msisdn=self._partner_msisdn,
            partner_name=self._partner_name,
            is_sandbox=self.is_sandbox,
        )

        # Add additional optional headers (sanitize first)
        if cell_id_a:
            headers["CellIdA"] = str(cell_id_a)[:50]

        if geo_location_a:
            headers["GeoLocationA"] = str(geo_location_a)[:100]

        if cell_id_b:
            headers["CellIdB"] = str(cell_id_b)[:50]

        if geo_location_b:
            headers["GeoLocationB"] = str(geo_location_b)[:100]

        return headers

    def _handle_error_response(self, e, default_message: str) -> None:
        """
        Extract error details from a failed API response and raise appropriate exception.

        Args:
            e: The caught exception
            default_message: Default error message prefix

        Raises:
            MVolaTransactionError: Always raised with extracted details
        """
        error_message = default_message

        if hasattr(e, "response") and e.response is not None:
            try:
                error_data = e.response.json()
                # Extract error detail but limit length to prevent log flooding
                if "fault" in error_data:
                    detail = str(error_data["fault"].get("message", ""))[:200]
                    error_message = f"{error_message}: {detail}"
                elif "errorDescription" in error_data:
                    detail = str(error_data["errorDescription"])[:200]
                    error_message = f"{error_message}: {detail}"
                elif "ErrorDescription" in error_data:
                    detail = str(error_data["ErrorDescription"])[:200]
                    error_message = f"{error_message}: {detail}"
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

    def initiate_merchant_payment(
        self,
        amount,
        debit_msisdn,
        credit_msisdn,
        description,
        currency=DEFAULT_CURRENCY,
        foreign_currency="USD",
        foreign_amount="1",
        correlation_id=None,
        user_language="MG",
        callback_url=None,
        requesting_organisation_transaction_reference="",
        original_transaction_reference="",
        cell_id_a=None,
        geo_location_a=None,
        cell_id_b=None,
        geo_location_b=None,
    ):
        """
        Initiate a merchant payment transaction.

        Args:
            amount: Transaction amount (must be a positive whole number)
            debit_msisdn: MSISDN of the payer
            credit_msisdn: MSISDN of the merchant
            description: Transaction description (max 50 chars, safe chars only)
            currency: Currency code, default "Ar"
            foreign_currency: Foreign currency code, default "USD"
            foreign_amount: Amount in foreign currency, default "1"
            correlation_id: Custom correlation ID
            user_language: User language (MG recommended)
            callback_url: Callback URL for notifications
            requesting_organisation_transaction_reference: Your transaction ID
            original_transaction_reference: Reference number
            cell_id_a: Cell ID A
            geo_location_a: Geo Location A
            cell_id_b: Cell ID B
            geo_location_b: Geo Location B

        Returns:
            Transaction response dict

        Raises:
            MVolaTransactionError: If transaction initiation fails
            MVolaValidationError: If parameters are invalid
            RateLimitError: If rate limit is exceeded
        """
        # Rate limit check
        self._rate_limiter.acquire()

        # Validate parameters
        self._validate_transaction_params(
            amount, debit_msisdn, credit_msisdn, description
        )

        # Create correlation ID if not provided
        if not correlation_id:
            correlation_id = self._generate_correlation_id()

        # Generate transaction reference if not provided
        if not requesting_organisation_transaction_reference:
            requesting_organisation_transaction_reference = f"ref{str(uuid.uuid4())[:8]}"

        # Get access token
        access_token = self._auth.get_access_token()

        # Build headers with strict callback URL validation
        headers = get_mvola_headers(
            access_token=access_token,
            correlation_id=correlation_id,
            user_language=user_language,
            callback_url=callback_url,
            partner_msisdn=self._partner_msisdn,
            partner_name=self._partner_name,
            is_sandbox=self.is_sandbox,
        )

        # Add optional headers
        if cell_id_a:
            headers["CellIdA"] = str(cell_id_a)[:50]
        if geo_location_a:
            headers["GeoLocationA"] = str(geo_location_a)[:100]
        if cell_id_b:
            headers["CellIdB"] = str(cell_id_b)[:50]
        if geo_location_b:
            headers["GeoLocationB"] = str(geo_location_b)[:100]

        # Build request body
        request_date = self._get_current_datetime()

        payload = {
            "amount": str(amount),
            "currency": currency,
            "descriptionText": description,
            "requestDate": request_date,
            "requestingOrganisationTransactionReference": requesting_organisation_transaction_reference,
            "originalTransactionReference": original_transaction_reference or "MVOLA_123",
            "debitParty": [{"key": "msisdn", "value": debit_msisdn}],
            "creditParty": [{"key": "msisdn", "value": credit_msisdn}],
            "metadata": [
                {"key": "partnerName", "value": credit_msisdn},
                {"key": "fc", "value": foreign_currency or "USD"},
                {"key": "amountFc", "value": str(foreign_amount or "1")},
            ],
        }

        # Send request via secure HTTP client (POST is NEVER retried)
        url = urljoin(self._base_url, MERCHANT_PAY_ENDPOINT)

        try:
            response = self._http_client.post(
                url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json(),
                "correlation_id": correlation_id,
            }

        except Exception as e:
            self._handle_error_response(e, "Failed to initiate transaction")

    def get_transaction_status(
        self, server_correlation_id, correlation_id=None, user_language=DEFAULT_LANGUAGE
    ):
        """
        Get the status of a transaction.

        Args:
            server_correlation_id: Server correlation ID from initiate_transaction
            correlation_id: Custom correlation ID for request
            user_language: User language (FR or MG)

        Returns:
            Transaction status response dict

        Raises:
            MVolaTransactionError: If status request fails
        """
        # Rate limit check
        self._rate_limiter.acquire()

        # Sanitize the server correlation ID to prevent path traversal
        server_correlation_id = sanitize_id(server_correlation_id, "server_correlation_id")

        # Create correlation ID if not provided
        if not correlation_id:
            correlation_id = self._generate_correlation_id()

        # Set up headers
        headers = self._get_headers(
            correlation_id=correlation_id, user_language=user_language
        )

        # Send request (GET — will be retried automatically on transient failures)
        url = urljoin(
            self._base_url, f"{TRANSACTION_STATUS_ENDPOINT}{server_correlation_id}"
        )

        try:
            response = self._http_client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json(),
            }

        except Exception as e:
            self._handle_error_response(e, "Failed to get transaction status")

    def get_transaction_details(
        self, transaction_id, correlation_id=None, user_language=DEFAULT_LANGUAGE
    ):
        """
        Get details of a transaction.

        Args:
            transaction_id: Transaction ID
            correlation_id: Custom correlation ID for request
            user_language: User language (FR or MG)

        Returns:
            Transaction details response dict

        Raises:
            MVolaTransactionError: If details request fails
        """
        # Rate limit check
        self._rate_limiter.acquire()

        # Sanitize the transaction ID to prevent path traversal
        transaction_id = sanitize_id(transaction_id, "transaction_id")

        # Create correlation ID if not provided
        if not correlation_id:
            correlation_id = self._generate_correlation_id()

        # Set up headers
        headers = self._get_headers(
            correlation_id=correlation_id, user_language=user_language
        )

        # Send request (GET — will be retried automatically on transient failures)
        url = urljoin(self._base_url, f"{TRANSACTION_DETAILS_ENDPOINT}{transaction_id}")

        try:
            response = self._http_client.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json(),
            }

        except Exception as e:
            self._handle_error_response(e, "Failed to get transaction details")
