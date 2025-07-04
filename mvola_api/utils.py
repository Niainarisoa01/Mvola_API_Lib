"""
Utility functions for MVola API
"""

import base64
import datetime
import re
import uuid


def encode_credentials(consumer_key, consumer_secret):
    """
    Encode consumer key and secret for Basic Auth

    Args:
        consumer_key (str): Consumer key
        consumer_secret (str): Consumer secret

    Returns:
        str: Base64 encoded credentials
    """
    credentials = f"{consumer_key}:{consumer_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return encoded


def generate_uuid():
    """
    Generate a UUID for correlation IDs

    Returns:
        str: UUID v4 string
    """
    return str(uuid.uuid4())


def generate_correlation_id():
    """
    Generate a correlation ID for MVola API

    For testing with a specific backend, you may need to use a fixed ID like "123"
    instead of a random UUID. Uncomment the fixed ID line for such cases.

    Returns:
        str: Correlation ID
    """
    # For production, use a random UUID
    return str(uuid.uuid4())
    
    # For testing with specific backends, you might need a fixed ID
    # return "123"


def get_formatted_datetime():
    """
    Get current datetime in ISO 8601 format as required by MVola API

    Returns:
        str: Formatted datetime string (YYYY-MM-DDThh:mm:ss.sssZ)
    """
    # Use timezone-aware UTC datetime instead of deprecated utcnow()
    try:
        # For Python 3.11+ where datetime.UTC is available
        return (
            datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
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


def get_mvola_headers(access_token, correlation_id, user_language="MG", callback_url=None, partner_msisdn=None, partner_name=None):
    """
    Get standard headers for MVola API requests based on working example format
    
    Args:
        access_token (str): OAuth2 access token
        correlation_id (str): Correlation ID
        user_language (str, optional): User language, default is "MG"
        callback_url (str, optional): Callback URL for notifications
        partner_msisdn (str, optional): Partner MSISDN
        partner_name (str, optional): Partner name
        
    Returns:
        dict: Headers for API request
    """
    headers = {
        "version": "1.0",
        "X-CorrelationID": correlation_id,
        "UserLanguage": user_language,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept-Charset": "utf-8",
    }
    
    if callback_url:
        headers["X-Callback-URL"] = callback_url
        
    if partner_msisdn:
        headers["UserAccountIdentifier"] = f"msisdn;{partner_msisdn}"
        
    if partner_name:
        headers["partnerName"] = partner_name
        
    return headers


def validate_msisdn(msisdn):
    """
    Validate Madagascar phone number format

    Args:
        msisdn (str): Phone number to validate

    Returns:
        bool: True if valid, False otherwise
    """
    # Basic Madagascar phone number validation (starts with 03)
    pattern = r"^0(3\d{8})$"
    return re.match(pattern, msisdn) is not None


def validate_description(description):
    """
    Validate transaction description

    Args:
        description (str): Description text

    Returns:
        tuple: (is_valid, error_message)
    """
    if not description:
        return False, "Description is required"

    if len(description) > 50:
        return False, "Description must be less than 50 characters"

    # Check for invalid characters (only allow characters specified in MVola documentation)
    # Documentation says: allow only "- ", ".", "_ ", ","
    # We'll also allow alphanumeric characters as those are implicitly permitted
    if re.search(r"[^a-zA-Z0-9\s\-\._,]", description):
        return False, "Description contains invalid characters. Only alphanumeric, spaces, hyphens, dots, underscores, and commas are allowed."

    return True, ""


def format_transaction_response(response_data):
    """
    Format transaction response data into a more user-friendly format

    Args:
        response_data (dict): Raw response data

    Returns:
        dict: Formatted response data
    """
    formatted = {
        "success": True,
        "transaction_id": response_data.get("objectReference", ""),
        "status": response_data.get("status", ""),
        "server_correlation_id": response_data.get("serverCorrelationId", ""),
        "notification_method": response_data.get("notificationMethod", ""),
    }

    return formatted
