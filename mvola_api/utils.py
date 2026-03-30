"""
Utility functions for MVola API

Security-hardened utility functions for input validation,
credential masking, and request formatting.
"""

import base64
import datetime
import ipaddress
import re
import uuid
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from .constants import MAX_DESCRIPTION_LENGTH


def encode_credentials(consumer_key: str, consumer_secret: str) -> str:
    """
    Encode consumer key and secret for Basic Auth

    Args:
        consumer_key: Consumer key
        consumer_secret: Consumer secret

    Returns:
        Base64 encoded credentials
    """
    if not consumer_key or not consumer_secret:
        raise ValueError("Both consumer_key and consumer_secret are required")
    credentials = f"{consumer_key}:{consumer_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return encoded


def generate_uuid() -> str:
    """
    Generate a UUID for correlation IDs

    Returns:
        UUID v4 string
    """
    return str(uuid.uuid4())


def generate_correlation_id() -> str:
    """
    Generate a correlation ID for MVola API

    Returns:
        Correlation ID (UUID v4)
    """
    return str(uuid.uuid4())


def get_formatted_datetime() -> str:
    """
    Get current datetime in ISO 8601 format as required by MVola API

    Returns:
        Formatted datetime string (YYYY-MM-DDThh:mm:ss.sssZ)
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


def sanitize_id(id_value: str, param_name: str = "ID") -> str:
    """
    Validate and sanitize an identifier to prevent path traversal and injection.

    Args:
        id_value: The identifier value to sanitize
        param_name: Name of the parameter (for error messages)

    Returns:
        The sanitized identifier

    Raises:
        ValueError: If the identifier is invalid
    """
    if not id_value or not isinstance(id_value, str):
        raise ValueError(f"{param_name} is required and must be a string")

    # Strip whitespace
    id_value = id_value.strip()

    # Check for empty after strip
    if not id_value:
        raise ValueError(f"{param_name} cannot be empty")

    # Only allow alphanumeric and hyphens (no dots — they enable path traversal)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', id_value):
        raise ValueError(
            f"{param_name} contains invalid characters. "
            "Only alphanumeric characters, hyphens, and underscores are allowed."
        )

    # Length limit
    if len(id_value) > 256:
        raise ValueError(f"{param_name} is too long (max 256 characters)")

    return id_value


def _is_private_ip(hostname: str) -> bool:
    """
    Check if a hostname resolves to a private/internal IP address.

    Covers all RFC 1918, RFC 5737, loopback, link-local, and
    reserved address spaces for both IPv4 and IPv6.

    Args:
        hostname: The hostname to check

    Returns:
        True if the hostname points to a private/internal address
    """
    # Check literal IP addresses
    try:
        addr = ipaddress.ip_address(hostname)
        return (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_multicast
            or addr.is_unspecified
        )
    except ValueError:
        pass

    # Check common private hostnames
    private_hostnames = {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
    }
    if hostname.lower() in private_hostnames:
        return True

    # Block .local, .internal, .private TLDs
    private_tlds = (".local", ".internal", ".private", ".localhost", ".corp")
    if any(hostname.lower().endswith(tld) for tld in private_tlds):
        return True

    return False


def validate_callback_url(url: str, allow_http: bool = False) -> str:
    """
    Validate a callback URL for security (SSRF protection).

    Args:
        url: The callback URL to validate
        allow_http: If True, allow HTTP scheme (for sandbox testing only)

    Returns:
        The validated URL

    Raises:
        ValueError: If the URL is invalid or insecure
    """
    if not url or not isinstance(url, str):
        raise ValueError("Callback URL is required and must be a string")

    # Strip whitespace
    url = url.strip()

    parsed = urlparse(url)

    # Scheme validation
    allowed_schemes = ("https",)
    if allow_http:
        allowed_schemes = ("https", "http")

    if parsed.scheme not in allowed_schemes:
        if allow_http:
            raise ValueError("Callback URL must use HTTPS or HTTP scheme")
        raise ValueError("Callback URL must use HTTPS scheme")

    if not parsed.netloc:
        raise ValueError("Callback URL must have a valid hostname")

    hostname = parsed.hostname or ""

    if not hostname:
        raise ValueError("Callback URL must have a valid hostname")

    # Block private/internal IP addresses using robust ipaddress module
    if _is_private_ip(hostname):
        raise ValueError(
            "Callback URL must not point to internal/private addresses"
        )

    # Block URLs with credentials (user:password@host)
    if parsed.username or parsed.password:
        raise ValueError("Callback URL must not contain credentials")

    # Block unusual ports that might indicate port scanning
    if parsed.port and parsed.port not in (80, 443, 8080, 8443):
        raise ValueError(
            f"Callback URL uses non-standard port {parsed.port}. "
            "Only ports 80, 443, 8080, 8443 are allowed."
        )

    return url


def mask_msisdn(msisdn: str) -> str:
    """
    Mask an MSISDN for safe logging.

    Args:
        msisdn: Phone number to mask

    Returns:
        Masked phone number (e.g., "034****04")
    """
    if not msisdn or not isinstance(msisdn, str) or len(msisdn) < 4:
        return "****"
    return msisdn[:3] + "****" + msisdn[-2:]


def mask_token(token: str) -> str:
    """
    Mask a token for safe logging.

    Args:
        token: Token to mask

    Returns:
        Masked token (e.g., "eyJ4...W6A")
    """
    if not token or not isinstance(token, str) or len(token) < 8:
        return "****"
    return token[:4] + "..." + token[-3:]


def get_mvola_headers(
    access_token: str,
    correlation_id: str,
    user_language: str = "MG",
    callback_url: Optional[str] = None,
    partner_msisdn: Optional[str] = None,
    partner_name: Optional[str] = None,
    is_sandbox: bool = False,
) -> Dict[str, str]:
    """
    Get standard headers for MVola API requests.

    Args:
        access_token: OAuth2 access token
        correlation_id: Correlation ID
        user_language: User language, default is "MG"
        callback_url: Callback URL for notifications
        partner_msisdn: Partner MSISDN
        partner_name: Partner name
        is_sandbox: If True, allow HTTP callback URLs (sandbox only)

    Returns:
        Headers dict for API request

    Raises:
        ValueError: If callback_url is invalid
    """
    if not access_token:
        raise ValueError("access_token is required")
    if not correlation_id:
        raise ValueError("correlation_id is required")

    headers = {
        "version": "1.0",
        "X-CorrelationID": correlation_id,
        "UserLanguage": user_language,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept-Charset": "utf-8",
    }

    if callback_url:
        # STRICT validation — never silently bypass
        validate_callback_url(callback_url, allow_http=is_sandbox)
        headers["X-Callback-URL"] = callback_url

    if partner_msisdn:
        headers["UserAccountIdentifier"] = f"msisdn;{partner_msisdn}"

    if partner_name:
        headers["partnerName"] = partner_name

    return headers


def validate_msisdn(msisdn: str) -> bool:
    """
    Validate Madagascar phone number format.

    Args:
        msisdn: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    if not msisdn or not isinstance(msisdn, str):
        return False
    # Basic Madagascar phone number validation (starts with 03, exactly 10 digits)
    pattern = r"^0(3\d{8})$"
    return re.match(pattern, msisdn) is not None


def validate_description(description: str) -> Tuple[bool, str]:
    """
    Validate transaction description.

    Args:
        description: Description text

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not description:
        return False, "Description is required"

    if not isinstance(description, str):
        return False, "Description must be a string"

    if len(description) > MAX_DESCRIPTION_LENGTH:
        return False, f"Description must be less than {MAX_DESCRIPTION_LENGTH} characters"

    # Check for invalid characters — only allow safe characters
    # MVola documentation allows: alphanumeric, spaces, hyphens, dots, underscores, commas
    if re.search(r"[^a-zA-Z0-9\s\-\._,àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ]", description):
        return False, (
            "Description contains invalid characters. "
            "Only alphanumeric, spaces, hyphens, dots, underscores, and commas are allowed."
        )

    return True, ""


def format_transaction_response(response_data: dict) -> dict:
    """
    Format transaction response data into a more user-friendly format.

    Args:
        response_data: Raw response data

    Returns:
        Formatted response data
    """
    if not isinstance(response_data, dict):
        return {"success": False, "error": "Invalid response data"}

    formatted = {
        "success": True,
        "transaction_id": response_data.get("objectReference", ""),
        "status": response_data.get("status", ""),
        "server_correlation_id": response_data.get("serverCorrelationId", ""),
        "notification_method": response_data.get("notificationMethod", ""),
    }

    return formatted
