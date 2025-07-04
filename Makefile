.PHONY: docs docs-pdf docs-deploy docs-all clean build dist publish publish-test deploy-all

# Génération de documentation
docs:
	mkdocs build

docs-pdf:
	python scripts/generate_docs.py --pdf

docs-deploy:
	python scripts/generate_docs.py --deploy

docs-all:
	python scripts/generate_docs.py --all

# Nettoyage
clean:
	rm -rf site/
	rm -rf docs/output/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Installation des dépendances de développement
install-dev:
	pip install -e ".[dev,docs]"
	pip install weasyprint markdown

# Tests
test:
	pytest

# Construction du package
build:
	python -m pip install --upgrade build
	python -m build

# Distribution du package
dist: clean build

# Publication sur PyPI
publish:
	python -m pip install --upgrade twine
	python -m twine upload dist/*

# Publication sur TestPyPI
publish-test:
	python -m pip install --upgrade twine
	python -m twine upload --repository testpypi dist/*

# Déploiement complet (documentation et package)
deploy-all: docs-deploy dist publish

# Lancement du serveur de documentation en mode développement
serve:
	mkdocs serve 