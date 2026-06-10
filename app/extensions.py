from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db  = SQLAlchemy()
jwt = JWTManager()

facade = None


def init_facade():
    global facade
    from app.services.facade import SweeloFacade
    facade = SweeloFacade()


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    from app.models.token_blocklist import TokenBlocklist
    jti = jwt_payload["jti"]
    return db.session.query(TokenBlocklist.id).filter_by(jti=jti).first() is not None



    """
Sweelo — Extensions
===================
Initialisation des extensions Flask et de la façade.
Ce fichier évite les imports circulaires en séparant
la création des extensions de leur configuration.

Usage dans les routes :
    from app.extensions import db, jwt, facade
"""
