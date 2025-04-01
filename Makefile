.PHONY: docs docs-pdf docs-deploy docs-all clean

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

# Installation des dépendances de développement
install-dev:
	pip install -e ".[dev,docs]"
	pip install weasyprint markdown

# Tests
test:
	pytest

# Lancement du serveur de documentation en mode développement
serve:
	mkdocs serve 