# Intégration Web

Ce guide explique comment intégrer la bibliothèque MVola API dans une application web en utilisant Flask comme exemple.

## Configuration du projet

Avant de commencer, assurez-vous d'avoir installé la bibliothèque MVola API ainsi que Flask :

```bash
 pip install mvola-api-lib | flask python-dotenv
```

## Structure du projet

Voici une structure de projet recommandée pour une application web Flask avec MVola :

```
mvola-web-app/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── payment_controller.py
│   │   └── webhook_controller.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── mvola_service.py
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       ├── base.html
│       ├── index.html
│       └── payment.html
│
├── .env
├── requirements.txt
└── run.py
```

## Configuration de l'application

Commençons par configurer l'application Flask.

**app/config.py**:

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Configuration MVola
    MVOLA_CONSUMER_KEY = os.environ.get('MVOLA_CONSUMER_KEY')
    MVOLA_CONSUMER_SECRET = os.environ.get('MVOLA_CONSUMER_SECRET')
    MVOLA_PARTNER_NAME = os.environ.get('MVOLA_PARTNER_NAME')
    MVOLA_PARTNER_MSISDN = os.environ.get('MVOLA_PARTNER_MSISDN')
    MVOLA_BASE_URL = os.environ.get('MVOLA_BASE_URL', 'https://devapi.mvola.mg')
    
    # URL pour les webhooks (url publique)
    WEBHOOK_BASE_URL = os.environ.get('WEBHOOK_BASE_URL', 'https://example.com')
```

**app/__init__.py**:

```python
from flask import Flask
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enregistrement des blueprints
    from app.controllers.payment_controller import payment_bp
    from app.controllers.webhook_controller import webhook_bp
    
    app.register_blueprint(payment_bp)
    app.register_blueprint(webhook_bp)
    
    return app
```

## Service MVola

Créons un service qui encapsule notre logique d'interaction avec MVola.

**app/services/mvola_service.py**:

```python
import uuid
import logging
from mvola_api import MVolaClient
from mvola_api.exceptions import MVolaError, MVolaAuthError, MVolaTransactionError

class MVolaService:
    def __init__(self, config):
        self.logger = logging.getLogger('mvola_service')
        
        self.client = MVolaClient(
            consumer_key=config['MVOLA_CONSUMER_KEY'],
            consumer_secret=config['MVOLA_CONSUMER_SECRET'],
            partner_name=config['MVOLA_PARTNER_NAME'],
            partner_msisdn=config['MVOLA_PARTNER_MSISDN'],
            base_url=config['MVOLA_BASE_URL']
        )
        
        self.webhook_base_url = config['WEBHOOK_BASE_URL']
    
    def generate_reference(self):
        """Génère une référence unique pour une transaction."""
        return f"WEB-{uuid.uuid4().hex[:12].upper()}"
    
    def initiate_payment(self, amount, debit_msisdn, description, order_id=None):
        """
        Initie un paiement MVola.
        
        Args:
            amount (str): Le montant à payer (en chaîne de caractères)
            debit_msisdn (str): Le MSISDN du client qui paie
            description (str): Description du paiement (max 50 caractères)
            order_id (str, optional): Identifiant de commande pour le callback
        
        Returns:
            dict: Les informations de la transaction
        """
        reference = self.generate_reference()
        
        # Construire l'URL de callback avec l'ID de commande si fourni
        callback_url = f"{self.webhook_base_url}/webhooks/mvola/callback"
        if order_id:
            callback_url = f"{callback_url}?order_id={order_id}"
        
        try:
            self.logger.info(f"Initiation de paiement: {amount} Ar depuis {debit_msisdn}")
            
            transaction_info = self.client.initiate_merchant_payment(
                amount=amount,
                debit_msisdn=debit_msisdn,
                credit_msisdn=self.client.partner_msisdn,
                description=description,
                requesting_organisation_transaction_reference=reference,
                callback_url=callback_url
            )
            
            server_correlation_id = transaction_info['response']['serverCorrelationId']
            self.logger.info(f"Paiement initié avec succès. ID: {server_correlation_id}")
            
            # Stocker les infos de transaction avec l'ID de commande pour le suivi
            return {
                'server_correlation_id': server_correlation_id,
                'reference': reference,
                'amount': amount,
                'debit_msisdn': debit_msisdn,
                'status': 'pending',
                'order_id': order_id
            }
            
        except MVolaError as e:
            self.logger.error(f"Erreur lors de l'initiation du paiement: {e}")
            raise
    
    def check_transaction_status(self, server_correlation_id):
        """Vérifie le statut d'une transaction."""
        try:
            status_info = self.client.get_transaction_status(
                server_correlation_id=server_correlation_id
            )
            
            return status_info['response']
            
        except MVolaError as e:
            self.logger.error(f"Erreur lors de la vérification du statut: {e}")
            raise
    
    def get_transaction_details(self, transaction_id):
        """Récupère les détails d'une transaction complétée."""
        try:
            details = self.client.get_transaction_details(
                transaction_id=transaction_id
            )
            
            return details['response']
            
        except MVolaError as e:
            self.logger.error(f"Erreur lors de la récupération des détails: {e}")
            raise

## Contrôleur de paiement

Créons le contrôleur qui gère les routes pour l'interface utilisateur et le traitement des paiements.

**app/controllers/payment_controller.py**:

```python
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash, session
from app.services.mvola_service import MVolaService
from mvola_api.exceptions import MVolaError, MVolaValidationError

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/')
def index():
    """Page d'accueil avec formulaire de paiement."""
    return render_template('index.html')

@payment_bp.route('/pay', methods=['POST'])
def process_payment():
    """Traite une demande de paiement."""
    form_data = request.form
    
    # Validation des données
    if not form_data.get('amount') or not form_data.get('phone'):
        flash('Veuillez fournir un montant et un numéro de téléphone', 'danger')
        return redirect(url_for('payment.index'))
    
    try:
        # Initialiser le service MVola
        mvola_service = MVolaService(current_app.config)
        
        # Générer un ID de commande unique
        order_id = str(uuid.uuid4())
        
        # Stocker les informations de commande dans la session
        session['order'] = {
            'id': order_id,
            'amount': form_data.get('amount'),
            'phone': form_data.get('phone'),
            'description': form_data.get('description', 'Paiement en ligne'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Initier le paiement
        transaction = mvola_service.initiate_payment(
            amount=form_data.get('amount'),
            debit_msisdn=form_data.get('phone'),
            description=form_data.get('description', 'Paiement en ligne'),
            order_id=order_id
        )
        
        # Stocker l'ID de corrélation pour le suivi
        session['server_correlation_id'] = transaction['server_correlation_id']
        
        # Rediriger vers la page de statut
        return redirect(url_for('payment.payment_status', order_id=order_id))
        
    except MVolaValidationError as e:
        flash(f'Erreur de validation: {e}', 'danger')
        return redirect(url_for('payment.index'))
    except MVolaError as e:
        flash(f'Erreur MVola: {e}', 'danger')
        return redirect(url_for('payment.index'))
    except Exception as e:
        flash(f'Erreur inattendue: {e}', 'danger')
        return redirect(url_for('payment.index'))

@payment_bp.route('/status/<order_id>')
def payment_status(order_id):
    """Page de statut de paiement avec rafraîchissement automatique."""
    
    # Vérifier si la commande existe dans la session
    if 'order' not in session or session['order']['id'] != order_id:
        flash('Commande introuvable', 'danger')
        return redirect(url_for('payment.index'))
    
    order = session['order']
    server_correlation_id = session.get('server_correlation_id')
    
    # Si pas d'ID de corrélation, impossible de vérifier le statut
    if not server_correlation_id:
        flash('Impossible de vérifier le statut du paiement', 'danger')
        return redirect(url_for('payment.index'))
    
    try:
        # Vérifier le statut actuel
        mvola_service = MVolaService(current_app.config)
        status_info = mvola_service.check_transaction_status(server_correlation_id)
        
        status = status_info.get('status')
        
        # Si la transaction est complétée, récupérer les détails
        transaction_details = None
        if status == 'completed' and 'objectReference' in status_info:
            transaction_id = status_info['objectReference']
            transaction_details = mvola_service.get_transaction_details(transaction_id)
        
        return render_template(
            'payment_status.html',
            order=order,
            server_correlation_id=server_correlation_id,
            status=status,
            transaction_details=transaction_details
        )
        
    except Exception as e:
        flash(f'Erreur lors de la vérification du statut: {e}', 'danger')
        return redirect(url_for('payment.index'))
```

## Contrôleur de webhook

Créons le contrôleur pour gérer les webhooks de MVola.

**app/controllers/webhook_controller.py**:

```python
import logging
from flask import Blueprint, request, jsonify, current_app

webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhooks')
logger = logging.getLogger('webhook_controller')

@webhook_bp.route('/mvola/callback', methods=['PUT'])
def mvola_callback():
    """
    Endpoint pour recevoir les notifications de MVola.
    MVola envoie les notifications de statut à cet endpoint.
    """
    webhook_data = request.get_json()
    
    if not webhook_data:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
    
    # Log des données reçues
    current_app.logger.info(f"Webhook MVola reçu: {json.dumps(webhook_data)}")
    
    # Extraire les informations importantes
    server_correlation_id = webhook_data.get('serverCorrelationId')
    transaction_status = webhook_data.get('transactionStatus')
    transaction_reference = webhook_data.get('transactionReference')
    
    if not server_correlation_id or not transaction_status:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    # Récupérer l'ID de commande depuis les paramètres de la requête
    order_id = request.args.get('order_id')
    
    # Mettre à jour le statut de la commande dans la base de données
    update_order_status(order_id, transaction_status, transaction_reference, webhook_data)
    
    # Renvoyer un succès pour indiquer que la notification a été reçue
    return jsonify({'status': 'success'}), 200
```

## Templates

Créons les templates de base pour notre application.

**app/templates/base.html**:

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MVola Payment Demo{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <header>
        <h1>MVola Payment Demo</h1>
        <nav>
            <ul>
                <li><a href="{{ url_for('payment.index') }}">Accueil</a></li>
                <li><a href="{{ url_for('payment.payment') }}">Paiement</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flashes">
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; {% now "Y" %} MVola API Demo</p>
    </footer>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

**app/templates/index.html**:

```html
{% extends "base.html" %}

{% block title %}Accueil - MVola Payment Demo{% endblock %}

{% block content %}
<section class="hero">
    <h2>Paiements faciles avec MVola API</h2>
    <p>Découvrez comment intégrer MVola dans votre application web</p>
    <a href="{{ url_for('payment.payment') }}" class="btn btn-primary">Essayer maintenant</a>
</section>

<section class="features">
    <div class="feature">
        <h3>Simple</h3>
        <p>Intégration facile avec la bibliothèque MVola API</p>
    </div>
    <div class="feature">
        <h3>Sécurisé</h3>
        <p>Transactions sécurisées avec validation</p>
    </div>
    <div class="feature">
        <h3>Rapide</h3>
        <p>Paiements instantanés avec notifications</p>
    </div>
</section>
{% endblock %}
```

**app/templates/payment.html**:

```html
{% extends "base.html" %}

{% block title %}Paiement - MVola Payment Demo{% endblock %}

{% block content %}
<section class="payment-form">
    <h2>Effectuer un paiement</h2>
    
    <form method="POST" action="{{ url_for('payment.payment') }}">
        <div class="form-group">
            <label for="amount">Montant (Ar)</label>
            <input type="number" id="amount" name="amount" min="100" step="100" 
                   value="{{ form_data.amount if form_data else 1000 }}" required>
        </div>
        
        <div class="form-group">
            <label for="phone_number">Numéro de téléphone</label>
            <input type="text" id="phone_number" name="phone_number" 
                   placeholder="0343500003" 
                   value="{{ form_data.phone_number if form_data else '' }}" required>
            <small>Format: 034XXXXXXX ou 038XXXXXXX</small>
        </div>
        
        <div class="form-group">
            <label for="description">Description</label>
            <input type="text" id="description" name="description" 
                   value="{{ form_data.description if form_data else 'Achat en ligne' }}">
        </div>
        
        <div class="form-actions">
            <button type="submit" class="btn btn-primary">Payer maintenant</button>
        </div>
    </form>
</section>
{% endblock %}
```

**app/templates/status.html**:

```html
{% extends "base.html" %}

{% block title %}Statut du paiement - MVola Payment Demo{% endblock %}

{% block content %}
<section class="payment-status">
    <h2>Statut du paiement</h2>
    
    <div class="status-card">
        <p>ID de transaction: <strong>{{ transaction_id }}</strong></p>
        
        {% if status_info %}
            <div class="status-info">
                <p>Statut: <strong>{{ status_info.get('status', 'Inconnu') }}</strong></p>
                <p>Date: {{ status_info.get('date', 'N/A') }}</p>
                {% if status_info.get('status', '').lower() == 'completed' %}
                    <div class="success-message">
                        <p>Paiement réussi!</p>
                    </div>
                {% elif status_info.get('status', '').lower() in ['failed', 'rejected', 'cancelled'] %}
                    <div class="error-message">
                        <p>Le paiement a échoué</p>
                    </div>
                {% else %}
                    <div class="pending-message">
                        <p>Paiement en attente</p>
                        <p>Veuillez confirmer sur votre téléphone</p>
                    </div>
                {% endif %}
            </div>
        {% else %}
            <p>En attente de confirmation...</p>
        {% endif %}
        
        <div class="status-actions">
            <a href="{{ url_for('payment.status', check=1) }}" class="btn btn-secondary">Vérifier le statut</a>
            <a href="{{ url_for('payment.index') }}" class="btn btn-link">Retour à l'accueil</a>
        </div>
    </div>
</section>
{% endblock %}

{% block scripts %}
<script>
    // Vérifier automatiquement le statut toutes les 5 secondes
    {% if not status_info or status_info.get('status', '').lower() not in ['completed', 'failed', 'rejected', 'cancelled'] %}
    const checkInterval = 5000; // 5 secondes
    
    function checkStatus() {
        window.location.href = "{{ url_for('payment.status', check=1) }}";
    }
    
    // Définir un timeout pour vérifier le statut
    setTimeout(checkStatus, checkInterval);
    {% endif %}
</script>
{% endblock %}
```

## Point d'entrée de l'application

Créons le point d'entrée principal de l'application.

**run.py**:

```python
import os
import logging
from app import create_app

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Création de l'application
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
```

## Fichier d'environnement

Créez un fichier `.env` à la racine du projet avec les configurations nécessaires :

```
SECRET_KEY=votre_secret_key_generee_aleatoirement
MVOLA_CONSUMER_KEY=votre_consumer_key
MVOLA_CONSUMER_SECRET=votre_consumer_secret
MVOLA_PARTNER_NAME=NOM_DU_PARTENAIRE
MVOLA_PARTNER_MSISDN=0343500003
MVOLA_BASE_URL=https://devapi.mvola.mg
WEBHOOK_BASE_URL=https://votre-domaine.com
```

> **Note**: Pour les tests en développement local, vous pouvez utiliser un service comme ngrok pour créer un tunnel vers votre localhost et obtenir une URL publique temporaire pour les webhooks.

## Dépendances du projet

Créez un fichier `requirements.txt` à la racine du projet :

```
flask==2.0.1
python-dotenv==0.19.0
mvola-api==1.0.0
gunicorn==21.0.0
```

## Lancement de l'application

Pour lancer l'application en développement :

```bash
python run.py
```

Pour le déploiement en production, utilisez un serveur WSGI comme Gunicorn :

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## Tests et débogage

### Test des webhooks en local

Pour tester les webhooks en développement local, vous pouvez utiliser ngrok :

```bash
# Installation de ngrok (si ce n'est pas déjà fait)
pip install pyngrok

# Dans un terminal séparé, lancez ngrok
ngrok http 5000
```

Utilisez l'URL fournie par ngrok comme valeur pour `WEBHOOK_BASE_URL` dans votre fichier `.env`.

### Simulations de paiement

Vous pouvez simuler des paiements en utilisant l'environnement sandbox de MVola. Dans cet environnement, les transactions sont simulées sans mouvement d'argent réel.

## Conclusion

Cette intégration web montre comment :

1. Initialiser la bibliothèque MVola API dans une application Flask
2. Créer un formulaire de paiement pour les utilisateurs
3. Gérer le flux de paiement complet
4. Recevoir et traiter les notifications via webhooks

Vous pouvez adapter ce code à votre framework web préféré en suivant les mêmes principes.

## Prochaines étapes

Pour compléter votre intégration, consultez:

- [Guide de gestion des webhooks](webhook-handling.md) pour plus de détails sur les notifications
- [Gestion des erreurs](../guides/error-handling.md) pour une meilleure gestion des cas d'erreur 