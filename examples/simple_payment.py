#!/usr/bin/env python
"""
Example script demonstrating the basic payment flow with MVola API.
"""
import os
import time
import logging
from dotenv import load_dotenv

from mvola_api import MVolaClient, MVolaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Check required environment variables
required_vars = [
    'MVOLA_CONSUMER_KEY', 
    'MVOLA_CONSUMER_SECRET',
    'MVOLA_PARTNER_NAME',
    'MVOLA_PARTNER_MSISDN'
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please create a .env file with the required variables.")
    exit(1)

def main():
    """Run the example payment flow"""
    print("MVola API Example - Simple Payment Flow")
    print("-" * 50)

    # Initialize client
    client = MVolaClient(
        consumer_key=os.getenv('MVOLA_CONSUMER_KEY'),
        consumer_secret=os.getenv('MVOLA_CONSUMER_SECRET'),
        partner_name=os.getenv('MVOLA_PARTNER_NAME'),
        partner_msisdn=os.getenv('MVOLA_PARTNER_MSISDN'),
        sandbox=True  # Use sandbox environment for testing
    )

    # Step 1: Generate token
    print("\n1. Generating API token...")
    try:
        token_data = client.generate_token()
        print(f"✓ Token generated successfully (expires in {token_data.get('expires_in', 3600)}s)")
    except MVolaError as e:
        print(f"✗ Token generation failed: {e}")
        return

    # Step 2: Initiate a payment
    print("\n2. Initiating a payment transaction...")
    
    # For sandbox testing, use the test numbers
    debit_msisdn = "0343500003"  # Customer
    credit_msisdn = "0343500004"  # Merchant
    
    try:
        payment_result = client.initiate_payment(
            amount=10000,
            debit_msisdn=debit_msisdn,
            credit_msisdn=credit_msisdn,
            description="Test payment",
            callback_url="https://example.com/webhook"  # Replace with your callback URL
        )
        
        print(f"✓ Payment initiated successfully")
        
        # Save the server correlation ID for status checks
        server_correlation_id = payment_result['response']['serverCorrelationId']
        print(f"  Server Correlation ID: {server_correlation_id}")
        print(f"  Status: {payment_result['response']['status']}")
        
    except MVolaError as e:
        print(f"✗ Payment initiation failed: {e}")
        return

    # Step 3: Check transaction status (poll a few times)
    print("\n3. Checking transaction status...")
    
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        print(f"  Attempt {attempt}/{max_attempts}...")
        
        try:
            status_result = client.get_transaction_status(server_correlation_id)
            status = status_result['response']['status']
            print(f"  Status: {status}")
            
            # If the transaction has completed or failed, stop polling
            if status in ['completed', 'failed', 'rejected']:
                if status == 'completed':
                    transaction_id = status_result['response'].get('objectReference')
                    print(f"  Transaction ID: {transaction_id}")
                    
                    # Get transaction details
                    print("\n4. Getting transaction details...")
                    details = client.get_transaction_details(transaction_id)
                    print(f"  Amount: {details['response'].get('amount')}")
                    print(f"  Currency: {details['response'].get('currency')}")
                    print(f"  Status: {details['response'].get('transactionStatus')}")
                break
                
            # Wait before next attempt
            if attempt < max_attempts:
                print("  Waiting for transaction to complete...")
                time.sleep(5)
                
        except MVolaError as e:
            print(f"✗ Failed to get transaction status: {e}")
            break
    
    print("\nExample completed.")

if __name__ == "__main__":
    main() 