"""
MVola API constants

Security-hardened configuration values for the MVola API library.
"""

# API URLs — These are the ONLY allowed base URLs
SANDBOX_URL = "https://devapi.mvola.mg"
PRODUCTION_URL = "https://api.mvola.mg"

# Whitelist of allowed base URLs to prevent URL redirection attacks
ALLOWED_BASE_URLS = frozenset([SANDBOX_URL, PRODUCTION_URL])

# API Endpoints
TOKEN_ENDPOINT = "/token"
MERCHANT_PAY_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/"
TRANSACTION_STATUS_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/status/"
TRANSACTION_DETAILS_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/"

# Headers
API_VERSION = "1.0"
DEFAULT_LANGUAGE = "FR"
DEFAULT_CURRENCY = "Ar"

# HTTP Settings
DEFAULT_TIMEOUT = 30  # seconds
MAX_RESPONSE_SIZE = 1 * 1024 * 1024  # 1 MB — prevent OOM from oversized responses

# Transaction limits
MAX_TRANSACTION_AMOUNT = 10_000_000  # 10 million Ar — configurable safety limit
MIN_TRANSACTION_AMOUNT = 1  # Minimum 1 Ar

# Grant types
GRANT_TYPE = "client_credentials"
TOKEN_SCOPE = "EXT_INT_MVOLA_SCOPE"

# Test account numbers (sandbox only)
TEST_MSISDN_1 = "0343500003"
TEST_MSISDN_2 = "0343500004"

# Rate limiting defaults
RATE_LIMIT_MAX_REQUESTS = 30  # Maximum requests per window
RATE_LIMIT_REFILL_RATE = 2.0  # Tokens replenished per second

# Description constraints
MAX_DESCRIPTION_LENGTH = 50
