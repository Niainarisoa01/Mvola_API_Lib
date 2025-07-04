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
from .utils import get_mvola_headers


class MVolaTransaction:
    """
    Class for managing MVola transactions
    
    Note: L'API MVola présente certaines limitations connues :
    - L'environnement sandbox retourne parfois l'erreur "Missing field" (code 4001) même lorsque tous
      les champs obligatoires mentionnés dans la documentation sont inclus.
    - L'authentification fonctionne correctement, mais l'initiation de paiement peut échouer avec 
      cette erreur malgré la présence des champs requis.
    - Les champs fc et amountFc doivent être inclus dans les métadonnées comme indiqué dans la 
      documentation, mais cela peut ne pas être suffisant dans l'environnement sandbox.
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
        elif len(description) > 50:  # Mise à jour pour limite de 50 caractères selon la documentation
            errors.append("Description must be less than 50 characters")
        elif any(c in description for c in "#$%^&*+={}[]|\\:;\"'<>?/"):
            errors.append("Description contains invalid characters")

        if errors:
            raise MVolaValidationError(message="; ".join(errors))

    def _get_headers(
        self, correlation_id=None, user_language=DEFAULT_LANGUAGE, callback_url=None,
        cell_id_a=None, geo_location_a=None, cell_id_b=None, geo_location_b=None
    ):
        """
        Get standard headers for API requests

        Args:
            correlation_id (str, optional): Correlation ID
            user_language (str, optional): User language (FR or MG)
            callback_url (str, optional): Callback URL for notifications
            cell_id_a (str, optional): Cell ID A
            geo_location_a (str, optional): Geo Location A
            cell_id_b (str, optional): Cell ID B
            geo_location_b (str, optional): Geo Location B

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

        # Use the utility function to get the headers
        headers = get_mvola_headers(
            access_token=access_token,
            correlation_id=correlation_id,
            user_language=user_language,
            callback_url=callback_url,
            partner_msisdn=self.partner_msisdn,
            partner_name=self.partner_name
        )
        
        # Add additional headers if provided
        if cell_id_a:
            headers["CellIdA"] = cell_id_a
            
        if geo_location_a:
            headers["GeoLocationA"] = geo_location_a
            
        if cell_id_b:
            headers["CellIdB"] = cell_id_b
            
        if geo_location_b:
            headers["GeoLocationB"] = geo_location_b

        return headers

    def initiate_merchant_payment(
        self,
        amount,
        debit_msisdn,
        credit_msisdn,
        description,
        currency=DEFAULT_CURRENCY,
        foreign_currency="USD",  # Défini par défaut à USD comme dans la documentation
        foreign_amount="1",      # Défini par défaut à 1 comme dans la documentation
        correlation_id=None,
        user_language="MG",      # Default to MG as in working example
        callback_url=None,
        requesting_organisation_transaction_reference="",
        original_transaction_reference="",
        cell_id_a=None,
        geo_location_a=None,
        cell_id_b=None,
        geo_location_b=None,
    ):
        """
        Initiate a merchant payment transaction
        
        Note: Malgré l'ajout de tous les champs requis dans la documentation, l'API MVola
        sandbox peut retourner une erreur "Missing field" (code 4001). Cela semble être une 
        limitation de l'environnement sandbox plutôt qu'un problème avec cette implémentation.

        Args:
            amount (str): Transaction amount
            debit_msisdn (str): MSISDN of the payer
            credit_msisdn (str): MSISDN of the merchant
            description (str): Transaction description
            currency (str, optional): Currency code, default is "Ar"
            foreign_currency (str, optional): Foreign currency code for conversion, default is "USD"
            foreign_amount (str, optional): Amount in foreign currency, default is "1"
            correlation_id (str, optional): Custom correlation ID
            user_language (str, optional): User language (MG recommended)
            callback_url (str, optional): Callback URL for notifications
            requesting_organisation_transaction_reference (str, optional): Transaction ID on client side
            original_transaction_reference (str, optional): Reference number related to original transaction
            cell_id_a (str, optional): Cell ID A from MVola API documentation
            geo_location_a (str, optional): Geo Location A from MVola API documentation
            cell_id_b (str, optional): Cell ID B from MVola API documentation
            geo_location_b (str, optional): Geo Location B from MVola API documentation

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

        # Generate transaction reference if not provided
        if not requesting_organisation_transaction_reference:
            requesting_organisation_transaction_reference = f"ref{str(uuid.uuid4())[:8]}"

        # Get access token
        access_token = self.auth.get_access_token()
        
        # Use the utility function to get the headers in the format that works
        headers = get_mvola_headers(
            access_token=access_token,
            correlation_id=correlation_id,
            user_language=user_language,
            callback_url=callback_url,
            partner_msisdn=self.partner_msisdn,
            partner_name=self.partner_name
        )
        
        # Add additional headers if provided
        if cell_id_a:
            headers["CellIdA"] = cell_id_a
            
        if geo_location_a:
            headers["GeoLocationA"] = geo_location_a
            
        if cell_id_b:
            headers["CellIdB"] = cell_id_b
            
        if geo_location_b:
            headers["GeoLocationB"] = geo_location_b

        # Set up request body
        request_date = self._get_current_datetime()

        # Create payload using the format from the working example
        payload = {
            "amount": str(amount),
            "currency": currency,
            "descriptionText": description,
            "requestDate": request_date,
            "requestingOrganisationTransactionReference": requesting_organisation_transaction_reference,
            "originalTransactionReference": original_transaction_reference or "MVOLA_123",  # Use default value if not provided
            "debitParty": [{"key": "msisdn", "value": debit_msisdn}],
            "creditParty": [{"key": "msisdn", "value": credit_msisdn}],
            "metadata": [
                {"key": "partnerName", "value": credit_msisdn},  # Use credit_msisdn as partnerName in metadata
                {"key": "fc", "value": foreign_currency or "USD"},
                {"key": "amountFc", "value": str(foreign_amount or "1")}
            ]
        }

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
                    elif "errorDescription" in error_data:
                        error_message = (
                            f"{error_message}: {error_data['errorDescription']}"
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
                    elif "errorDescription" in error_data:
                        error_message = (
                            f"{error_message}: {error_data['errorDescription']}"
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
                    elif "errorDescription" in error_data:
                        error_message = (
                            f"{error_message}: {error_data['errorDescription']}"
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
