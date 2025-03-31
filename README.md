# MVola API Python Library

A robust Python library for integrating with MVola mobile payment API in Madagascar.

## Installation

```bash
pip install mvola_api
```

## Features

- Simple and intuitive API for MVola payment integration
- Handles authentication token generation and management
- Supports merchant payment operations
- Comprehensive error handling
- Logging support
- Built-in parameter validation
- Works with both sandbox and production environments

## Quick Start

```python
from mvola_api import MVolaClient, SANDBOX_URL

# Initialize the client
client = MVolaClient(
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret",
    partner_name="Your Application Name",
    partner_msisdn="0340000000",  # Your merchant number
    sandbox=True  # Use sandbox environment
)

# Generate a token
token_data = client.generate_token()
print(f"Token generated: {token_data['access_token'][:10]}...")

# Initiate a payment
result = client.initiate_payment(
    amount=10000,
    debit_msisdn="0343500003",  # Customer phone number
    credit_msisdn="0343500004",  # Merchant phone number
    description="Payment for service",
    callback_url="https://example.com/callback"
)

# Track the server correlation ID for status checks
server_correlation_id = result['response']['serverCorrelationId']
print(f"Transaction initiated with correlation ID: {server_correlation_id}")

# Check transaction status
status = client.get_transaction_status(server_correlation_id)
print(f"Transaction status: {status['response']['status']}")

# Once transaction is completed, get details using transaction ID
transaction_id = status['response'].get('objectReference')
if transaction_id:
    details = client.get_transaction_details(transaction_id)
    print(f"Transaction details: {details['response']}")
```

## Sandbox Testing

For sandbox testing, use the following test phone numbers:
- 0343500003
- 0343500004

## Error Handling

The library provides custom exceptions for different error types:

```python
from mvola_api import MVolaClient, MVolaError, MVolaAuthError, MVolaTransactionError

client = MVolaClient(...)

try:
    result = client.initiate_payment(...)
except MVolaAuthError as e:
    print(f"Authentication error: {e}")
except MVolaTransactionError as e:
    print(f"Transaction error: {e}")
except MVolaError as e:
    print(f"General MVola error: {e}")
```

## API Documentation

### MVolaClient

The main client class for interacting with MVola API.

#### Initialization

```python
client = MVolaClient(
    consumer_key,          # Consumer key from MVola Developer Portal
    consumer_secret,       # Consumer secret from MVola Developer Portal
    partner_name,          # Your application/merchant name
    partner_msisdn=None,   # Partner MSISDN (phone number)
    sandbox=True,          # Use sandbox environment
    logger=None            # Custom logger
)
```

#### Methods

- `generate_token(force_refresh=False)`: Generate an access token
- `initiate_payment(amount, debit_msisdn, credit_msisdn, description, ...)`: Initiate a merchant payment
- `get_transaction_status(server_correlation_id, user_language="FR")`: Get transaction status
- `get_transaction_details(transaction_id, user_language="FR")`: Get transaction details

## Best Practices

1. **Token Management**: The library handles token refresh automatically, but you can force a refresh if needed.
2. **Error Handling**: Always implement proper error handling in your application.
3. **Logging**: The library includes logging, but you can provide your own logger.
4. **Sandbox Testing**: Always test your integration in the sandbox environment before going live.
5. **Webhook Handling**: Implement proper webhook handling for transaction notifications.

## Development

### Requirements

- Python 3.6+
- requests library

### Installation for Development

```bash
git clone https://github.com/yourusername/mvola_api.git
cd mvola_api
pip install -e .
```

## License

MIT

## Credits

Developed based on the official MVola API documentation. 