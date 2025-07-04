# Guide d'authentification

Ce guide vous explique comment configurer et gérer l'authentification avec l'API MVola en utilisant la bibliothèque MVola API.

## Obtenir les identifiants API

Avant de pouvoir vous authentifier auprès de l'API MVola, vous devez obtenir vos identifiants API (Consumer Key et Consumer Secret) :

1. Créez un compte sur le [Portail Développeur MVola](https://developer.mvola.mg/)
2. Créez une nouvelle application dans votre tableau de bord développeur
3. Notez votre `Consumer Key` et `Consumer Secret`

## Types d'environnements

MVola offre deux environnements distincts :

- **Sandbox** : Environnement de test et de développement
- **Production** : Environnement de production pour les applications en direct

### Différences entre les environnements

| Caractéristique | Sandbox | Production |
|-----------------|---------|------------|
| Transactions réelles | Non | Oui |
| Limites de transaction | Illimitées | Selon la réglementation |
| URL de base | https://devapi.mvola.mg | https://api.mvola.mg |
| Nécessite validation | Non | Oui |

## Configuration de l'authentification

### Méthode 1 : Initialisation directe

```python
from mvola_api import MVolaClient

# Initialisation pour l'environnement sandbox
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="Nom de votre application",
    partner_msisdn="0343500004",  # Votre numéro MVola (utiliser 0343500004 pour sandbox)
    sandbox=True  # Utiliser l'environnement sandbox
)

# Pour la production
client = MVolaClient(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    partner_name="Nom de votre application",
    partner_msisdn="votre_numero_mvola",  # Votre vrai numéro MVola
    sandbox=False  # Utiliser l'environnement de production
)
```

### Méthode 2 : Utilisation des variables d'environnement (Recommandée)

Pour une meilleure sécurité, nous recommandons d'utiliser des variables d'environnement pour stocker vos identifiants.

#### Étape 1 : Créer un fichier .env

Créez un fichier `.env` à la racine de votre projet :

```
# MVola API credentials
MVOLA_CONSUMER_KEY=votre_consumer_key
MVOLA_CONSUMER_SECRET=votre_consumer_secret

# MVola API configuration
MVOLA_PARTNER_NAME=Nom de votre application
MVOLA_PARTNER_MSISDN=0343500004

# Environment (True pour sandbox, False pour production)
MVOLA_SANDBOX=True
```

#### Étape 2 : Utiliser MVolaClient.from_env()

```python
from mvola_api import MVolaClient
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Initialisation complète à partir des variables d'environnement
client = MVolaClient.from_env()

# Le client est maintenant prêt à être utilisé
token_data = client.generate_token()
print(f"Token généré avec succès, expire dans {token_data['expires_in']} secondes")
```

#### Étape 3 (optionnelle) : Surcharger certaines variables d'environnement

Vous pouvez également surcharger certaines variables d'environnement tout en utilisant les autres :

```python
from mvola_api import MVolaClient
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Utiliser les credentials des variables d'environnement mais personnaliser d'autres paramètres
client = MVolaClient(
    # Ces valeurs seront chargées depuis les variables d'environnement
    consumer_key=None,  # None indique d'utiliser la variable d'environnement
    consumer_secret=None,  # None indique d'utiliser la variable d'environnement
    
    # Ces valeurs vont surcharger celles des variables d'environnement
    partner_name="Nom personnalisé",
    sandbox=False  # Forcer l'utilisation de l'environnement de production
)
```

### Variables d'environnement supportées

| Variable d'environnement | Description | Valeur par défaut |
|--------------------------|-------------|-----------------|
| MVOLA_CONSUMER_KEY       | Votre Consumer Key obtenue du portail développeur | Aucune (obligatoire) |
| MVOLA_CONSUMER_SECRET    | Votre Consumer Secret obtenue du portail développeur | Aucune (obligatoire) |
| MVOLA_PARTNER_NAME       | Le nom de votre entreprise/application | Aucune (obligatoire) |
| MVOLA_PARTNER_MSISDN     | Votre numéro MVola | 0343500004 pour sandbox |
| MVOLA_SANDBOX            | "True" pour l'environnement sandbox, "False" pour la production | True |

## Processus d'authentification

L'authentification MVola utilise le protocole OAuth 2.0 avec le flux `client_credentials` et le scope `EXT_INT_MVOLA_SCOPE`. Voici comment cela fonctionne :

1. La bibliothèque MVola API envoie une requête à l'endpoint `/token` avec :
   - Un en-tête `Authorization: Basic` contenant vos credentials encodés en Base64
   - Des données de formulaire contenant `grant_type=client_credentials` et `scope=EXT_INT_MVOLA_SCOPE`

2. Le serveur MVola répond avec un token d'accès :
   ```json
   {
     "access_token": "<ACCESS_TOKEN>",
     "scope": "EXT_INT_MVOLA_SCOPE",
     "token_type": "Bearer",
     "expires_in": 3600
   }
   ```

3. Ce token est ensuite utilisé pour authentifier toutes les requêtes suivantes à l'API MVola.

## Gestion des tokens

### Comment la bibliothèque gère les tokens

La bibliothèque MVola API gère automatiquement les tokens d'authentification pour vous :

1. La première fois que vous effectuez une opération, un token est généré
2. Ce token est stocké en mémoire
3. Pour les opérations suivantes, le token existant est utilisé
4. Si le token est expiré, un nouveau token est généré automatiquement

Vous n'avez généralement pas besoin de manipuler les tokens directement.

### Cycle de vie des tokens

```python
# Le token est généré automatiquement lors de la première utilisation
transaction_info = client.initiate_payment(...)

# Pour générer manuellement un token
token_data = client.generate_token()
print(f"Token: {token_data['access_token'][:20]}...") # Ne jamais afficher le token complet
print(f"Expire dans: {token_data['expires_in']} secondes")

# Forcer le rafraîchissement du token
token_data = client.generate_token(force_refresh=True)
```

## Gestion des erreurs d'authentification

Les erreurs d'authentification sont gérées par des exceptions spécifiques :

```python
from mvola_api import MVolaClient
from mvola_api.exceptions import MVolaAuthError, MVolaError

try:
    client = MVolaClient.from_env()
    
    # Une opération qui nécessite une authentification
    client.initiate_payment(
        amount="1000",
        debit_msisdn="0343500003",
        credit_msisdn="0343500004",
        description="Paiement test"
    )
except MVolaAuthError as e:
    print(f"Erreur d'authentification: {e}")
    # Vérifiez vos consumer_key et consumer_secret
except MVolaError as e:
    print(f"Erreur MVola: {e}")
    # Gérer les autres erreurs
```

## Codes d'erreur HTTP

L'API MVola utilise les codes d'erreur HTTP standard pour indiquer le résultat des requêtes d'authentification :

| Code | Description |
|------|-------------|
| 200 | OK - La requête a réussi |
| 400 | Bad Request - Requête incorrecte, souvent en raison d'un paramètre manquant |
| 401 | Unauthorized - Clé API invalide fournie |
| 402 | Request Failed - Les paramètres sont valides mais la requête a échoué |
| 403 | Forbidden - La clé API n'a pas les permissions nécessaires |
| 404 | Not Found - La ressource demandée n'existe pas |
| 409 | Conflict - La requête est en conflit avec une autre requête |
| 429 | Too Many Requests - Trop de requêtes envoyées à l'API trop rapidement |
| 500, 502, 503, 504 | Server Errors - Erreur au niveau du serveur |

## Bonnes pratiques de sécurité

1. **Utilisez des variables d'environnement** - Préférez `MVolaClient.from_env()` plutôt que les identifiants en dur
2. **Créez un fichier `.env.example`** - Fournissez un modèle sans les vraies credentials
3. **Ajoutez `.env` à votre .gitignore** - Pour éviter que vos credentials ne soient versionnées
4. **Ne partagez jamais vos identifiants API** - Chaque application doit avoir ses propres identifiants
5. **Utilisez HTTPS pour toutes les communications** - La bibliothèque MVola API le fait automatiquement
6. **Journalisez les tentatives d'authentification échouées** pour détecter les abus potentiels

## Passage en production

Lorsque vous êtes prêt à passer en production :

1. Suivez le processus "GO LIVE" sur le portail développeur MVola
2. Obtenez des identifiants API de production auprès de MVola
3. Mettez à jour votre fichier `.env` avec les identifiants de production
4. Définissez `MVOLA_SANDBOX=False` dans votre `.env` ou utilisez `sandbox=False` dans le constructeur
5. Effectuez des tests avec des montants minimes avant de manipuler des transactions plus importantes

## Prochaines étapes

Une fois l'authentification configurée, vous pouvez commencer à effectuer des transactions. Consultez le [Guide des transactions](transactions.md) pour apprendre à initier des paiements et à vérifier leur statut. 