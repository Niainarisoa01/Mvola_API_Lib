"""
MVola API Authentication Module

Secure, thread-safe token management for MVola API authentication.
"""

import base64
import gc
import time
from threading import Lock
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from .constants import (
    ALLOWED_BASE_URLS,
    DEFAULT_TIMEOUT,
    GRANT_TYPE,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_REFILL_RATE,
    TOKEN_ENDPOINT,
    TOKEN_SCOPE,
)
from .exceptions import MVolaAuthError, MVolaValidationError
from .http_client import SecureHTTPClient
from .rate_limiter import TokenBucketRateLimiter


class MVolaAuth:
    """
    Class for managing authentication with MVola API.

    Thread-safe implementation with secure token management.
    Credentials are stored as private attributes and never exposed
    through properties, repr, or str.
    """

    def __init__(self, consumer_key: str, consumer_secret: str, base_url: str) -> None:
        """
        Initialize the auth module.

        Args:
            consumer_key: Consumer key from MVola Developer Portal
            consumer_secret: Consumer secret from MVola Developer Portal
            base_url: Base URL for the API (sandbox or production)

        Raises:
            MVolaValidationError: If credentials are empty or base_url is invalid
        """
        # Validate inputs
        if not consumer_key or not isinstance(consumer_key, str):
            raise MVolaValidationError(message="consumer_key is required and must be a non-empty string")
        if not consumer_secret or not isinstance(consumer_secret, str):
            raise MVolaValidationError(message="consumer_secret is required and must be a non-empty string")
        if not base_url or not isinstance(base_url, str):
            raise MVolaValidationError(message="base_url is required and must be a non-empty string")

        # Validate base_url against whitelist
        base_url = base_url.rstrip("/")
        if base_url not in ALLOWED_BASE_URLS:
            raise MVolaValidationError(
                message=(
                    f"Invalid base_url: '{base_url}'. "
                    f"Allowed URLs: {', '.join(sorted(ALLOWED_BASE_URLS))}"
                )
            )

        # Store credentials as private attributes — NEVER expose them
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._base_url = base_url
        self._token: Optional[Dict[str, Any]] = None
        self._token_expiry: float = 0
        self._token_lock = Lock()

        # Secure HTTP client and rate limiter
        self._http_client = SecureHTTPClient()
        self._rate_limiter = TokenBucketRateLimiter(
            max_tokens=RATE_LIMIT_MAX_REQUESTS,
            refill_rate=RATE_LIMIT_REFILL_RATE,
            name="auth",
        )

    def __repr__(self) -> str:
        """Secure repr — NEVER leaks any credential information."""
        return (
            f"MVolaAuth(base_url='{self._base_url}', "
            f"has_token={self._token is not None})"
        )

    def __str__(self) -> str:
        """Secure str representation."""
        return f"MVolaAuth(base_url='{self._base_url}')"

    def __del__(self) -> None:
        """Securely clear credentials from memory on deletion."""
        try:
            self._consumer_key = None
            self._consumer_secret = None
            self._token = None
            self._token_expiry = 0
            if hasattr(self, "_http_client") and self._http_client:
                self._http_client.close()
        except Exception:
            pass

    @property
    def base_url(self) -> str:
        """Access base URL (read-only property)."""
        return self._base_url

    @property
    def token_expiry(self) -> float:
        """Access token expiry timestamp (read-only property)."""
        return self._token_expiry

    def _encode_credentials(self) -> str:
        """
        Encode consumer key and secret for Basic Auth.

        Returns:
            Base64 encoded credentials
        """
        credentials = f"{self._consumer_key}:{self._consumer_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded

    def _clear_expired_token(self) -> None:
        """Clear expired tokens from memory for security."""
        if self._token and time.time() >= self._token_expiry:
            self._token = None
            self._token_expiry = 0
            gc.collect()

    def is_token_valid(self) -> bool:
        """
        Check if the current token is still valid.

        Returns:
            True if token exists and is not expired (with 60s safety buffer)
        """
        if not self._token:
            return False
        return time.time() < self._token_expiry - 60

    def generate_token(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Generate an access token for MVola API (thread-safe, rate-limited).

        Args:
            force_refresh: Force token refresh even if current token is valid

        Returns:
            Token response with access_token, token_type, expires_in, scope

        Raises:
            MVolaAuthError: If token generation fails
            RateLimitError: If rate limit is exceeded
        """
        # Rate limit check before acquiring lock
        self._rate_limiter.acquire()

        with self._token_lock:
            # Check if token is still valid (with 60 seconds buffer)
            current_time = time.time()
            if not force_refresh and self._token and current_time < self._token_expiry - 60:
                return self._token

            # Clear any expired token
            self._clear_expired_token()

            # Set up the request
            url = urljoin(self._base_url, TOKEN_ENDPOINT)
            headers = {
                "Authorization": f"Basic {self._encode_credentials()}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cache-Control": "no-store",
            }
            data = {"grant_type": GRANT_TYPE, "scope": TOKEN_SCOPE}

            try:
                response = self._http_client.post(
                    url, headers=headers, data=data, timeout=DEFAULT_TIMEOUT
                )
                response.raise_for_status()

                token_data = response.json()

                # Validate the token response has required fields
                if "access_token" not in token_data:
                    raise MVolaAuthError(
                        message="Invalid token response: missing access_token"
                    )

                # Calculate token expiry time
                self._token = token_data
                self._token_expiry = current_time + token_data.get("expires_in", 3600)

                return token_data

            except MVolaAuthError:
                raise
            except Exception as e:
                error_message = "Failed to generate token"

                # Try to extract error details if available
                if hasattr(e, "response") and e.response is not None:
                    try:
                        error_data = e.response.json()
                        if "error" in error_data:
                            error_message = (
                                f"{error_message}: "
                                f"{error_data.get('error_description', error_data['error'])}"
                            )
                    except (ValueError, KeyError):
                        pass

                raise MVolaAuthError(
                    message=error_message,
                    code=(
                        e.response.status_code
                        if hasattr(e, "response") and e.response
                        else None
                    ),
                    response=e.response if hasattr(e, "response") else None,
                ) from e

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get current access token or generate a new one.

        Args:
            force_refresh: Force token refresh

        Returns:
            Access token string

        Raises:
            MVolaAuthError: If token generation fails
        """
        token_data = self.generate_token(force_refresh)
        return token_data["access_token"]
