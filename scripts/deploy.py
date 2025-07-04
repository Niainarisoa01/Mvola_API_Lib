#!/usr/bin/env python
"""
Script de déploiement pour MVola API Library

Ce script facilite le déploiement de la bibliothèque MVola API:
1. Construit et déploie la documentation sur GitHub Pages
2. Construit et publie le package sur PyPI

Usage:
    python scripts/deploy.py [--docs-only] [--package-only] [--test]
"""
import os
import sys
import argparse
import subprocess
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Exécute une commande shell et log le résultat"""
    logger.info(f"Exécution: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ Succès: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Échec: {description}")
        logger.error(f"Erreur: {e}")
        logger.error(f"Sortie standard: {e.stdout}")
        logger.error(f"Erreur standard: {e.stderr}")
        return False

def deploy_docs():
    """Déployer la documentation sur GitHub Pages"""
    return run_command("mkdocs gh-deploy", "Déploiement de la documentation sur GitHub Pages")

def build_package():
    """Construire le package pour distribution"""
    commands = [
        "python -m pip install --upgrade build",
        "python -m build"
    ]
    for cmd in commands:
        if not run_command(cmd, "Construction du package"):
            return False
    return True

def publish_package(test=False):
    """Publier le package sur PyPI ou TestPyPI"""
    commands = [
        "python -m pip install --upgrade twine"
    ]
    
    if test:
        publish_cmd = "python -m twine upload --repository testpypi dist/*"
        description = "Publication du package sur TestPyPI"
    else:
        publish_cmd = "python -m twine upload dist/*"
        description = "Publication du package sur PyPI"
    
    commands.append(publish_cmd)
    
    for cmd in commands:
        if not run_command(cmd, description if cmd == publish_cmd else "Installation de twine"):
            return False
    return True

def clean():
    """Nettoyer les répertoires de build"""
    return run_command("rm -rf dist/ build/ *.egg-info/", "Nettoyage des répertoires de build")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Script de déploiement pour MVola API Library")
    parser.add_argument("--docs-only", action="store_true", help="Déployer uniquement la documentation")
    parser.add_argument("--package-only", action="store_true", help="Publier uniquement le package")
    parser.add_argument("--test", action="store_true", help="Publier sur TestPyPI au lieu de PyPI")
    
    args = parser.parse_args()
    
    # Si aucune option n'est spécifiée, on déploie tout
    deploy_all = not (args.docs_only or args.package_only)
    
    # Chemin absolu vers le répertoire racine du projet
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    
    logger.info(f"🚀 Démarrage du déploiement depuis {os.getcwd()}")
    
    if deploy_all or args.docs_only:
        if not deploy_docs():
            logger.warning("❗ Échec du déploiement de la documentation")
            if not args.package_only:
                return 1
    
    if deploy_all or args.package_only:
        if not clean():
            logger.warning("❗ Échec du nettoyage des répertoires")
        
        if not build_package():
            logger.error("❌ Échec de la construction du package")
            return 1
        
        if not publish_package(test=args.test):
            logger.error("❌ Échec de la publication du package")
            return 1
    
    logger.info("✅ Déploiement terminé avec succès!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 