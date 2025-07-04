#!/usr/bin/env python
"""
Example demonstrating how to use MVola API with environment variables
"""

import logging
import sys
import os
from dotenv import load_dotenv

# Add parent directory to path to import mvola_api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mvola_api import MVolaClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mvola_example")

def main():
    """Run the example"""
    logger.info("Starting MVola API example with environment variables")
    
    # Method 1: Create client automatically from environment variables
    client = MVolaClient.from_env()
    
    # Method 2: Create client with explicit parameters, falling back to environment variables
    # client = MVolaClient(
    #     consumer_key=None,  # Will use MVOLA_CONSUMER_KEY from .env
    #     consumer_secret=None,  # Will use MVOLA_CONSUMER_SECRET from .env
    #     partner_name="Custom Partner Name",  # Override MVOLA_PARTNER_NAME from .env
    #     sandbox=True  # Override MVOLA_SANDBOX from .env
    # )
    
    # Get token to verify credentials
    try:
        token_data = client.generate_token()
        logger.info(f"Token generated successfully, expires in {token_data.get('expires_in')} seconds")
        
        # Optional: Initiate a test payment
        # result = client.initiate_payment(
        #     amount="1000",
        #     debit_msisdn="0343500003",  # Sandbox test number
        #     credit_msisdn="0343500004",  # Sandbox test number
        #     description="Test payment from environment variables example",
        #     callback_url="https://example.com/callback"
        # )
        # logger.info(f"Payment initiated: {result.get('correlation_id', '')}")
        # logger.info(f"Status: {result.get('response', {}).get('status', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 