"""
Sweelo — Configuration de Gunicorn (serveur WSGI de production)
================================================================
Chargée automatiquement par la commande « gunicorn run:app ».
"""
import os

# Railway fournit le port d'écoute dans la variable d'environnement PORT
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Un seul processus : la création des tables au démarrage (db.create_all)
# n'est ainsi exécutée qu'une fois. Les threads gèrent les requêtes simultanées.
workers = 1
threads = 4
timeout = 60

# Journaux envoyés sur la sortie standard, affichés dans l'onglet Logs de Railway
accesslog = "-"
errorlog = "-"
