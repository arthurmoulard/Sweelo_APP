import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()  # Charge le fichier .env à la racine du projet


class BaseConfig:
    """Configuration commune à tous les environnements."""

    # ── Flask ──────────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "sweelo-dev-secret-change-in-prod")

    # ── JWT ────────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY            = os.getenv("JWT_SECRET_KEY", "sweelo-jwt-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=24)
    JWT_TOKEN_LOCATION         = ["headers"]         # Bearer token dans Authorization
    JWT_HEADER_NAME            = "Authorization"
    JWT_HEADER_TYPE            = "Bearer"

    # ── SQLAlchemy ─────────────────────────────────────────────────────────────
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── OpenAI ─────────────────────────────────────────────────────────────────
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")   # Coaching IA + Modération

    # ── Cloudinary (photos des posts) ──────────────────────────────────────────
    CLOUDINARY_URL         = os.getenv("CLOUDINARY_URL", "")
    CLOUDINARY_CLOUD_NAME  = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY     = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET  = os.getenv("CLOUDINARY_API_SECRET", "")

    # ── Upload ─────────────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH     = 5 * 1024 * 1024   # 5 MB max par upload
    ALLOWED_EXTENSIONS     = {"jpg", "jpeg", "png", "webp"}


class DevelopmentConfig(BaseConfig):
    """
    Environnement de développement local.
    BDD : SQLite (fichier sweelo_dev.db à la racine)
    """

    DEBUG                   = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///sweelo_dev.db")

    # Logs SQL dans le terminal en dev (pratique pour déboguer)
    SQLALCHEMY_ECHO         = True


class TestingConfig(BaseConfig):
    """
    Environnement de test.
    BDD : SQLite en mémoire (réinitialisée à chaque test)
    """

    TESTING                 = True
    DEBUG                   = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO         = False

    # Désactive la protection CSRF pour les tests
    WTF_CSRF_ENABLED        = False

    # Tokens JWT courts pour les tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(BaseConfig):
    """
    Environnement de production.
    BDD : MySQL (variable DATABASE_URL obligatoire)
    """

    DEBUG                   = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@localhost/sweelo_prod"
    )
    SQLALCHEMY_ECHO         = False

    # Sécurité renforcée en prod
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    JWT_COOKIE_SECURE        = True    # HTTPS uniquement


# ── Dictionnaire de configuration ──────────────────────────────────────────────
config = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}

"""
Sweelo — Configuration
======================
Trois environnements : Development · Testing · Production

Variables d'environnement requises (fichier .env) :
    SECRET_KEY          — clé secrète Flask
    JWT_SECRET_KEY      — clé de signature des tokens JWT
    OPENAI_API_KEY      — clé API OpenAI (coaching IA + modération)
    DATABASE_URL        — URL BDD (optionnel, sinon SQLite par défaut)
    CLOUDINARY_URL      — URL Cloudinary (optionnel, photos des posts)

Usage :
    from app.config import config
    app.config.from_object(config["development"])
"""
