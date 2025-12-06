# Changelog

Toutes les modifications notables apportées à ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.1] - 2025-12-07

### Ajouté
- Nouvelle méthode `is_token_valid()` dans `MVolaAuth` pour vérifier la validité du token
- Type hints complets dans tous les modules (`client.py`, `auth.py`, `transaction.py`)
- Constante `DEFAULT_TIMEOUT = 30` pour les requêtes HTTP
- Validation MSISDN avec `validate_msisdn()` dans les paramètres de transaction

### Modifié
- Timeout de 30 secondes ajouté à toutes les requêtes HTTP (prévention des blocages)
- Nettoyage des imports inutilisés dans `client.py`

### Corrigé
- Exports manquants dans `__init__.py` : `MVolaValidationError`, `MVolaConnectionError`
- Synchronisation de la version entre `__init__.py`, `pyproject.toml` et `setup.py`
- Documentation corrigée : paramètre `sandbox` au lieu de `base_url`

## [1.4.0] - 2025-07-04

### Ajouté
- Support des variables d'environnement pour stocker les credentials et la configuration
- Nouvelle méthode de classe `MVolaClient.from_env()` pour créer un client à partir des variables d'environnement
- Fichier `.env.example` pour faciliter la configuration
- Exemple `env_example.py` qui démontre l'utilisation des variables d'environnement
- Tests spécifiques pour valider la fonctionnalité des variables d'environnement

### Modifié
- MVolaClient accepte maintenant des paramètres optionnels, avec fallback vers les variables d'environnement
- Tests mis à jour pour utiliser les variables d'environnement
- Utilisation du langage "MG" par défaut pour améliorer la compatibilité
- La valeur par défaut pour `originalTransactionReference` est maintenant "MVOLA_123"
- Corrélation ID fixe "123" pour les tests de compatibilité

### Corrigé
- Format exact des en-têtes HTTP basé sur les exemples fonctionnels
- Correction du casse pour l'en-tête "version" (utilisation de la minuscule)
- Ajout de "Accept-Charset: utf-8" dans les en-têtes par défaut

## [1.3.0] - 2025-07-01

### Ajouté
- Ajout des champs obligatoires `fc` et `amountFc` par défaut dans les métadonnées de la requête de paiement
- Ajout d'une section "Known Limitations" dans le README pour documenter les problèmes avec l'API MVola
- Nouvel exemple `auth_example.py` qui démontre l'authentification qui fonctionne correctement

### Modifié
- Documentation améliorée sur les limitations de l'environnement sandbox MVola
- Meilleure gestion des erreurs dans l'initiation de paiement (reconnaissance de `errorDescription` et `ErrorDescription`)
- Les paramètres `foreign_currency` et `foreign_amount` ont désormais des valeurs par défaut (USD et 1)

### Corrigé
- Format des en-têtes HTTP pour correspondre exactement à la documentation MVola

## [1.2.0] - 2025-04-22

### Ajouté
- Support pour les callbacks (webhooks)
- Nouveau module d'exceptions pour une meilleure gestion des erreurs
- Documentation complète dans docs/
- Exemples d'intégration dans examples/

### Modifié
- Amélioration de la gestion des tokens d'authentification
- Refactoring pour une meilleure lisibilité et maintenance

## [1.1.0] - 2025-02-15

### Ajouté
- Support pour la vérification du statut d'une transaction
- Support pour les détails d'une transaction
- Tests automatisés

### Modifié
- Améliorations de performance
- Mise à jour des URLs d'API (https://devapi.mvola.mg)

## [1.0.0] - 2025-01-10

### Ajouté
- Version initiale
- Support pour l'authentification
- Support pour l'initiation de paiement
- Documentation de base

## [Non publié]

### Ajouté
- Structure initiale du projet
- Configuration de build avec pyproject.toml
- Framework de tests
- Documentation avec MkDocs 