#!/usr/bin/env python
"""
Script pour générer la documentation en différents formats
"""
import os
import subprocess
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directory(directory):
    """S'assure que le répertoire existe, le crée si nécessaire"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Répertoire créé: {directory}")

def generate_pdf():
    """Génère un PDF à partir du fichier Markdown"""
    try:
        import markdown
        from weasyprint import HTML
        
        # Lecture du fichier Markdown
        with open("docs/documentation.md", "r", encoding="utf-8") as md_file:
            markdown_content = md_file.read()
        
        # Conversion en HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'codehilite', 'toc']
        )
        
        # Ajout de style CSS basique
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>MVola API Documentation</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                pre {{ background-color: #f8f8f8; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                code {{ font-family: Consolas, Monaco, 'Andale Mono', monospace; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Création du répertoire output s'il n'existe pas
        ensure_directory("docs/output")
        
        # Écriture du HTML dans un fichier temporaire
        html_path = "docs/output/temp.html"
        with open(html_path, "w", encoding="utf-8") as html_file:
            html_file.write(styled_html)
        
        # Conversion du HTML en PDF
        pdf_path = "docs/output/mvola_api_documentation.pdf"
        HTML(html_path).write_pdf(pdf_path)
        
        logger.info(f"PDF généré avec succès: {pdf_path}")
        return True
    except ImportError:
        logger.warning("Modules nécessaires non installés. Veuillez installer weasyprint et markdown.")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF: {e}")
        return False

def build_mkdocs():
    """Construit le site de documentation avec MkDocs"""
    try:
        subprocess.run(["mkdocs", "build"], check=True)
        logger.info("Site MkDocs généré avec succès")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de la génération du site MkDocs: {e}")
        return False

def deploy_mkdocs():
    """Déploie le site MkDocs sur GitHub Pages"""
    try:
        subprocess.run(["mkdocs", "gh-deploy"], check=True)
        logger.info("Site MkDocs déployé avec succès sur GitHub Pages")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors du déploiement sur GitHub Pages: {e}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Outil de génération de documentation pour MVola API")
    parser.add_argument("--pdf", action="store_true", help="Générer un PDF")
    parser.add_argument("--build", action="store_true", help="Construire le site MkDocs")
    parser.add_argument("--deploy", action="store_true", help="Déployer sur GitHub Pages")
    parser.add_argument("--all", action="store_true", help="Exécuter toutes les actions")

    args = parser.parse_args()

    # Si aucune option n'est spécifiée, afficher l'aide
    if not (args.pdf or args.build or args.deploy or args.all):
        parser.print_help()
    
    # Exécution des commandes demandées
    if args.all or args.pdf:
        generate_pdf()
    
    if args.all or args.build:
        build_mkdocs()
    
    if args.all or args.deploy:
        if args.all or args.build:
            # Si on vient de construire le site, on peut le déployer
            deploy_mkdocs()
        else:
            # Sinon, on demande confirmation
            response = input("Voulez-vous construire le site avant de le déployer? (y/n): ")
            if response.lower() in ["y", "yes", "o", "oui"]:
                if build_mkdocs():
                    deploy_mkdocs()
            else:
                deploy_mkdocs() 