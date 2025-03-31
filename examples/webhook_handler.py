#!/usr/bin/env python
"""
Example webhook handler for MVola API transaction notifications.
This is a simple Flask application that can be used to receive
transaction status updates from MVola API.

To run this in development:
1. pip install flask python-dotenv
2. python webhook_handler.py
3. Use a tool like ngrok to expose the local server to the internet
4. Configure the X-Callback-URL in your MVola transaction to point to
   your exposed URL, e.g. https://your-ngrok-url.ngrok.io/mvola/webhook
"""
import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mvola_webhook")

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Transaction storage (in-memory for this example)
# In a real application, you would use a database
transactions = {}

@app.route('/mvola/webhook', methods=['POST'])
def mvola_webhook():
    """
    Handle incoming webhook notifications from MVola API
    """
    logger.info("Received MVola webhook notification")
    
    # Get request data
    try:
        request_data = request.get_json()
        logger.info(f"Webhook data: {json.dumps(request_data, indent=2)}")
        
        # Extract transaction information
        transaction_id = request_data.get('transactionReference', '')
        status = request_data.get('status', 'unknown')
        amount = request_data.get('amount', '0')
        
        # Store transaction data
        transactions[transaction_id] = {
            'id': transaction_id,
            'status': status,
            'amount': amount,
            'timestamp': datetime.now().isoformat(),
            'raw_data': request_data
        }
        
        logger.info(f"Transaction {transaction_id} updated with status: {status}")
        
        # Process transaction based on status
        if status == 'completed':
            # Transaction was successful, process order fulfillment
            logger.info(f"Processing successful payment for transaction {transaction_id}")
            # Your business logic here...
            
        elif status == 'failed':
            # Transaction failed
            logger.warning(f"Payment failed for transaction {transaction_id}")
            # Your business logic here...
            
        return jsonify({'status': 'success', 'message': 'Notification received'}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/mvola/transactions', methods=['GET'])
def list_transactions():
    """
    List all received transactions (for demonstration purposes)
    """
    return jsonify({
        'status': 'success',
        'count': len(transactions),
        'transactions': list(transactions.values())
    })

@app.route('/mvola/transactions/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """
    Get details of a specific transaction
    """
    transaction = transactions.get(transaction_id)
    if transaction:
        return jsonify({
            'status': 'success',
            'transaction': transaction
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Transaction {transaction_id} not found'
        }), 404

if __name__ == '__main__':
    # Get port from environment variable or use default (5000)
    port = int(os.environ.get('PORT', 5000))
    
    # For development purposes, use the development server
    # In production, use a proper WSGI server like Gunicorn
    app.run(host='0.0.0.0', port=port, debug=True)
    
    # Print instructions
    print(f"MVola webhook handler running on port {port}")
    print("Use a tool like ngrok to expose the local server to the internet")
    print("Example: ngrok http 5000") 