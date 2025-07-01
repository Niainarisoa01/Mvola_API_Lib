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
    base_url="https://devapi.mvola.mg"  # URL de l'API (sandbox par défaut)
)
```

### Génération d'un token

```python
# Générer un nouveau token
auth_token = auth.generate_token()

# Le token est un dictionnaire contenant:
# - access_token: Le token d'accès à utiliser dans les requêtes
# - token_type: Le type de token (généralement "Bearer")
# - expires_in: Durée de validité du token en secondes (3600 secondes = 1 heure)
# - scope: Le scope du token (EXT_INT_MVOLA_SCOPE)

print(f"Token d'accès: {auth_token['access_token']}")
print(f"Expire dans: {auth_token['expires_in']} secondes")
print(f"Type de token: {auth_token['token_type']}")
print(f"Scope: {auth_token['scope']}")
```

### Obtention d'un token d'accès

```python
# Obtenir uniquement la chaîne du token d'accès
access_token = auth.get_access_token()

# Cette méthode génère un nouveau token si nécessaire
# ou retourne le token existant s'il est encore valide

# Forcer le rafraîchissement du token, même s'il est encore valide
access_token = auth.get_access_token(force_refresh=True)
```

## Exceptions d'authentification

Le module d'authentification peut lever les exceptions suivantes :

- `MVolaAuthError`: Exception de base pour les erreurs d'authentification
  - Inclut des informations comme le code HTTP, le message d'erreur et la réponse complète

```python
from mvola_api.exceptions import MVolaAuthError

try:
    token = auth.generate_token()
except MVolaAuthError as e:
    print(f"Code d'erreur HTTP: {e.code}")
    print(f"Message d'erreur: {e.message}")
    print(f"Réponse complète: {e.response}")
```

## Fonctionnement interne

### Endpoints d'authentification

Le module utilise différents endpoints en fonction de l'environnement:

- **Sandbox**: `https://devapi.mvola.mg/token`
- **Production**: `https://api.mvola.mg/token`

### Format de la requête d'authentification

```python
# Requête POST avec les paramètres suivants:
headers = {
    "Authorization": "Basic {credentials_b64}",  # Base64(consumer_key:consumer_secret)
    "Content-Type": "application/x-www-form-urlencoded",
    "Cache-Control": "no-cache"
}

data = {
    "grant_type": "client_credentials",
    "scope": "EXT_INT_MVOLA_SCOPE"
}
```

### Format de la réponse

En cas de succès, la réponse contient:

```json
{
    "access_token": "<ACCESS_TOKEN>",
    "scope": "EXT_INT_MVOLA_SCOPE",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

En cas d'échec, la réponse peut contenir:

```json
{
    "ErrorCategory": "Error category",
    "ErrorCode": "Error Code",
    "ErrorDescription": "description on the error",
    "ErrorDateTime": "Date and time when the error occurred",
    "ErrorParameters": "Key/value which add more details on the nature of the error"
}
```

### Stockage du token

Le token est stocké en mémoire, dans l'instance de la classe `MVolaAuth`. Il n'est pas persistant entre les redémarrages de l'application. Si vous avez besoin de persistance, vous devez implémenter votre propre mécanisme de stockage.

## Codes d'erreur HTTP

L'API utilise les codes d'erreur HTTP standard:

- **200 - OK**: Tout a fonctionné comme prévu.
- **400 - Bad Request**: La requête est inacceptable, souvent en raison d'un paramètre manquant.
- **401 - Unauthorized**: Aucune clé API valide fournie.
- **402 - Request Failed**: Les paramètres étaient valides mais la requête a échoué.
- **403 - Forbidden**: La clé API n'a pas les permissions pour effectuer la requête.
- **404 - Not Found**: La ressource demandée n'existe pas.
- **409 - Conflict**: La requête est en conflit avec une autre requête.
- **429 - Too Many Requests**: Trop de requêtes envoyées à l'API trop rapidement.
- **500, 502, 503, 504 - Server Errors**: Une erreur s'est produite sur le serveur.

## Bonnes pratiques

1. **Sécurité**: Ne stockez jamais les clés d'API (consumer_key, consumer_secret) directement dans le code. Utilisez des variables d'environnement ou un système de gestion de secrets.

2. **Gestion des tokens**: Laissez la bibliothèque gérer automatiquement les tokens avec `get_access_token()` plutôt que de les gérer manuellement.

3. **Environnement de test**: Commencez toujours par l'environnement sandbox (`https://devapi.mvola.mg`) avant de passer à la production.

4. **Gestion des erreurs**: Implémentez une gestion d'erreurs robuste autour des appels d'authentification, car ils peuvent échouer pour diverses raisons (réseau, identifiants invalides, etc.).

5. **Backoff exponentiel**: En cas d'erreur 429 (trop de requêtes), implémentez un délai exponentiel entre les tentatives.

## Voir aussi

- [Guide d'authentification](../guides/authentication.md) - Guide complet sur l'authentification avec MVola
- [Référence MVolaClient](client.md) - Documentation de la classe principale qui utilise MVolaAuth
- [Gestion des erreurs](../guides/error-handling.md) - Comment gérer les erreurs d'authentification