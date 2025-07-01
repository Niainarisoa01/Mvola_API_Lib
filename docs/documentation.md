 # Documentation de l'API MVola

## Introduction

Cette documentation décrit l'intégration des services de paiement mobile MVola dans vos applications. MVola est un service de paiement mobile opéré par Telma Madagascar permettant aux entreprises de recevoir des paiements électroniques.

## Table des matières

1. [Portail développeur MVola](#portail)
2. [Configuration de l'API](#configuration)
3. [API d'authentification](#authentification)
4. [API de paiement marchand](#paiement)
5. [Codes d'erreur](#erreurs)
6. [Environnement de test](#test)
7. [Bonnes pratiques](#pratiques)

## Portail

### Création de compte et connexion

1. Accédez au portail MVola Developer et cliquez sur "Connectez-vous".
2. Pour créer un compte:
   - Saisissez une adresse email valide
   - Remplissez vos informations personnelles
   - Acceptez les conditions d'utilisation
   - Confirmez via le lien envoyé par email

### Déclaration d'application

1. Une fois connecté, déclarez votre application.
2. Fournissez des informations précises et complètes.
3. Attendez la validation par l'équipe MVola.

### Abonnement aux API

1. Après validation de votre application, accédez à l'onglet "Subscriptions".
2. Abonnez-vous aux API MVola pour recevoir vos clés d'accès.
3. Un email de confirmation vous sera envoyé.

## Configuration

### Environnements disponibles

| Environnement | Base URL                |
|---------------|-------------------------|
| Sandbox       | https://devapi.mvola.mg |
| Production    | https://api.mvola.mg    |

### Obtention des clés API

1. Dans la section "SUBSCRIPTIONS", cliquez sur "SANDBOX KEYS".
2. Décochez tous les "grant types" sauf "Client Credentials".
3. Vous obtiendrez votre Consumer Key et Consumer Secret.

### Configuration de l'environnement

Pour passer en production:
1. Cliquez sur "GO LIVE" dans le portail développeur.
2. Suivez les étapes de validation.
3. Utilisez les clés de production une fois approuvées.

## Authentification

### Endpoints

| Environnement | Méthode | URL                           |
|---------------|---------|-------------------------------|
| Sandbox       | POST    | https://devapi.mvola.mg/token |
| Production    | POST    | https://api.mvola.mg/token    |

### En-têtes requis

| Clé            | Valeur                                     |
|----------------|-------------------------------------------|
| Authorization  | Basic Base64(consumer-key:consumer-secret) |
| Content-Type   | application/x-www-form-urlencoded          |
| Cache-Control  | no-cache                                   |

### Corps de la requête

| Paramètre  | Valeur                |
|------------|----------------------|
| grant_type | client_credentials   |
| scope      | EXT_INT_MVOLA_SCOPE  |

### Exemple de requête

```bash
curl --location --request POST 'https://devapi.mvola.mg/token' \
--header 'Authorization: Basic Base64(consumer-key:consumer-secret)' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--header 'Cache-Control: no-cache' \
--data-urlencode 'grant_type=client_credentials' \
--data-urlencode 'scope=EXT_INT_MVOLA_SCOPE'
```

### Réponse en cas de succès (200)

```json
{
  "access_token": "<ACCESS_TOKEN>",
  "scope": "EXT_INT_MVOLA_SCOPE",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Notes:
- Le token expire après 3600 secondes (1 heure)
- L'encodage Base64 utilise le format `consumer-key:consumer-secret` avec un deux-points (:)

## Paiement

### Endpoints

| Ressource                | Méthode | URL Sandbox                                                             | URL Production                                                       |
|--------------------------|---------|------------------------------------------------------------------------|----------------------------------------------------------------------|
| Initier une transaction  | POST    | https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/   | https://api.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/   |
| Détails de transaction   | GET     | https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/{transID} | https://api.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/{transID} |
| Statut de transaction    | GET     | https://devapi.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/status/{serverCorrelationId} | https://api.mvola.mg/mvola/mm/transactions/type/merchantpay/1.0.0/status/{serverCorrelationId} |

### En-têtes communs

| Clé                   | Valeur                                |
|-----------------------|--------------------------------------|
| Authorization         | Bearer <ACCESS_TOKEN>                 |
| Version               | 1.0                                   |
| X-CorrelationID       | ID unique (ex: UUID)                  |
| UserLanguage          | FR (Français) ou MG (Malgache)        |
| UserAccountIdentifier | msisdn;{numéro} (ex: msisdn;0340017983) |
| partnerName           | Nom de votre entreprise               |
| Content-Type          | application/json                      |
| Cache-Control         | no-cache                              |

### Initier une transaction (POST)

En-têtes additionnels:
- `X-Callback-URL`: URL pour notifications (optionnel)

Corps de la requête:
```json
{  
  "amount": "10000",  
  "currency": "Ar",  
  "descriptionText": "Paiement Marchand",  
  "requestDate": "2023-10-05T14:30:00.000Z",  
  "debitParty": [{"key": "msisdn", "value": "0340017983"}],  
  "creditParty": [{"key": "msisdn", "value": "0340017984"}],  
  "metadata": [  
    {"key": "partnerName", "value": "MonEntreprise"},  
    {"key": "fc", "value": "USD"},  
    {"key": "amountFc", "value": "10"}  
  ]  
}
```

Réponse (succès):
```json
{  
  "status": "pending",  
  "serverCorrelationId": "421a22a2-effd-42bc-9452-f4939a3d5cdf",  
  "notificationMethod": "callback"  
}
```

### Obtenir les détails d'une transaction (GET)

Requête:
```bash
GET /mvola/mm/transactions/type/merchantpay/1.0.0/{transID}
```

Réponse (succès):
```json
{  
  "amount": "10000",  
  "currency": "Ar",  
  "transactionReference": "123456",  
  "transactionStatus": "completed",  
  "debitParty": [{"key": "msisdn", "value": "0340017983"}],  
  "creditParty": [{"key": "msisdn", "value": "0340017984"}]  
}
```

### Vérifier le statut d'une transaction (GET)

Requête:
```bash
GET /mvola/mm/transactions/type/merchantpay/1.0.0/status/{serverCorrelationId}
```

Réponse (succès):
```json
{  
  "status": "completed",  
  "serverCorrelationId": "421a22a2-effd-42bc-9452-f4939a3d5cdf",  
  "notificationMethod": "polling",  
  "objectReference": "123456"  
}
```

## Erreurs

### Codes HTTP

| Code | Signification |
|------|---------------|
| 200  | OK – Requête réussie |
| 400  | Paramètres manquants ou invalides |
| 401  | Authentification échouée / Token invalide |
| 402  | Échec métier (ex: solde insuffisant) |
| 403  | Droits insuffisants |
| 404  | Ressource introuvable |
| 409  | Conflit (ex: clé idempotente dupliquée) |
| 429  | Trop de requêtes |
| 5xx  | Erreur serveur |

### Format des erreurs

```json
{  
  "ErrorCategory": "Transaction",  
  "ErrorCode": "5001",  
  "ErrorDescription": "Solde insuffisant",  
  "ErrorDateTime": "2023-10-05T12:34:56Z",  
  "ErrorParameters": {"param": "value"}  
}
```

Erreur d'authentification:
```json
{  
  "fault": {  
    "code": 900901,  
    "message": "Invalid Credentials",  
    "description": "Invalid Credentials. Make sure you have given the correct access token."  
  }  
}
```

## Test

### Numéros de test disponibles

Pour l'environnement Sandbox, utilisez uniquement:
- 0343500003
- 0343500004

### Test des transactions

1. Dans le portail développeur MVola, section "TRY OUT":
   - Sélectionnez votre application
   - Générez une clé de test

2. Exécutez vos requêtes de test

3. Approuvez les transactions en attente via "Transaction Approvals"

## Pratiques

1. **Gestion des tokens**
   - Stockez le token de manière sécurisée
   - Intégrez un mécanisme de rafraîchissement automatique (avant expiration)

2. **Validation des paramètres**
   - Vérifiez les numéros de téléphone (format valide)
   - Évitez les caractères spéciaux dans les descriptions

3. **Dates et formats**
   - Format des dates: ISO 8601 (yyyy-MM-dd'T'HH:mm:ss.SSSZ)
   - Utilisez UTC pour éviter les problèmes de fuseau horaire

4. **Suivi des transactions**
   - Conservez le serverCorrelationId pour suivre les statuts
   - Implémentez un système de webhook pour les notifications

5. **Sécurité**
   - Utilisez HTTPS pour toutes les communications
   - Ne stockez jamais les credentials en clair
   - Implémentez une rotation régulière des clés d'API

---

## Support et assistance

Pour toute question technique, contactez MVola via le portail développeur ou à l'adresse support-api@mvola.mg. 