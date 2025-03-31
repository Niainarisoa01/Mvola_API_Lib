"""
MVola API exceptions
"""


class MVolaError(Exception):
    """Base exception for all MVola-related errors"""

    def __init__(self, message, code=None, response=None):
        self.message = message
        self.code = code
        self.response = response
        super().__init__(self.message)

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class MVolaAuthError(MVolaError):
    """Authentication-related errors"""

    pass


class MVolaTransactionError(MVolaError):
    """Transaction-related errors"""

    pass


class MVolaValidationError(MVolaError):
    """Validation errors for request parameters"""

    pass


class MVolaConnectionError(MVolaError):
    """Connection-related errors"""

    pass
