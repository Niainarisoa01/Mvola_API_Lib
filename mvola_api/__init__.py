"""
MVola API Python Library

A secure, robust Python library for MVola payment integration.
"""

try:
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("mvola-api-lib")
    except PackageNotFoundError:
        __version__ = "2.0.0"
except ImportError:
    __version__ = "2.0.0"

from .auth import MVolaAuth
from .client import MVolaClient
from .constants import PRODUCTION_URL, SANDBOX_URL
from .exceptions import (
    MVolaAuthError,
    MVolaConnectionError,
    MVolaError,
    MVolaTransactionError,
    MVolaValidationError,
)
from .http_client import SecureHTTPClient
from .rate_limiter import RateLimitError, TokenBucketRateLimiter
from .transaction import MVolaTransaction

__all__ = [
    # Client
    "MVolaClient",
    # Auth
    "MVolaAuth",
    # Transaction
    "MVolaTransaction",
    # HTTP
    "SecureHTTPClient",
    # Rate Limiting
    "TokenBucketRateLimiter",
    "RateLimitError",
    # URLs
    "SANDBOX_URL",
    "PRODUCTION_URL",
    # Exceptions
    "MVolaError",
    "MVolaAuthError",
    "MVolaTransactionError",
    "MVolaValidationError",
    "MVolaConnectionError",
]
