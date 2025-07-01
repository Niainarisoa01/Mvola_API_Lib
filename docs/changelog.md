# Changelog

Toutes les modifications notables apportées à ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-06-30

### Ajouté
- Support du nouveau paramètre `scope=EXT_INT_MVOLA_SCOPE` pour l'authentification
- Support des nouveaux paramètres de transaction: `requestingOrganisationTransactionReference` et `originalTransactionReference`
- Nouvelle longueur maximale de 50 caractères pour la description des transactions

### Changé
- Migration des URLs d'API: 
  - Sandbox: `https://devapi.mvola.mg` (remplace pre-api.mvola.mg)
  - Production: `https://api.mvola.mg` (remplace api.mvola.mg)
- Mise à jour du client pour utiliser `base_url` au lieu de `sandbox`
- Renommage de la méthode `initiate_payment` en `initiate_merchant_payment`
- Mise à jour complète de la documentation pour refléter les changements d'API
- Amélioration de la gestion des erreurs avec les nouveaux formats de réponse standardisés
- Mise à jour du processus de vérification de statut pour utiliser `serverCorrelationId`

### Corrigé
- Format de la réponse de callback pour utiliser `transactionStatus` au lieu de `status`
- Méthode de callback modifiée pour utiliser PUT au lieu de POST

## [1.0.0] - 2024-07-24

### Ajouté
- Première version de la bibliothèque
- Module d'authentification avec gestion de tokens
- Module de transaction pour les paiements marchands
- Support des environnements sandbox et production
- Gestion complète des erreurs
- Documentation utilisateur et guide d'intégration
- Exemples d'utilisation

### Changé
- N/A (première version)

### Corrigé
- N/A (première version)

## [Non publié]

### Ajouté
- Structure initiale du projet
- Configuration de build avec pyproject.toml
- Framework de tests
- Documentation avec MkDocs 