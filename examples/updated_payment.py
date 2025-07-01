#!/usr/bin/env python
"""
Example script demonstrating the basic payment flow with the updated MVola API.
"""
import os
import time
import logging
import uuid
from dotenv import load_dotenv

# Import from the updated mvola_api package
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
    """Run the example payment flow with the updated API"""
    print("MVola API Example - Simple Payment Flow (Updated API)")
    print("-" * 60)

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
    
    # For sandbox testing, use the test numbers (check current sandbox test numbers)
    debit_msisdn = "0343500003"  # Customer
    credit_msisdn = "0343500004"  # Merchant
    
    # Generate a transaction reference
    transaction_ref = f"MVOLA-TEST-{uuid.uuid4().hex[:8]}"
    
    try:
        payment_result = client.initiate_payment(
            amount=10000,
            debit_msisdn=debit_msisdn,
            credit_msisdn=credit_msisdn,
            description="Test payment with updated API",
            callback_url="https://example.com/webhook",  # Replace with your callback URL
            requesting_organisation_transaction_reference=transaction_ref,
            foreign_currency="USD",
            foreign_amount=2.5
        )
        
        print(f"✓ Payment initiated successfully")
        print(f"  Transaction Reference: {transaction_ref}")
        
        # Save the server correlation ID for status checks
        server_correlation_id = payment_result['response']['serverCorrelationId']
        print(f"  Server Correlation ID: {server_correlation_id}")
        print(f"  Status: {payment_result['response']['status']}")
        print(f"  Notification Method: {payment_result['response'].get('notificationMethod', 'N/A')}")
        
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
                    try:
                        details = client.get_transaction_details(transaction_id)
                        print(f"  Amount: {details['response'].get('amount', 'N/A')}")
                        print(f"  Currency: {details['response'].get('currency', 'N/A')}")
                        print(f"  Status: {details['response'].get('transactionStatus', 'N/A')}")
                        
                        # Print foreign currency information if available
                        fc_metadata = next((item for item in details['response'].get('metadata', []) 
                                          if item.get('key') == 'fc'), None)
                        fc_amount_metadata = next((item for item in details['response'].get('metadata', []) 
                                                if item.get('key') == 'amountFc'), None)
                        
                        if fc_metadata and fc_amount_metadata:
                            print(f"  Foreign Currency: {fc_metadata.get('value', 'N/A')}")
                            print(f"  Foreign Amount: {fc_amount_metadata.get('value', 'N/A')}")
                            
                    except MVolaError as e:
                        print(f"✗ Failed to get transaction details: {e}")
                break
                
            # Wait before next attempt
            if attempt < max_attempts:
                print("  Waiting for transaction to complete...")
                time.sleep(5)
                
        except MVolaError as e:
            print(f"✗ Failed to get transaction status: {e}")
            break
    
    print("\nExample completed.")
    print("\nNote: In the sandbox environment, transactions often remain in 'pending' status.")
    print("For testing, you may need to manually approve the transaction in the MVola Developer Portal.")

if __name__ == "__main__":
    main() 