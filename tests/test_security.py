#!/usr/bin/env python
"""
Security test suite for MVola API library.

Tests all security-critical functionality including:
- Path traversal prevention
- SSRF protection
- Credential exposure prevention
- Amount validation (Decimal precision)
- Rate limiting
- Input sanitization
- TLS enforcement
"""
import os
import sys
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Import modules to test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mvola_api import MVolaClient, MVolaAuth, MVolaTransaction
from mvola_api.constants import (
    ALLOWED_BASE_URLS,
    MAX_TRANSACTION_AMOUNT,
    MIN_TRANSACTION_AMOUNT,
    SANDBOX_URL,
)
from mvola_api.exceptions import (
    MVolaError,
    MVolaAuthError,
    MVolaValidationError,
)
from mvola_api.rate_limiter import RateLimitError, TokenBucketRateLimiter
from mvola_api.utils import (
    mask_msisdn,
    mask_token,
    sanitize_id,
    validate_callback_url,
    validate_description,
    validate_msisdn,
)


class TestPathTraversalPrevention(unittest.TestCase):
    """Test that all ID inputs prevent path traversal attacks."""

    def test_sanitize_id_blocks_double_dots(self):
        """Path traversal with .. must be blocked."""
        with self.assertRaises(ValueError):
            sanitize_id("../../../etc/passwd")

    def test_sanitize_id_blocks_slashes(self):
        """Path traversal with / must be blocked."""
        with self.assertRaises(ValueError):
            sanitize_id("foo/bar/baz")

    def test_sanitize_id_blocks_backslashes(self):
        """Path traversal with \\ must be blocked."""
        with self.assertRaises(ValueError):
            sanitize_id("foo\\bar")

    def test_sanitize_id_blocks_dots(self):
        """Dots are no longer allowed in IDs (removed from regex)."""
        with self.assertRaises(ValueError):
            sanitize_id("file.extension")

    def test_sanitize_id_blocks_null_bytes(self):
        """Null bytes must be blocked."""
        with self.assertRaises(ValueError):
            sanitize_id("valid\x00evil")

    def test_sanitize_id_blocks_empty(self):
        """Empty strings must be rejected."""
        with self.assertRaises(ValueError):
            sanitize_id("")

    def test_sanitize_id_blocks_whitespace_only(self):
        """Whitespace-only strings must be rejected."""
        with self.assertRaises(ValueError):
            sanitize_id("   ")

    def test_sanitize_id_blocks_none(self):
        """None must be rejected."""
        with self.assertRaises(ValueError):
            sanitize_id(None)

    def test_sanitize_id_blocks_too_long(self):
        """IDs over 256 chars must be rejected."""
        with self.assertRaises(ValueError):
            sanitize_id("a" * 257)

    def test_sanitize_id_allows_valid_uuids(self):
        """Valid UUID-style IDs must pass."""
        result = sanitize_id("550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(result, "550e8400-e29b-41d4-a716-446655440000")

    def test_sanitize_id_allows_alphanumeric_with_hyphens(self):
        """Alphanumeric with hyphens and underscores must pass."""
        result = sanitize_id("txn_abc-123")
        self.assertEqual(result, "txn_abc-123")

    def test_sanitize_id_strips_whitespace(self):
        """Leading/trailing whitespace must be stripped."""
        result = sanitize_id("  valid-id  ")
        self.assertEqual(result, "valid-id")


class TestSSRFProtection(unittest.TestCase):
    """Test that callback URL validation prevents SSRF attacks."""

    def test_blocks_localhost(self):
        with self.assertRaises(ValueError):
            validate_callback_url("https://localhost/callback")

    def test_blocks_127_0_0_1(self):
        with self.assertRaises(ValueError):
            validate_callback_url("https://127.0.0.1/callback")

    def test_blocks_0_0_0_0(self):
        with self.assertRaises(ValueError):
            validate_callback_url("https://0.0.0.0/callback")

    def test_blocks_ipv6_loopback(self):
        with self.assertRaises(ValueError):
            validate_callback_url("https://[::1]/callback")

    def test_blocks_private_10_x(self):
        with self.assertRaises(ValueError):
            validate_callback_url("https://10.0.0.1/callback")

    def test_blocks_private_192_168(self):
        with self.assertRaises(ValueError):
            validate_callback_url("https://192.168.1.1/callback")

    def test_blocks_private_172_16(self):
        with self.assertRaises(ValueError):
            validate_callback_url("https://172.16.0.1/callback")

    def test_blocks_http_by_default(self):
        """HTTP must be blocked by default (production)."""
        with self.assertRaises(ValueError):
            validate_callback_url("http://example.com/callback")

    def test_allows_http_in_sandbox(self):
        """HTTP can be allowed in sandbox mode."""
        result = validate_callback_url(
            "http://example.com/callback", allow_http=True
        )
        self.assertEqual(result, "http://example.com/callback")

    def test_blocks_ftp_scheme(self):
        with self.assertRaises(ValueError):
            validate_callback_url("ftp://example.com/file")

    def test_blocks_javascript_scheme(self):
        with self.assertRaises(ValueError):
            validate_callback_url("javascript:alert(1)")

    def test_blocks_credentials_in_url(self):
        """URLs with user:password@ must be blocked."""
        with self.assertRaises(ValueError):
            validate_callback_url("https://user:pass@example.com/callback")

    def test_blocks_unusual_ports(self):
        """Non-standard ports must be blocked to prevent port scanning."""
        with self.assertRaises(ValueError):
            validate_callback_url("https://example.com:22/callback")

    def test_allows_standard_ports(self):
        """Standard HTTPS port must be allowed."""
        result = validate_callback_url("https://example.com:443/callback")
        self.assertEqual(result, "https://example.com:443/callback")

    def test_blocks_internal_tlds(self):
        """Internal TLDs (.local, .internal) must be blocked."""
        with self.assertRaises(ValueError):
            validate_callback_url("https://server.local/callback")
        with self.assertRaises(ValueError):
            validate_callback_url("https://api.internal/callback")

    def test_blocks_empty_url(self):
        with self.assertRaises(ValueError):
            validate_callback_url("")

    def test_blocks_none_url(self):
        with self.assertRaises(ValueError):
            validate_callback_url(None)

    def test_allows_valid_https_url(self):
        """Valid HTTPS URLs must pass."""
        result = validate_callback_url("https://myapp.example.com/webhook")
        self.assertEqual(result, "https://myapp.example.com/webhook")


class TestCredentialExposurePrevention(unittest.TestCase):
    """Test that credentials are never exposed through repr, str, or properties."""

    def test_auth_repr_no_key(self):
        """MVolaAuth repr must not contain any part of the consumer key."""
        auth = MVolaAuth("secret_key_12345", "secret_value_67890", SANDBOX_URL)
        repr_str = repr(auth)
        self.assertNotIn("secret_key", repr_str)
        self.assertNotIn("12345", repr_str)
        self.assertNotIn("secret_value", repr_str)
        self.assertNotIn("67890", repr_str)

    def test_auth_str_no_key(self):
        """MVolaAuth str must not contain any credential info."""
        auth = MVolaAuth("secret_key_12345", "secret_value_67890", SANDBOX_URL)
        str_repr = str(auth)
        self.assertNotIn("secret_key", str_repr)
        self.assertNotIn("secret_value", str_repr)

    def test_auth_no_public_consumer_key_property(self):
        """Consumer key must NOT be accessible as a public property."""
        auth = MVolaAuth("test_key", "test_secret", SANDBOX_URL)
        # The _consumer_key attribute exists but not consumer_key property
        self.assertTrue(hasattr(auth, "_consumer_key"))
        # Accessing consumer_key should raise AttributeError
        with self.assertRaises(AttributeError):
            _ = auth.consumer_key

    def test_auth_no_public_consumer_secret_property(self):
        """Consumer secret must NOT be accessible as a public property."""
        auth = MVolaAuth("test_key", "test_secret", SANDBOX_URL)
        with self.assertRaises(AttributeError):
            _ = auth.consumer_secret

    @patch('mvola_api.client.MVolaAuth')
    @patch('mvola_api.client.MVolaTransaction')
    def test_client_repr_no_credentials(self, mock_txn, mock_auth):
        """MVolaClient repr must not reveal credentials."""
        client = MVolaClient(
            consumer_key="real_key_xyz",
            consumer_secret="real_secret_abc",
            partner_name="Test",
            sandbox=True,
        )
        repr_str = repr(client)
        self.assertNotIn("real_key", repr_str)
        self.assertNotIn("real_secret", repr_str)
        self.assertNotIn("xyz", repr_str)
        self.assertNotIn("abc", repr_str)

    @patch('mvola_api.client.MVolaAuth')
    @patch('mvola_api.client.MVolaTransaction')
    def test_client_no_public_consumer_key(self, mock_txn, mock_auth):
        """Client must not expose consumer_key as a public attribute."""
        client = MVolaClient(
            consumer_key="test_key",
            consumer_secret="test_secret",
            partner_name="Test",
            sandbox=True,
        )
        # Should NOT have public consumer_key attribute
        self.assertFalse(hasattr(client, "consumer_key"))
        self.assertFalse(hasattr(client, "consumer_secret"))


class TestAmountValidation(unittest.TestCase):
    """Test that amount validation uses Decimal and enforces limits."""

    def setUp(self):
        self.auth = MagicMock()
        self.auth.get_access_token.return_value = "test_token"
        self.txn = MVolaTransaction(self.auth, SANDBOX_URL, "Test", "0340000000")

    def test_rejects_negative_amount(self):
        with self.assertRaises(MVolaValidationError):
            self.txn._validate_transaction_params(
                "-100", "0340000001", "0340000002", "Test"
            )

    def test_rejects_zero_amount(self):
        with self.assertRaises(MVolaValidationError):
            self.txn._validate_transaction_params(
                "0", "0340000001", "0340000002", "Test"
            )

    def test_rejects_decimal_amount(self):
        """MVola doesn't support centimes — only whole numbers."""
        with self.assertRaises(MVolaValidationError):
            self.txn._validate_transaction_params(
                "100.50", "0340000001", "0340000002", "Test"
            )

    def test_rejects_amount_over_max(self):
        """Amount exceeding MAX_TRANSACTION_AMOUNT must be rejected."""
        huge_amount = str(MAX_TRANSACTION_AMOUNT + 1)
        with self.assertRaises(MVolaValidationError):
            self.txn._validate_transaction_params(
                huge_amount, "0340000001", "0340000002", "Test"
            )

    def test_rejects_non_numeric_amount(self):
        with self.assertRaises(MVolaValidationError):
            self.txn._validate_transaction_params(
                "not_a_number", "0340000001", "0340000002", "Test"
            )

    def test_accepts_valid_amount(self):
        """Valid whole number amount within limits must pass."""
        self.txn._validate_transaction_params(
            "1000", "0340000001", "0340000002", "Test payment"
        )

    def test_rejects_same_debit_credit(self):
        """Debit and credit MSISDN cannot be the same."""
        with self.assertRaises(MVolaValidationError):
            self.txn._validate_transaction_params(
                "1000", "0340000001", "0340000001", "Test"
            )


class TestMSISDNValidation(unittest.TestCase):
    """Test MSISDN validation for Madagascar numbers."""

    def test_valid_msisdn(self):
        self.assertTrue(validate_msisdn("0340000001"))
        self.assertTrue(validate_msisdn("0343500003"))

    def test_invalid_msisdn_wrong_prefix(self):
        self.assertFalse(validate_msisdn("0140000001"))

    def test_invalid_msisdn_too_short(self):
        self.assertFalse(validate_msisdn("034000"))

    def test_invalid_msisdn_too_long(self):
        self.assertFalse(validate_msisdn("03400000011"))

    def test_invalid_msisdn_letters(self):
        self.assertFalse(validate_msisdn("034ABCDEFG"))

    def test_invalid_msisdn_empty(self):
        self.assertFalse(validate_msisdn(""))

    def test_invalid_msisdn_none(self):
        self.assertFalse(validate_msisdn(None))


class TestDescriptionValidation(unittest.TestCase):
    """Test description validation blocks injection and enforces limits."""

    def test_valid_description(self):
        is_valid, _ = validate_description("Payment for services")
        self.assertTrue(is_valid)

    def test_rejects_empty(self):
        is_valid, _ = validate_description("")
        self.assertFalse(is_valid)

    def test_rejects_too_long(self):
        is_valid, _ = validate_description("A" * 51)
        self.assertFalse(is_valid)

    def test_rejects_special_chars(self):
        """Script injection characters must be blocked."""
        is_valid, _ = validate_description("<script>alert(1)</script>")
        self.assertFalse(is_valid)

    def test_rejects_sql_injection_chars(self):
        is_valid, _ = validate_description("'; DROP TABLE users; --")
        self.assertFalse(is_valid)

    def test_allows_safe_chars(self):
        """Hyphens, dots, underscores, commas must be allowed."""
        is_valid, _ = validate_description("Paiement - ref_123, ok")
        self.assertTrue(is_valid)

    def test_allows_malagasy_accents(self):
        """French/Malagasy accented characters must be allowed."""
        is_valid, _ = validate_description("Paiement référencé été")
        self.assertTrue(is_valid)


class TestMasking(unittest.TestCase):
    """Test that masking functions properly hide sensitive data."""

    def test_mask_msisdn(self):
        masked = mask_msisdn("0343500003")
        self.assertEqual(masked, "034****03")
        self.assertNotIn("343500", masked)

    def test_mask_msisdn_short(self):
        masked = mask_msisdn("03")
        self.assertEqual(masked, "****")

    def test_mask_msisdn_none(self):
        masked = mask_msisdn(None)
        self.assertEqual(masked, "****")

    def test_mask_token(self):
        masked = mask_token("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9")
        self.assertEqual(masked, "eyJh...CJ9")
        self.assertNotIn("bGciOiJSUzI1NiIs", masked)

    def test_mask_token_short(self):
        masked = mask_token("short")
        self.assertEqual(masked, "****")

    def test_mask_token_none(self):
        masked = mask_token(None)
        self.assertEqual(masked, "****")


class TestBaseURLValidation(unittest.TestCase):
    """Test that only whitelisted MVola API URLs are accepted."""

    def test_rejects_arbitrary_url(self):
        """Random URLs must be rejected to prevent credential theft."""
        with self.assertRaises(MVolaValidationError):
            MVolaAuth("key", "secret", "https://evil-server.com")

    def test_rejects_http_url(self):
        """HTTP (non-TLS) must be rejected."""
        with self.assertRaises(MVolaValidationError):
            MVolaAuth("key", "secret", "http://devapi.mvola.mg")

    def test_accepts_sandbox_url(self):
        """Sandbox URL must be accepted."""
        auth = MVolaAuth("key", "secret", "https://devapi.mvola.mg")
        self.assertEqual(auth.base_url, "https://devapi.mvola.mg")

    def test_accepts_production_url(self):
        """Production URL must be accepted."""
        auth = MVolaAuth("key", "secret", "https://api.mvola.mg")
        self.assertEqual(auth.base_url, "https://api.mvola.mg")

    def test_rejects_empty_url(self):
        with self.assertRaises(MVolaValidationError):
            MVolaAuth("key", "secret", "")

    def test_rejects_none_url(self):
        with self.assertRaises(MVolaValidationError):
            MVolaAuth("key", "secret", None)


class TestRateLimiter(unittest.TestCase):
    """Test the token bucket rate limiter."""

    def test_allows_requests_within_limit(self):
        limiter = TokenBucketRateLimiter(max_tokens=5, refill_rate=1.0)
        for _ in range(5):
            self.assertTrue(limiter.acquire(blocking=False))

    def test_blocks_when_exhausted(self):
        limiter = TokenBucketRateLimiter(max_tokens=2, refill_rate=0.1)
        limiter.acquire(blocking=False)
        limiter.acquire(blocking=False)
        with self.assertRaises(RateLimitError):
            limiter.acquire(blocking=False)

    def test_rejects_invalid_max_tokens(self):
        with self.assertRaises(ValueError):
            TokenBucketRateLimiter(max_tokens=0)

    def test_rejects_invalid_refill_rate(self):
        with self.assertRaises(ValueError):
            TokenBucketRateLimiter(refill_rate=-1)

    def test_repr(self):
        limiter = TokenBucketRateLimiter(max_tokens=10, refill_rate=1.0, name="test")
        self.assertIn("test", repr(limiter))


class TestExceptionSafety(unittest.TestCase):
    """Test that exceptions don't leak sensitive information."""

    def test_error_message_truncated(self):
        """Very long error messages must be truncated."""
        long_msg = "A" * 1000
        error = MVolaError(long_msg)
        self.assertEqual(len(error.message), 500)

    def test_error_repr_safe(self):
        """Exception repr must not contain raw response data."""
        error = MVolaError("test error", code=401, response=MagicMock())
        repr_str = repr(error)
        self.assertIn("test error", repr_str)
        self.assertNotIn("response", repr_str.lower().replace("response=none", ""))


class TestAuthCredentialValidation(unittest.TestCase):
    """Test that MVolaAuth validates credentials on initialization."""

    def test_rejects_empty_consumer_key(self):
        with self.assertRaises(MVolaValidationError):
            MVolaAuth("", "secret", SANDBOX_URL)

    def test_rejects_none_consumer_key(self):
        with self.assertRaises(MVolaValidationError):
            MVolaAuth(None, "secret", SANDBOX_URL)

    def test_rejects_empty_consumer_secret(self):
        with self.assertRaises(MVolaValidationError):
            MVolaAuth("key", "", SANDBOX_URL)

    def test_rejects_none_consumer_secret(self):
        with self.assertRaises(MVolaValidationError):
            MVolaAuth("key", None, SANDBOX_URL)


if __name__ == "__main__":
    unittest.main()
