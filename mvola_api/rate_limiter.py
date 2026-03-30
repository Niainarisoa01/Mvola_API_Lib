"""
Thread-safe rate limiter for MVola API calls.

Implements a token bucket algorithm to prevent API abuse
and protect against runaway transaction loops.
"""

import threading
import time
from .exceptions import MVolaError


class RateLimitError(MVolaError):
    """Raised when rate limit is exceeded"""
    pass


class TokenBucketRateLimiter:
    """
    Thread-safe token bucket rate limiter.

    Controls the rate of API calls to prevent abuse and
    protect against accidental transaction storms.

    Args:
        max_tokens: Maximum number of tokens (requests) in the bucket
        refill_rate: Tokens added per second
        name: Name of this limiter (for error messages)
    """

    def __init__(self, max_tokens: int = 10, refill_rate: float = 1.0, name: str = "api"):
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")

        self._max_tokens = max_tokens
        self._refill_rate = refill_rate
        self._tokens = float(max_tokens)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()
        self._name = name

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        tokens_to_add = elapsed * self._refill_rate
        self._tokens = min(self._max_tokens, self._tokens + tokens_to_add)
        self._last_refill = now

    def acquire(self, tokens: int = 1, blocking: bool = True, timeout: float = 30.0) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait until tokens are available
            timeout: Maximum time to wait (seconds) if blocking

        Returns:
            True if tokens were acquired

        Raises:
            RateLimitError: If non-blocking and no tokens available,
                           or if timeout exceeded
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")

        deadline = time.monotonic() + timeout if blocking else 0

        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

            if not blocking or time.monotonic() >= deadline:
                raise RateLimitError(
                    message=(
                        f"Rate limit exceeded for {self._name}. "
                        f"Maximum {self._max_tokens} requests allowed. "
                        "Please wait before retrying."
                    )
                )

            # Wait a small interval before retrying
            time.sleep(min(0.1, timeout / 10))

    @property
    def available_tokens(self) -> float:
        """Get the current number of available tokens."""
        with self._lock:
            self._refill()
            return self._tokens

    def __repr__(self) -> str:
        return (
            f"TokenBucketRateLimiter(name='{self._name}', "
            f"max={self._max_tokens}, rate={self._refill_rate}/s)"
        )
