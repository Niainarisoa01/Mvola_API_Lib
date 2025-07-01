# Architecture de la bibliothèque MVola API

Cette page explique l'architecture interne de la bibliothèque MVola API, sa conception, et les décisions prises lors de son développement.

## Vue d'ensemble de l'architecture

La bibliothèque MVola API est conçue selon un modèle à plusieurs couches :

```
+------------------------------------------+
|            MVolaClient                   |  <- Interface publique principale
+------------------------------------------+
          |                  |
          v                  v
+------------------+  +------------------+
|    MVolaAuth     |  | MVolaTransaction |  <- Modules spécialisés
+------------------+  +------------------+
          |                  |
          v                  v
+------------------------------------------+
|          Couche HTTP (requests)          |  <- Communication HTTP
+------------------------------------------+
          |
          v
+------------------------------------------+
|            API MVola (externe)           |  <- API externe
+------------------------------------------+
```

## Principes de conception

La bibliothèque a été conçue avec les principes suivants :

1. **Separation of Concerns (SoC)** - Chaque module a une responsabilité claire et distincte
2. **Interface intuitive** - API simple et facile à utiliser pour les développeurs
3. **Robustesse** - Gestion complète des erreurs et validation des données
4. **Flexibilité** - Support des environnements sandbox et production

## Composants principaux

### MVolaClient

Le client est le point d'entrée principal de la bibliothèque. Il :
- Coordonne les interactions entre les différents modules
- Fournit une interface simplifiée pour les opérations courantes
- Gère la journalisation et les paramètres globaux
- Configure les URLs pour les environnements sandbox (https://devapi.mvola.mg) et production (https://api.mvola.mg)

### MVolaAuth

Le module d'authentification :
- Gère la génération de tokens OAuth avec le scope `EXT_INT_MVOLA_SCOPE`
- Maintient l'état du token et gère son expiration
- Rafraîchit automatiquement le token lorsque nécessaire
- Gère les en-têtes d'authentification pour les appels API

### MVolaTransaction

Le module de transaction :
- Implémente les opérations de paiement marchand via l'endpoint `/mvola/mm/transactions/type/merchantpay/1.0.0/`
- Gère la validation des paramètres de transaction avec la nouvelle limite de 50 caractères pour la description
- Fournit des méthodes pour vérifier le statut des transactions via `serverCorrelationId`
- Récupère les détails des transactions avec une réponse structurée standardisée
- Prend en charge les nouveaux paramètres comme `requestingOrganisationTransactionReference` et `originalTransactionReference`

### Gestion des erreurs

Le système de gestion des erreurs utilise une hiérarchie d'exceptions :
- `MVolaError` - Classe de base pour toutes les erreurs
- `MVolaAuthError` - Erreurs liées à l'authentification
- `MVolaTransactionError` - Erreurs liées aux transactions
- `MVolaValidationError` - Erreurs de validation des paramètres
- `MVolaConnectionError` - Erreurs de connexion réseau

## Flux de données

1. **Authentification** :
   ```
   MVolaClient → MVolaAuth → API MVola → Token d'accès → Stocké dans MVolaAuth
   ```

2. **Initiation de paiement marchand** :
   ```
   MVolaClient → MVolaTransaction → Validation des paramètres → 
   MVolaTransaction demande token à MVolaAuth → 
   MVolaTransaction envoie requête à API MVola → 
   Résultat retourné à MVolaClient
   ```

3. **Vérification de statut** :
   ```
   MVolaClient → MVolaTransaction → 
   MVolaTransaction demande token à MVolaAuth → 
   MVolaTransaction envoie requête avec serverCorrelationId à API MVola → 
   Résultat retourné à MVolaClient
   ```

## Considérations de performances

- **Réutilisation des tokens** - Les tokens sont réutilisés jusqu'à leur expiration
- **Validation précoce** - Les paramètres sont validés avant d'envoyer des requêtes pour éviter des appels API inutiles
- **Journalisation configurable** - Permet d'ajuster le niveau de journalisation selon les besoins

## Sécurité

- **Pas de stockage persistant de credentials** - Les identifiants ne sont jamais écrits sur disque
- **Communication HTTPS** - Toutes les communications avec l'API MVola utilisent HTTPS
- **Validation des entrées** - Toutes les entrées utilisateur sont validées avant utilisation
- **Scope spécifique** - Utilisation du scope `EXT_INT_MVOLA_SCOPE` pour l'authentification

## Évolutivité

La bibliothèque est conçue pour évoluer facilement :
- Ajout de nouveaux endpoints API
- Support de nouvelles fonctionnalités MVola
- Extension à d'autres services de paiement mobile

## Défis techniques

Lors du développement, plusieurs défis ont été relevés :
- Gestion cohérente des erreurs provenant de l'API MVola
- Conception d'une API intuitive tout en exposant les fonctionnalités nécessaires
- Équilibre entre simplicité d'utilisation et flexibilité
- Adaptation aux changements d'API avec les nouveaux formats de réponse standardisés 