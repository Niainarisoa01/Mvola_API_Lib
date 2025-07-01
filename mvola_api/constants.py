"""
MVola API constants
"""

# API URLs
SANDBOX_URL = "https://devapi.mvola.mg"
PRODUCTION_URL = "https://api.mvola.mg"

# API Endpoints
TOKEN_ENDPOINT = "/token"
MERCHANT_PAY_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/"
TRANSACTION_STATUS_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/status/"
TRANSACTION_DETAILS_ENDPOINT = "/mvola/mm/transactions/type/merchantpay/1.0.0/"

# Headers
API_VERSION = "1.0"
DEFAULT_LANGUAGE = "FR"
DEFAULT_CURRENCY = "Ar"

# Grant types
GRANT_TYPE = "client_credentials"
TOKEN_SCOPE = "EXT_INT_MVOLA_SCOPE"

# Test account numbers
TEST_MSISDN_1 = "0343500003"
TEST_MSISDN_2 = "0343500004"
