#!/usr/bin/env python
"""
Example MVola Payment Web Application

This is a simple Flask application that demonstrates how to integrate
MVola payments into a web application. It provides a payment form and
handles payment processing and status updates.

Requirements:
    pip install flask python-dotenv mvola_api

To run:
    python payment_web_app.py
"""
import os
import uuid
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template_string, request, redirect, url_for, flash, session

# Import MVola API client (assuming it's installed)
try:
    from mvola_api import MVolaClient, MVolaError, MVolaAuthError, MVolaTransactionError
except ImportError:
    # For development purposes
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mvola_api import MVolaClient, MVolaError, MVolaAuthError, MVolaTransactionError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mvola_payment_app")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'development-secret-key')

# Initialize MVola client
try:
    client = MVolaClient(
        consumer_key=os.getenv('MVOLA_CONSUMER_KEY'),
        consumer_secret=os.getenv('MVOLA_CONSUMER_SECRET'),
        partner_name=os.getenv('MVOLA_PARTNER_NAME'),
        partner_msisdn=os.getenv('MVOLA_PARTNER_MSISDN'),
        sandbox=True  # Set to False for production
    )
except Exception as e:
    logger.error(f"Failed to initialize MVola client: {e}")
    client = None

# In-memory storage for orders and transactions
# In a real application, use a database
orders = {}
transactions = {}

# HTML Templates
# In a real application, you would use separate template files
BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>MVola Payment Demo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding-top: 20px; }
        .container { max-width: 800px; }
        .payment-form { margin: 30px 0; }
        .order-details { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">MVola Payment Demo</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
        
        <footer class="mt-5 text-center text-muted">
            <p>MVola Payment Integration Demo</p>
        </footer>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

INDEX_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
    <div class="row">
        <div class="col-md-8 offset-md-2">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0">Pay with MVola</h3>
                </div>
                <div class="card-body">
                    <form method="post" action="{{ url_for('create_order') }}" class="payment-form">
                        <div class="mb-3">
                            <label for="product" class="form-label">Product</label>
                            <select name="product" id="product" class="form-select" required>
                                <option value="">-- Select a product --</option>
                                <option value="product1">Product 1 - 5,000 Ar</option>
                                <option value="product2">Product 2 - 10,000 Ar</option>
                                <option value="product3">Product 3 - 20,000 Ar</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="phone" class="form-label">MVola Phone Number</label>
                            <input type="tel" class="form-control" id="phone" name="phone" 
                                   placeholder="034xxxxxxx" required>
                            <div class="form-text">For testing, use: 0343500003</div>
                        </div>
                        <div class="mb-3">
                            <label for="email" class="form-label">Email (optional)</label>
                            <input type="email" class="form-control" id="email" name="email" 
                                   placeholder="email@example.com">
                        </div>
                        <button type="submit" class="btn btn-primary">Pay with MVola</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
"""

ORDER_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
    <div class="row">
        <div class="col-md-8 offset-md-2">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0">Order Summary</h3>
                </div>
                <div class="card-body">
                    <div class="order-details">
                        <h4>Order #{{ order.id }}</h4>
                        <p><strong>Product:</strong> {{ order.product_name }}</p>
                        <p><strong>Amount:</strong> {{ order.amount }} Ar</p>
                        <p><strong>Phone:</strong> {{ order.phone }}</p>
                        <p><strong>Status:</strong> <span class="badge bg-{{ order.status_color }}">{{ order.status }}</span></p>
                        {% if order.transaction %}
                            <p><strong>Transaction ID:</strong> {{ order.transaction }}</p>
                        {% endif %}
                        {% if order.status == 'pending' %}
                            <div class="alert alert-info">
                                <h5>Payment Instructions:</h5>
                                <ol>
                                    <li>You will receive a prompt on your MVola phone.</li>
                                    <li>Enter your MVola PIN to confirm the payment.</li>
                                    <li>Wait for the confirmation message.</li>
                                </ol>
                            </div>
                            <p>
                                <a href="{{ url_for('check_status', order_id=order.id) }}" class="btn btn-info">
                                    Refresh Status
                                </a>
                            </p>
                        {% elif order.status == 'completed' %}
                            <div class="alert alert-success">
                                <h5>Payment Successful!</h5>
                                <p>Thank you for your payment. Your transaction was successful.</p>
                            </div>
                        {% elif order.status == 'failed' %}
                            <div class="alert alert-danger">
                                <h5>Payment Failed</h5>
                                <p>{{ order.error_message }}</p>
                                <p>
                                    <a href="{{ url_for('retry_payment', order_id=order.id) }}" class="btn btn-warning">
                                        Retry Payment
                                    </a>
                                </p>
                            </div>
                        {% endif %}
                    </div>
                    <p class="mt-4">
                        <a href="{{ url_for('index') }}" class="btn btn-secondary">Back to Home</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
"""

@app.route('/')
def index():
    """Render the payment form"""
    return render_template_string(INDEX_TEMPLATE)

@app.route('/create-order', methods=['POST'])
def create_order():
    """Create a new order and redirect to payment page"""
    if not client:
        flash("Payment service is currently unavailable", "danger")
        return redirect(url_for('index'))
    
    # Get form data
    product = request.form.get('product')
    phone = request.form.get('phone')
    email = request.form.get('email')
    
    # Validate input
    if not product or not phone:
        flash("Please fill in all required fields", "danger")
        return redirect(url_for('index'))
    
    # Map product to amount
    product_data = {
        'product1': {'name': 'Product 1', 'amount': 5000},
        'product2': {'name': 'Product 2', 'amount': 10000},
        'product3': {'name': 'Product 3', 'amount': 20000}
    }
    
    if product not in product_data:
        flash("Invalid product selected", "danger")
        return redirect(url_for('index'))
    
    # Create order
    order_id = str(uuid.uuid4())[:8]  # Short ID for demo
    amount = product_data[product]['amount']
    product_name = product_data[product]['name']
    
    order = {
        'id': order_id,
        'product': product,
        'product_name': product_name,
        'amount': amount,
        'phone': phone,
        'email': email,
        'status': 'new',
        'status_color': 'secondary',
        'created_at': datetime.now().isoformat(),
        'transaction': None,
        'correlation_id': None,
        'error_message': None
    }
    
    # Store order
    orders[order_id] = order
    
    # Redirect to payment page
    return redirect(url_for('process_payment', order_id=order_id))

@app.route('/process-payment/<order_id>')
def process_payment(order_id):
    """Process payment for the order"""
    if not client:
        flash("Payment service is currently unavailable", "danger")
        return redirect(url_for('index'))
    
    # Get order
    order = orders.get(order_id)
    if not order:
        flash("Order not found", "danger")
        return redirect(url_for('index'))
    
    # Check if order is already being processed
    if order['status'] not in ['new', 'failed']:
        return redirect(url_for('order_status', order_id=order_id))
    
    # Update order status
    order['status'] = 'processing'
    order['status_color'] = 'info'
    
    try:
        # In sandbox environment, use test merchant number
        merchant_msisdn = os.getenv('MVOLA_PARTNER_MSISDN', "0343500004")
        # Use the customer's phone number from the order
        customer_msisdn = order['phone']
        
        # For sandbox testing, force specific values
        if os.getenv('MVOLA_SANDBOX', 'true').lower() == 'true':
            customer_msisdn = "0343500003"  # Test customer number
        
        # Generate token if needed
        client.generate_token()
        
        # Initiate payment
        result = client.initiate_payment(
            amount=order['amount'],
            debit_msisdn=customer_msisdn,
            credit_msisdn=merchant_msisdn,
            description=f"Payment for {order['product_name']}",
            callback_url=os.getenv('MVOLA_CALLBACK_URL')
        )
        
        # Update order with transaction details
        if result['success']:
            order['status'] = 'pending'
            order['status_color'] = 'warning'
            order['correlation_id'] = result['response']['serverCorrelationId']
            
            # Log transaction
            transactions[order['correlation_id']] = {
                'order_id': order_id,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'response': result['response']
            }
            
            logger.info(f"Payment initiated for order {order_id}: {order['correlation_id']}")
        else:
            order['status'] = 'failed'
            order['status_color'] = 'danger'
            order['error_message'] = "Failed to initiate payment"
            logger.error(f"Payment initiation failed for order {order_id}")
    
    except MVolaError as e:
        order['status'] = 'failed'
        order['status_color'] = 'danger'
        order['error_message'] = str(e)
        logger.error(f"Payment error for order {order_id}: {e}")
    
    return redirect(url_for('order_status', order_id=order_id))

@app.route('/order/<order_id>')
def order_status(order_id):
    """Show order status page"""
    # Get order
    order = orders.get(order_id)
    if not order:
        flash("Order not found", "danger")
        return redirect(url_for('index'))
    
    return render_template_string(ORDER_TEMPLATE, order=order)

@app.route('/check-status/<order_id>')
def check_status(order_id):
    """Check payment status and update order"""
    if not client:
        flash("Payment service is currently unavailable", "danger")
        return redirect(url_for('index'))
    
    # Get order
    order = orders.get(order_id)
    if not order:
        flash("Order not found", "danger")
        return redirect(url_for('index'))
    
    # If no correlation ID, redirect to order page
    if not order['correlation_id']:
        return redirect(url_for('order_status', order_id=order_id))
    
    try:
        # Check transaction status
        status_result = client.get_transaction_status(order['correlation_id'])
        
        if status_result['success']:
            status = status_result['response']['status']
            
            # Update transaction record
            if order['correlation_id'] in transactions:
                transactions[order['correlation_id']]['status'] = status
                transactions[order['correlation_id']]['updated_at'] = datetime.now().isoformat()
                transactions[order['correlation_id']]['response'] = status_result['response']
            
            # Update order status
            if status == 'completed':
                order['status'] = 'completed'
                order['status_color'] = 'success'
                order['transaction'] = status_result['response'].get('objectReference', '')
                flash("Payment completed successfully", "success")
                
                # In a real application, you would fulfill the order here
                logger.info(f"Payment completed for order {order_id}")
                
            elif status == 'failed' or status == 'rejected':
                order['status'] = 'failed'
                order['status_color'] = 'danger'
                order['error_message'] = "Transaction failed or was rejected"
                flash("Payment failed", "danger")
                logger.warning(f"Payment failed for order {order_id}")
                
            else:
                # Still pending
                flash("Payment is still being processed. Please wait...", "info")
        else:
            flash("Failed to check payment status", "warning")
    
    except MVolaError as e:
        flash(f"Error checking payment status: {e}", "danger")
        logger.error(f"Status check error for order {order_id}: {e}")
    
    return redirect(url_for('order_status', order_id=order_id))

@app.route('/retry-payment/<order_id>')
def retry_payment(order_id):
    """Retry a failed payment"""
    # Get order
    order = orders.get(order_id)
    if not order:
        flash("Order not found", "danger")
        return redirect(url_for('index'))
    
    # Reset status
    order['status'] = 'new'
    order['correlation_id'] = None
    order['transaction'] = None
    order['error_message'] = None
    
    # Redirect to payment processing
    return redirect(url_for('process_payment', order_id=order_id))

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle MVola webhook notifications"""
    try:
        data = request.get_json()
        logger.info(f"Webhook received: {data}")
        
        # Extract transaction details
        transaction_id = data.get('transactionReference', '')
        status = data.get('status', '')
        correlation_id = data.get('serverCorrelationId', '')
        
        # Find the order for this transaction
        order_id = None
        for oid, order in orders.items():
            if order.get('correlation_id') == correlation_id:
                order_id = oid
                break
        
        if order_id and order_id in orders:
            # Update order status
            if status == 'completed':
                orders[order_id]['status'] = 'completed'
                orders[order_id]['status_color'] = 'success'
                orders[order_id]['transaction'] = transaction_id
            elif status in ['failed', 'rejected']:
                orders[order_id]['status'] = 'failed'
                orders[order_id]['status_color'] = 'danger'
                orders[order_id]['error_message'] = "Transaction failed or was rejected"
        
        return {'status': 'success'}, 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {'status': 'error', 'message': str(e)}, 500

# Register template
app.jinja_env.globals.update(get_flashed_messages=flash)
app.jinja_env.loader.mapping['base.html'] = BASE_TEMPLATE

if __name__ == '__main__':
    # Check if MVola client is initialized
    if not client:
        print("WARNING: MVola client failed to initialize. Please check your configuration.")
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    
    print(f"MVola Payment Demo running at http://localhost:{port}")
    print("For sandbox testing, use the following test phone numbers:")
    print("- Customer: 0343500003")
    print("- Merchant: 0343500004")
    
    app.run(host='0.0.0.0', port=port, debug=True)