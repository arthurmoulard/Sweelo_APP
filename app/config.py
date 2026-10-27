import os
import tempfile
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv

load_dotenv()  # Charge le fichier .env à la racine du projet


def _database_url(default):
    """Lit DATABASE_URL et l'adapte au driver utilisé par SQLAlchemy.

    Aiven fournit une URL « mysql://…?ssl-mode=REQUIRED » :
    - SQLAlchemy a besoin du nom du driver Python, ici PyMySQL : « mysql+pymysql://… » ;
    - PyMySQL ne connaît pas le paramètre « ssl-mode » : on le retire de l'URL et
      le chiffrement est activé dans _mysql_connect_args().
    """
    url = os.getenv("DATABASE_URL", default)
    if url.startswith("mysql://"):
        url = "mysql+pymysql://" + url[len("mysql://"):]
    if "ssl-mode" not in url.lower() and "sslmode" not in url.lower():
        return url   # rien à nettoyer (SQLite, MySQL local) : l'URL reste intacte
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k.lower() not in ("ssl-mode", "sslmode")]
    return urlunsplit(parts._replace(query=urlencode(query)))


def _mysql_connect_args():
    """Options de connexion SSL pour MySQL hébergé (Aiven exige une connexion chiffrée).

    - DATABASE_CA_CERT (contenu du fichier ca.pem d'Aiven) : connexion chiffrée ET
      vérification du certificat du serveur (recommandé) ;
    - sinon, si l'URL contient ssl-mode=REQUIRED : connexion chiffrée sans vérification ;
    - sinon (MySQL local) : pas de SSL.
    """
    ca_cert = os.getenv("DATABASE_CA_CERT", "").strip()
    if ca_cert:
        # Sur Vercel, seul /tmp est accessible en écriture
        ca_path = os.path.join(tempfile.gettempdir(), "sweelo-db-ca.pem")
        with open(ca_path, "w", encoding="utf-8") as f:
            f.write(ca_cert.replace("\\n", "\n") + "\n")
        return {"ssl": {"ca": ca_path}}
    if "ssl-mode=" in os.getenv("DATABASE_URL", "").lower():
        return {"ssl": {"check_hostname": False}}
    return {}


class BaseConfig:
    """Configuration commune à tous les environnements."""

    # ── Flask ──────────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "sweelo-dev-secret-change-in-prod")

    # ── JWT ────────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY            = os.getenv("JWT_SECRET_KEY", "sweelo-jwt-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES   = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES  = timedelta(days=30)

    # Cookies httpOnly plutôt que localStorage + header Authorization :
    # le JS ne peut plus lire le token, ce qui ferme l'exfiltration via XSS.
    JWT_TOKEN_LOCATION      = ["cookies"]
    JWT_COOKIE_SECURE       = False   # ProductionConfig repasse ça à True (HTTPS)
    JWT_COOKIE_SAMESITE     = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True    # double-submit CSRF (nécessaire : les cookies sont vulnérables au CSRF)
    JWT_SESSION_COOKIE      = False   # sinon le cookie disparaît à la fermeture du navigateur
    JWT_ACCESS_COOKIE_PATH  = "/"
    JWT_REFRESH_COOKIE_PATH = "/api/v1/auth/refresh"

    # Tolérance de 10 s sur les dates des tokens (iat, nbf, exp) : sans elle, un
    # léger recul de l'horloge (resynchronisation NTP, WSL) fait rejeter un token
    # tout juste émis comme « pas encore valide ».
    JWT_DECODE_LEEWAY       = 10

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
    # Vercel refuse les requêtes de plus de 4,5 Mo : on bloque à 4 Mo côté Flask
    # pour renvoyer une erreur 413 claire plutôt qu'une erreur de la plateforme.
    MAX_CONTENT_LENGTH     = 4 * 1024 * 1024   # 4 MB max par upload
    ALLOWED_EXTENSIONS     = {"jpg", "jpeg", "png", "webp"}


class DevelopmentConfig(BaseConfig):
    """
    Environnement de développement local.
    BDD : SQLite (fichier sweelo_dev.db à la racine)
    """

    DEBUG                   = True
    SQLALCHEMY_DATABASE_URI = _database_url("sqlite:///sweelo_dev.db")

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
    Hébergement : Vercel · BDD : MySQL sur Aiven (variable DATABASE_URL obligatoire)
    """

    DEBUG                   = False
    SQLALCHEMY_DATABASE_URI = _database_url("mysql+pymysql://user:password@localhost/sweelo_prod")
    SQLALCHEMY_ECHO         = False

    # MySQL ferme les connexions inactives : on vérifie chaque connexion avant
    # de l'utiliser et on la renouvelle toutes les 5 minutes. Petit pool : sur
    # Vercel, chaque instance de la fonction ouvre ses propres connexions et
    # l'offre gratuite d'Aiven en accepte un nombre limité.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "pool_size": 2,
        "max_overflow": 3,
        "connect_args": _mysql_connect_args(),
    }

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

Variables d'environnement (fichier .env en local, réglages du projet sur Vercel) :
    SECRET_KEY            — clé secrète Flask
    JWT_SECRET_KEY        — clé de signature des tokens JWT
    OPENAI_API_KEY        — clé API OpenAI (coaching IA + modération)
    DATABASE_URL          — URL BDD (obligatoire en production, sinon SQLite par défaut)
    DATABASE_CA_CERT      — certificat CA d'Aiven (optionnel, vérifie le serveur MySQL)
    BLOB_READ_WRITE_TOKEN — jeton Vercel Blob (ajouté par Vercel, photos et avatars)

Usage :
    from app.config import config
    app.config.from_object(config["development"])
"""
