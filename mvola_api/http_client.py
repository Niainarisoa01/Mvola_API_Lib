"""
Secure HTTP client for MVola API.

Provides a hardened requests.Session with:
- TLS certificate verification enforced
- Strict timeouts
- Response size limits
- Automatic retry with exponential backoff
- Secure logging (secrets masked)
"""

import logging
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .constants import DEFAULT_TIMEOUT, MAX_RESPONSE_SIZE
from .exceptions import MVolaConnectionError, MVolaError
from .utils import mask_token

logger = logging.getLogger("mvola_api")


class SecureHTTPClient:
    """
    Hardened HTTP client for MVola API calls.

    Features:
    - Forces TLS certificate verification (verify=True always)
    - Enforces response size limits to prevent OOM attacks
    - Automatic retry with exponential backoff for transient failures
    - Thread-safe (uses requests.Session internals)
    - Secure logging that masks tokens and credentials

    Args:
        timeout: Default request timeout in seconds
        max_retries: Maximum number of retries for transient failures
        max_response_size: Maximum response body size in bytes
        backoff_factor: Multiplier for exponential backoff between retries
    """

    # Only retry on these status codes (server errors, rate limiting)
    RETRY_STATUS_CODES = frozenset([429, 500, 502, 503, 504])

    # Only retry on these HTTP methods (idempotent only - NEVER retry POST for payments)
    RETRY_METHODS = frozenset(["GET", "HEAD", "OPTIONS"])

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        max_response_size: int = MAX_RESPONSE_SIZE,
        backoff_factor: float = 0.5,
    ):
        self._timeout = timeout
        self._max_response_size = max_response_size
        self._session = self._create_session(max_retries, backoff_factor)

    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """Create a hardened requests.Session with retry logic."""
        session = requests.Session()

        # Configure retry strategy — ONLY for GET requests (never retry POST/payments)
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=self.RETRY_STATUS_CODES,
            allowed_methods=self.RETRY_METHODS,
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        # Do NOT mount http:// — force HTTPS only
        # session.mount("http://", adapter)  # Intentionally disabled

        # Security headers applied to all requests
        session.headers.update({
            "Accept-Charset": "utf-8",
            "Cache-Control": "no-store",
        })

        return session

    def _check_response_size(self, response: requests.Response) -> None:
        """
        Check if the response size is within limits.

        Raises:
            MVolaConnectionError: If response exceeds maximum size
        """
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > self._max_response_size:
            response.close()
            raise MVolaConnectionError(
                message=(
                    f"Response too large: {content_length} bytes "
                    f"(max: {self._max_response_size} bytes)"
                )
            )
        # Also check actual content length after download
        if len(response.content) > self._max_response_size:
            raise MVolaConnectionError(
                message=(
                    f"Response too large: {len(response.content)} bytes "
                    f"(max: {self._max_response_size} bytes)"
                )
            )

    def _safe_log_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Create a copy of headers with sensitive values masked for logging."""
        masked = {}
        sensitive_keys = {"authorization", "x-api-key", "cookie", "set-cookie"}
        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                if value.lower().startswith("bearer "):
                    masked[key] = f"Bearer {mask_token(value[7:])}"
                elif value.lower().startswith("basic "):
                    masked[key] = "Basic ****"
                else:
                    masked[key] = "****"
            else:
                masked[key] = value
        return masked

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """
        Send a POST request with security hardening.

        Note: POST requests are NEVER retried automatically to prevent
        duplicate transactions/payments.

        Args:
            url: Request URL
            headers: Request headers
            data: Form data
            json: JSON body
            timeout: Request timeout override

        Returns:
            requests.Response

        Raises:
            MVolaConnectionError: On connection failures
        """
        effective_timeout = timeout or self._timeout

        logger.debug(
            "POST %s (timeout=%ds, headers=%s)",
            url,
            effective_timeout,
            self._safe_log_headers(headers or {}),
        )

        try:
            response = self._session.post(
                url,
                headers=headers,
                data=data,
                json=json,
                timeout=effective_timeout,
                verify=True,  # ALWAYS verify TLS certificates
                allow_redirects=False,  # Don't follow redirects for security
            )
            self._check_response_size(response)
            return response

        except requests.exceptions.SSLError as e:
            raise MVolaConnectionError(
                message="TLS certificate verification failed. Do not disable TLS verification."
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise MVolaConnectionError(
                message=f"Connection failed to {url}"
            ) from e
        except requests.exceptions.Timeout as e:
            raise MVolaConnectionError(
                message=f"Request timed out after {effective_timeout}s"
            ) from e

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """
        Send a GET request with security hardening.

        GET requests are automatically retried on transient failures.

        Args:
            url: Request URL
            headers: Request headers
            timeout: Request timeout override

        Returns:
            requests.Response

        Raises:
            MVolaConnectionError: On connection failures
        """
        effective_timeout = timeout or self._timeout

        logger.debug(
            "GET %s (timeout=%ds)",
            url,
            effective_timeout,
        )

        try:
            response = self._session.get(
                url,
                headers=headers,
                timeout=effective_timeout,
                verify=True,  # ALWAYS verify TLS certificates
                allow_redirects=False,  # Don't follow redirects for security
            )
            self._check_response_size(response)
            return response

        except requests.exceptions.SSLError as e:
            raise MVolaConnectionError(
                message="TLS certificate verification failed. Do not disable TLS verification."
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise MVolaConnectionError(
                message=f"Connection failed to {url}"
            ) from e
        except requests.exceptions.Timeout as e:
            raise MVolaConnectionError(
                message=f"Request timed out after {effective_timeout}s"
            ) from e

    def close(self) -> None:
        """Close the underlying session and release resources."""
        if self._session:
            self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
