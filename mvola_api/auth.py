"""
MVola API Authentication Module
"""

import base64
import gc
import time
from threading import Lock
from typing import Dict, Any, Optional
from urllib.parse import urljoin

import requests

from .constants import DEFAULT_TIMEOUT, GRANT_TYPE, TOKEN_ENDPOINT, TOKEN_SCOPE
from .exceptions import MVolaAuthError


class MVolaAuth:
    """
    Class for managing authentication with MVola API

    Thread-safe implementation with secure token management.
    """

    def __init__(self, consumer_key: str, consumer_secret: str, base_url: str) -> None:
        """
        Initialize the auth module

        Args:
            consumer_key (str): Consumer key from MVola Developer Portal
            consumer_secret (str): Consumer secret from MVola Developer Portal
            base_url (str): Base URL for the API (sandbox or production)
        """
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self.base_url = base_url
        self._token: Optional[Dict[str, Any]] = None
        self._token_expiry: float = 0
        self._token_lock = Lock()

    def __repr__(self) -> str:
        """Secure repr to prevent credential leakage in logs/debug output"""
        return (
            f"MVolaAuth(base_url='{self.base_url}', "
            f"has_token={self._token is not None}, "
            f"key_hint='{self._consumer_key[:4]}...')"
        )

    def __str__(self) -> str:
        """Secure str representation"""
        return f"MVolaAuth(base_url='{self.base_url}')"

    @property
    def consumer_key(self) -> str:
        """Access consumer key (read-only property)"""
        return self._consumer_key

    @property
    def consumer_secret(self) -> str:
        """Access consumer secret (read-only property)"""
        return self._consumer_secret

    @property
    def token(self) -> Optional[Dict[str, Any]]:
        """Access current token (read-only property)"""
        return self._token

    @property
    def token_expiry(self) -> float:
        """Access token expiry (read-only property)"""
        return self._token_expiry

    def _encode_credentials(self) -> str:
        """
        Encode consumer key and secret for Basic Auth

        Returns:
            str: Base64 encoded credentials
        """
        credentials = f"{self._consumer_key}:{self._consumer_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded

    def _clear_expired_token(self) -> None:
        """Clear expired tokens from memory for security"""
        if self._token and time.time() >= self._token_expiry:
            self._token = None
            self._token_expiry = 0
            gc.collect()

    def is_token_valid(self) -> bool:
        """
        Check if the current token is still valid
        
        Returns:
            bool: True if token exists and is not expired (with 60s buffer)
        """
        if not self._token:
            return False
        return time.time() < self._token_expiry - 60

    def generate_token(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Generate an access token for MVola API (thread-safe)

        Args:
            force_refresh (bool): Force token refresh even if current token is valid

        Returns:
            dict: Token response with access_token, token_type, expires_in, scope

        Raises:
            MVolaAuthError: If token generation fails
        """
        with self._token_lock:
            # Check if token is still valid (with 60 seconds buffer)
            current_time = time.time()
            if not force_refresh and self._token and current_time < self._token_expiry - 60:
                return self._token

            # Clear any expired token
            self._clear_expired_token()

            # Set up the request
            url = urljoin(self.base_url, TOKEN_ENDPOINT)
            headers = {
                "Authorization": f"Basic {self._encode_credentials()}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cache-Control": "no-cache",
            }
            data = {"grant_type": GRANT_TYPE, "scope": TOKEN_SCOPE}

            try:
                response = requests.post(url, headers=headers, data=data, timeout=DEFAULT_TIMEOUT)
                response.raise_for_status()  # Raise exception for non-200 responses

                token_data = response.json()
                # Calculate token expiry time
                self._token = token_data
                self._token_expiry = current_time + token_data.get("expires_in", 3600)

                return token_data

            except requests.exceptions.RequestException as e:
                error_message = "Failed to generate token"

                # Try to extract error details if available
                if hasattr(e, "response") and e.response is not None:
                    try:
                        error_data = e.response.json()
                        if "error" in error_data:
                            error_message = f"{error_message}: {error_data.get('error_description', error_data['error'])}"
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
        Get current access token or generate a new one

        Args:
            force_refresh (bool): Force token refresh

        Returns:
            str: Access token string
        """
        token_data = self.generate_token(force_refresh)
        return token_data["access_token"]
