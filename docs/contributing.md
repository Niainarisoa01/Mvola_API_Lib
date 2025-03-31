# Guide de contribution

Nous sommes ravis que vous souhaitiez contribuer à la bibliothèque MVola API ! Ce document vous guidera à travers le processus de contribution.

## Code de conduite

En participant à ce projet, vous vous engagez à maintenir un environnement respectueux et accueillant pour tous. Nous attendons de tous les contributeurs qu'ils se conforment aux principes suivants :

- Utiliser un langage accueillant et inclusif
- Respecter les différents points de vue et expériences
- Accepter gracieusement les critiques constructives
- Se concentrer sur ce qui est le mieux pour la communauté
- Faire preuve d'empathie envers les autres membres de la communauté

## Comment contribuer

### Signaler des bugs

Si vous trouvez un bug, veuillez créer une issue sur GitHub avec les informations suivantes :

1. Un titre clair et descriptif
2. Une description détaillée du problème
3. Les étapes pour reproduire le bug
4. Le comportement attendu vs. le comportement observé
5. Toute information supplémentaire (environnement, logs, etc.)

### Proposer des améliorations

Pour proposer une amélioration, créez une issue en incluant :

1. Une description claire de l'amélioration proposée
2. La justification de cette amélioration (pourquoi est-elle utile ?)
3. Si possible, un exemple de code ou une esquisse de l'implémentation

### Contribution au code

1. **Fork** le dépôt sur GitHub
2. **Clone** votre fork sur votre machine locale
3. **Créez une branche** pour votre contribution (`git checkout -b feature/ma-fonctionnalite`)
4. **Modifiez le code** en suivant les conventions du projet
5. **Testez** vos modifications
6. **Committez** vos changements (`git commit -m "Ajout de ma fonctionnalité"`)
7. **Poussez** votre branche sur GitHub (`git push origin feature/ma-fonctionnalite`)
8. **Créez une Pull Request** sur le dépôt original

## Processus de développement

### Environnement de développement

Pour configurer votre environnement de développement :

```bash
# Cloner le dépôt
git clone https://github.com/Niainarisoa01/Mvlola_API_Lib.git
cd Mvlola_API_Lib

# Installer les dépendances de développement
pip install -e ".[dev]"
```

### Exécuter les tests

```bash
# Exécuter tous les tests
pytest

# Exécuter les tests avec couverture
pytest --cov=mvola_api
```

### Style de code

Nous utilisons les outils suivants pour maintenir un style de code cohérent :

- **Black** pour le formatage de code
- **isort** pour trier les imports
- **flake8** pour la vérification de style

Vous pouvez les exécuter avec :

```bash
# Formater le code
black mvola_api tests

# Trier les imports
isort mvola_api tests

# Vérifier le style
flake8 mvola_api tests
```

### Documentation

La documentation est générée avec MkDocs et mkdocstrings :

```bash
# Installer les dépendances de documentation
pip install -e ".[docs]"

# Servir la documentation localement
mkdocs serve

# Construire la documentation
mkdocs build
```

## Conventions de commit

Nous suivons une convention de messages de commit simple :

- `feat:` pour une nouvelle fonctionnalité
- `fix:` pour une correction de bug
- `docs:` pour les modifications de documentation
- `style:` pour les changements de formatage
- `refactor:` pour les refactorisations de code
- `test:` pour l'ajout ou la modification de tests
- `chore:` pour les tâches de maintenance

Exemple : `feat: Ajout de la fonctionnalité de paiement par callback`

## Versionnement

Nous suivons le [Semantic Versioning](https://semver.org/lang/fr/) :

- MAJOR pour les changements incompatibles
- MINOR pour les ajouts de fonctionnalités rétrocompatibles
- PATCH pour les corrections de bugs rétrocompatibles

## Processus de revue

Lorsque vous soumettez une Pull Request, un mainteneur du projet la passera en revue. Le processus peut inclure des demandes de modifications ou des discussions sur l'implémentation.

Pour faciliter la revue :

1. Assurez-vous que tous les tests passent
2. Documentez les nouvelles fonctionnalités
3. Maintenez vos Pull Requests focalisées sur une seule fonctionnalité/correction

## Remerciements

Un grand merci à tous les contributeurs qui aident à améliorer cette bibliothèque ! 