from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Extensions Flask — créées ici, initialisées dans create_app()
db  = SQLAlchemy()
jwt = JWTManager()

# Façade — instanciée dans create_app() après init des extensions
facade = None


def init_facade():
    """
    Instancie la SweeloFacade après l'init de SQLAlchemy.
    Appelée depuis create_app() une fois db.init_app(app) fait.
    """
    global facade
    from app.services.facade import SweeloFacade
    facade = SweeloFacade()



    """
Sweelo — Extensions
===================
Initialisation des extensions Flask et de la façade.
Ce fichier évite les imports circulaires en séparant
la création des extensions de leur configuration.

Usage dans les routes :
    from app.extensions import db, jwt, facade
"""
