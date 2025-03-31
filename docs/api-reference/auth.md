# Référence du module d'authentification

Le module d'authentification `mvola_api.auth` gère l'authentification auprès de l'API MVola en utilisant OAuth 2.0. Il s'occupe de la génération, du stockage et du rafraîchissement des tokens d'accès.

## Classe MVolaAuth

La classe `MVolaAuth` est responsable de toutes les opérations liées à l'authentification auprès de l'API MVola.

### Initialisation

```python
from mvola_api.auth import MVolaAuth

auth = MVolaAuth(
    consumer_key="votre_consumer_key",
    consumer_secret="votre_consumer_secret",
    sandbox=True  # Utiliser False pour l'environnement de production
)
```

### Génération d'un token

```python
# Générer un nouveau token
auth_token = auth.generate_token()

# Le token est un dictionnaire contenant:
# - access_token: Le token d'accès à utiliser dans les requêtes
# - token_type: Le type de token (généralement "Bearer")
# - expires_in: Durée de validité du token en secondes
# - expires_at: Timestamp de l'expiration du token (ajouté par la bibliothèque)

print(f"Token d'accès: {auth_token['access_token']}")
print(f"Expire dans: {auth_token['expires_in']} secondes")
```

### Vérification et rafraîchissement automatique du token

```python
# Obtenir un token valide (génère un nouveau token si nécessaire)
token = auth.get_valid_token()

# Cette méthode vérifie si un token existe déjà et s'il est encore valide
# Si le token est expiré ou n'existe pas, un nouveau token est généré
```

### Utilisation manuelle du token

```python
# Vérifier si un token est expiré
is_expired = auth.is_token_expired()

# Rafraîchir manuellement le token
auth.refresh_token()

# Obtenir l'en-tête d'autorisation formaté pour les requêtes HTTP
auth_header = auth.get_auth_header()
# Retourne: {"Authorization": "Bearer votre_token_d_acces"}
```

## Exceptions d'authentification

Le module d'authentification peut lever les exceptions suivantes :

- `MVolaAuthError`: Exception de base pour les erreurs d'authentification
  - `MVolaInvalidCredentialsError`: Levée lorsque les identifiants (consumer_key, consumer_secret) sont invalides
  - `MVolaTokenExpiredError`: Levée lorsqu'un token a expiré et qu'une opération tente de l'utiliser

```python
from mvola_api.exceptions import MVolaAuthError, MVolaInvalidCredentialsError, MVolaTokenExpiredError

try:
    token = auth.generate_token()
except MVolaInvalidCredentialsError as e:
    print(f"Erreur d'identifiants: {e}")
except MVolaAuthError as e:
    print(f"Erreur d'authentification: {e}")
```

## Fonctionnement interne

### Endpoints d'authentification

Le module utilise différents endpoints en fonction de l'environnement:

- **Sandbox**: `https://api-uat.orange.mg/oauth/token`
- **Production**: `https://api.orange.mg/oauth/token`

### Format de la requête d'authentification

```python
# Requête POST avec les paramètres suivants:
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": "Basic {credentials_b64}"  # Base64(consumer_key:consumer_secret)
}

data = {
    "grant_type": "client_credentials"
}
```

### Stockage du token

Le token est stocké en mémoire, dans l'instance de la classe `MVolaAuth`. Il n'est pas persistant entre les redémarrages de l'application. Si vous avez besoin de persistance, vous devez implémenter votre propre mécanisme de stockage.

## Bonnes pratiques

1. **Sécurité**: Ne stockez jamais les clés d'API (consumer_key, consumer_secret) directement dans le code. Utilisez des variables d'environnement ou un système de gestion de secrets.

2. **Gestion des tokens**: Laissez la bibliothèque gérer automatiquement les tokens avec `get_valid_token()` plutôt que de les gérer manuellement.

3. **Environnement de test**: Commencez toujours par l'environnement sandbox (`sandbox=True`) avant de passer à la production.

4. **Gestion des erreurs**: Implémentez une gestion d'erreurs robuste autour des appels d'authentification, car ils peuvent échouer pour diverses raisons (réseau, identifiants invalides, etc.).

## Voir aussi

- [Guide d'authentification](../guides/authentication.md) - Guide complet sur l'authentification avec MVola
- [Référence MVolaClient](client.md) - Documentation de la classe principale qui utilise MVolaAuth
- [Gestion des erreurs](../guides/error-handling.md) - Comment gérer les erreurs d'authentification