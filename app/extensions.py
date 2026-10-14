"""
Sweelo — Extensions
===================
Initialisation des extensions Flask et de la façade.
Ce fichier évite les imports circulaires en séparant
la création des extensions de leur configuration.

Usage dans les routes :
    from app.extensions import db, jwt, facade
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()

facade = None


def init_facade():
    global facade
    from app.services.facade import SweeloFacade
    facade = SweeloFacade()


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    from app.models.token_blocklist import TokenBlocklist
    from app.models.user import User

    jti = jwt_payload["jti"]
    if db.session.query(TokenBlocklist.id).filter_by(jti=jti).first() is not None:
        return True

    # Un utilisateur banni perd l'accès immédiatement, même si son token
    # (jusqu'à 24h, voire 30j pour un refresh token) n'a pas encore expiré.
    user = db.session.get(User, jwt_payload.get("sub"))
    return user is None or user.is_banned
