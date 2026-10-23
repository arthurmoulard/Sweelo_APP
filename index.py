"""
Sweelo — Point d'entrée Vercel
==============================
Vercel cherche un fichier index.py (ou app.py…) à la racine du projet et une
variable nommée « app » : c'est l'application Flask, exécutée comme une
fonction serverless. En local, on continue d'utiliser run.py.
"""
import os

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "production"))
