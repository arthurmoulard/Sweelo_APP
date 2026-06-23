from flask import Flask
from flask_cors import CORS
from app.config import config
from app.extensions import db, jwt, init_facade


def create_app(config_name: str = "default") -> Flask:
    """
    Crée et configure l'application Flask.

    Args:
        config_name : "development" | "testing" | "production" | "default"

    Returns:
        Flask app configurée et prête à démarrer.
    """

    app = Flask(__name__)

    # ── 1. Chargement de la configuration ─────────────────────────────────────
    app.config.from_object(config[config_name])

    # ── 2. Initialisation des extensions ──────────────────────────────────────
    CORS(app, origins=["http://localhost:8080"], supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)

    # ── 3. Initialisation de la Façade ────────────────────────────────────────
    with app.app_context():
        init_facade()

    # ── 4. Enregistrement des namespaces API ──────────────────────────────────
    from app.api.v1.auth       import ns as auth_ns
    from app.api.v1.activities import ns as activities_ns
    from app.api.v1.feed       import ns as feed_ns
    from app.api.v1.users      import ns as users_ns
    from app.api.v1.admin      import ns as admin_ns

    from flask_restx import Api
    api = Api(
        app,
        title="Sweelo API",
        version="1.0",
        description="API REST pour l'application de tracking sportif Sweelo",
        prefix="/api/v1",
        doc="/api/docs",          # Swagger UI disponible sur /api/docs
    )

    api.add_namespace(auth_ns,        path="/auth")
    api.add_namespace(activities_ns,  path="/activities")
    api.add_namespace(feed_ns,        path="/feed")
    api.add_namespace(users_ns,       path="/users")
    api.add_namespace(admin_ns,       path="/admin")

    # ── 5. Création des tables BDD (si inexistantes) ──────────────────────────
    with app.app_context():
        from app.models.token_blocklist import TokenBlocklist  # noqa: F401
        db.create_all()

    return app

"""
Sweelo — Application Factory
=============================
Pattern Factory Flask : crée et configure l'application.
Permet d'instancier plusieurs configurations (dev, test, prod)
sans conflit d'état global.

Usage :
    # Lancement dev
    from app import create_app
    app = create_app("development")
    app.run()

    # Dans les tests
    app = create_app("testing")
    with app.test_client() as client:
        ...
"""
