"""
MVola API Authentication Module
"""

import base64
import time
from urllib.parse import urljoin

import requests

from .constants import GRANT_TYPE, TOKEN_ENDPOINT, TOKEN_SCOPE
from .exceptions import MVolaAuthError


class MVolaAuth:
    """
    Class for managing authentication with MVola API
    """

    def __init__(self, consumer_key, consumer_secret, base_url):
        """
        Initialize the auth module

        Args:
            consumer_key (str): Consumer key from MVola Developer Portal
            consumer_secret (str): Consumer secret from MVola Developer Portal
            base_url (str): Base URL for the API (sandbox or production)
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.base_url = base_url
        self.token = None
        self.token_expiry = 0

    def _encode_credentials(self):
        """
        Encode consumer key and secret for Basic Auth

        Returns:
            str: Base64 encoded credentials
        """
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded

    def generate_token(self, force_refresh=False):
        """
        Generate an access token for MVola API

        Args:
            force_refresh (bool): Force token refresh even if current token is valid

        Returns:
            dict: Token response with access_token, token_type, expires_in, scope

        Raises:
            MVolaAuthError: If token generation fails
        """
        # Check if token is still valid (with 60 seconds buffer)
        current_time = time.time()
        if not force_refresh and self.token and current_time < self.token_expiry - 60:
            return self.token

        # Set up the request
        url = urljoin(self.base_url, TOKEN_ENDPOINT)
        headers = {
            "Authorization": f"Basic {self._encode_credentials()}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        }
        data = {"grant_type": GRANT_TYPE, "scope": TOKEN_SCOPE}

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()  # Raise exception for non-200 responses

            token_data = response.json()
            # Calculate token expiry time
            self.token = token_data
            self.token_expiry = current_time + token_data.get("expires_in", 3600)

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

    def get_access_token(self, force_refresh=False):
        """
        Get current access token or generate a new one

        Args:
            force_refresh (bool): Force token refresh

        Returns:
            str: Access token string
        """
        token_data = self.generate_token(force_refresh)
        return token_data["access_token"]
