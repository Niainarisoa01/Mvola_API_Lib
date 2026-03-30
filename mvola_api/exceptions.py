"""
MVola API exceptions

Hierarchical exception classes for granular error handling.
All exceptions sanitize error messages to prevent information leakage.
"""


class MVolaError(Exception):
    """Base exception for all MVola-related errors."""

    def __init__(self, message, code=None, response=None):
        self.message = str(message)[:500] if message else "Unknown error"
        self.code = code
        # Store response reference but don't expose raw body in str/repr
        self._response = response
        super().__init__(self.message)

    @property
    def response(self):
        """Access the raw response (if available)."""
        return self._response

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def __repr__(self):
        return f"{self.__class__.__name__}(message='{self.message}', code={self.code})"


class MVolaAuthError(MVolaError):
    """Authentication-related errors (invalid credentials, expired tokens)."""
    pass


class MVolaTransactionError(MVolaError):
    """Transaction-related errors (payment failures, status errors)."""
    pass


class MVolaValidationError(MVolaError):
    """Validation errors for request parameters (invalid MSISDN, amount, etc.)."""
    pass


class MVolaConnectionError(MVolaError):
    """Connection-related errors (timeouts, TLS failures, DNS errors)."""
    pass
