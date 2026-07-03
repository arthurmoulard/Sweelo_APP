# Sweelo — Liens du projet

> Récapitulatif des liens vers les ressources de gestion de projet, le code source et les preuves de test.

| Ressource | Lien / Statut |
|-----------|---------------|
| Sprint planning | [Kanban GitHub — issues du sprint](https://github.com/arthurmoulard/Sweelo_APP/issues?q=is%3Aissue+updated%3A%3E%40today-1w+sort%3Aupdated-desc) |
| Sprint reviews | [Kanban GitHub — issues du sprint](https://github.com/arthurmoulard/Sweelo_APP/issues?q=is%3Aissue+updated%3A%3E%40today-1w+sort%3Aupdated-desc) |
| Rétrospectives | [Kanban GitHub — issues du sprint](https://github.com/arthurmoulard/Sweelo_APP/issues?q=is%3Aissue+updated%3A%3E%40today-1w+sort%3Aupdated-desc) |
| Dépôt source | [github.com/arthurmoulard/Sweelo_APP](https://github.com/arthurmoulard/Sweelo_APP) |
| Suivi des bugs | [GitHub Issues](https://github.com/arthurmoulard/Sweelo_APP/issues) — tickets ouverts tout au long du projet pour signaler et suivre les bugs identifiés |
| Preuves et résultats de tests | [Dossier `tests/`](https://github.com/arthurmoulard/Sweelo_APP/tree/main/tests) — 70 cas de test unitaires et d'intégration ([pytest](https://docs.pytest.org)), exécutables avec `pytest` — détail dans les tableaux ci-dessous |
| Environnement de production | N/A — l'application n'est pas déployée en ligne ; elle s'exécute en local via Flask (`python run.py`), SQLite en développement / MySQL prévu en production |

## Détails

### Gestion des sprints (GitHub)

L'ensemble du suivi agile (planification des sprints, reviews et rétrospectives) est géré en Kanban directement sur GitHub, via les issues du dépôt :
**https://github.com/arthurmoulard/Sweelo_APP/issues?q=is%3Aissue+updated%3A%3E%40today-1w+sort%3Aupdated-desc**

Cette vue filtre les issues mises à jour au cours de la dernière semaine (sprint en cours), triées par activité récente.

### Tests

Les tests backend se trouvent dans le dépôt : **70 cas** au total (45 d'intégration + 25 unitaires), écrits avec [pytest](https://docs.pytest.org).

Exécution : `pytest` (base SQLite en mémoire dédiée aux tests, `.venv` doit contenir `pytest` + `pytest-flask` du `requirement.txt`). La modération OpenAI est neutralisée pendant les tests (aucun appel réseau réel), sauf dans `test_moderation_service.py` où elle est simulée (mock).

**CI GitHub Actions** : [`.github/workflows/ci.yml`](https://github.com/arthurmoulard/Sweelo_APP/blob/main/.github/workflows/ci.yml) — lance `flake8` (lint) puis `pytest` (70 tests) sur chaque push et pull request, quelle que soit la branche.

#### Tests unitaires — `tests/unit/` (25 cas)

| Fichier | Cas testé |
|---------|-----------|
| `test_user_model.py` | Hash du mot de passe (bcrypt) — le hash diffère du mot de passe en clair |
| `test_user_model.py` | `check_password` accepte le bon mot de passe |
| `test_user_model.py` | `check_password` rejette un mauvais mot de passe |
| `test_user_model.py` | `to_dict()` expose uniquement les champs publics (pas le hash) |
| `test_activity_model.py` | `to_dict()` inclut les champs principaux (type, distance, durée, date, notes) |
| `test_activity_model.py` | Sport sans distance (`muscu`) autorise `distance_km = None` |
| `test_activity_model.py` | `NO_DISTANCE_TYPES` est un sous-ensemble de `ACTIVITY_TYPES` |
| `test_activity_model.py` | `run` nécessite une distance |
| `test_activity_model.py` | `muscu` ne nécessite pas de distance |
| `test_facade.py` | `register` crée l'utilisateur |
| `test_facade.py` | `register` rejette un email déjà utilisé |
| `test_facade.py` | `register` rejette un username déjà pris |
| `test_facade.py` | `login` rejette un mauvais mot de passe |
| `test_facade.py` | `login` rejette un compte banni |
| `test_facade.py` | `create_activity` rejette une date dans le futur |
| `test_facade.py` | `create_activity` crée aussi le `FeedPost` associé |
| `test_facade.py` | `get_activity` refuse l'accès à un autre utilisateur |
| `test_facade.py` | `get_activity` lève une erreur si l'id est inconnu |
| `test_facade.py` | `add_friend` crée la relation dans les deux sens |
| `test_facade.py` | `add_friend` rejette l'ajout de soi-même |
| `test_facade.py` | `add_friend` rejette un doublon |
| `test_moderation_service.py` | `check` laisse passer le contenu si `OPENAI_API_KEY` absente (fail open) |
| `test_moderation_service.py` | `check` laisse passer le contenu si l'API échoue (fail open) |
| `test_moderation_service.py` | `check` rejette un contenu flaggé par l'API |
| `test_moderation_service.py` | `check` accepte un contenu non flaggé |

#### Tests d'intégration — `tests/integration/test_auth_endpoints.py` (12 cas)

| Groupe | Cas testé |
|--------|-----------|
| Inscription | `POST /auth/register` retourne les tokens et l'utilisateur créé |
| Inscription | `POST /auth/register` refuse un email déjà utilisé (409) |
| Inscription | `POST /auth/register` refuse un username déjà pris (409) |
| Inscription | `POST /auth/register` refuse un mot de passe trop court (400) |
| Inscription | `POST /auth/register` refuse un email invalide (400) |
| Connexion | `POST /auth/login` avec identifiants valides retourne 200 + tokens |
| Connexion | `POST /auth/login` avec mauvais mot de passe échoue (401) |
| Connexion | `POST /auth/login` avec email inconnu échoue (401) |
| Session | `GET /users/me` retourne 401 si non connecté |
| Session | `GET /users/me` retourne l'utilisateur connecté |
| Session | `POST /auth/logout` révoque le token (accès refusé ensuite) |
| Session | `POST /auth/refresh` refuse un access token à la place d'un refresh token (422) |

#### Tests d'intégration — `tests/integration/test_activity_endpoints.py` (12 cas)

| Groupe | Cas testé |
|--------|-----------|
| Création | `POST /activities/` retourne 401 si non connecté |
| Création | `POST /activities/` crée l'activité (200/201) |
| Création | `POST /activities/` refuse l'absence de distance pour un sport avec distance (400) |
| Création | `POST /activities/` autorise `distance_km` absente pour un sport sans distance |
| Création | `POST /activities/` refuse une date dans le futur (400) |
| Détail | `GET /activities/:id` retourne l'activité du propriétaire |
| Détail | `GET /activities/:id` retourne 404 si l'activité n'existe pas |
| Détail | `GET /activities/:id` retourne 403 pour un autre utilisateur |
| Mise à jour | `PUT /activities/:id` modifie les champs |
| Mise à jour | `PUT /activities/:id` retourne 403 pour un autre utilisateur |
| Suppression | `DELETE /activities/:id` supprime l'activité |
| Liste | `GET /activities/` retourne la liste paginée |

#### Tests d'intégration — `tests/integration/test_feed_endpoints.py` (12 cas)

| Groupe | Cas testé |
|--------|-----------|
| Feed | `GET /feed/` retourne 401 si non connecté |
| Feed | `GET /feed/` contient son propre post |
| Feed | `GET /feed/` exclut les posts d'utilisateurs non amis |
| Likes | `POST /feed/:id/like` bascule liked/unliked |
| Likes | `POST /feed/:id/like` sur un post inconnu retourne 404 |
| Commentaires | Impossible de commenter son propre post (400) |
| Commentaires | Commenter le post d'un autre utilisateur fonctionne (201) |
| Commentaires | `GET /feed/:id/comments` liste les commentaires |
| Commentaires | Supprimer son propre commentaire fonctionne (204) |
| Commentaires | Supprimer le commentaire d'un autre utilisateur est refusé (403) |
| Signalement | `POST /feed/:id/report` retourne une confirmation |
| Signalement | `POST /feed/:id/report` sur un post inconnu retourne 404 |

#### Tests d'intégration — `tests/integration/test_admin_endpoints.py` (9 cas)

| Groupe | Cas testé |
|--------|-----------|
| Accès admin | Route admin retourne 401 si non connecté |
| Accès admin | Route admin retourne 403 pour un utilisateur non admin |
| Accès admin | Route admin retourne 200 pour un admin |
| Bannissement | Bannir un utilisateur empêche sa connexion |
| Bannissement | Débannir un utilisateur restaure sa connexion |
| Bannissement | Bannir un utilisateur inconnu retourne 404 |
| Signalements | Workflow complet : signalement → liste des reports → passage en "reviewed" |
| Suppression de post | Supprimer un post (admin) le retire du feed |
| Suppression de post | Supprimer un post inconnu retourne 404 |

#### Structure des tests

```
tests/
├── unit/
│   ├── test_user_model.py
│   ├── test_activity_model.py
│   ├── test_facade.py
│   └── test_moderation_service.py  # mock du client OpenAI
├── integration/
│   ├── test_auth_endpoints.py
│   ├── test_activity_endpoints.py
│   ├── test_feed_endpoints.py
│   └── test_admin_endpoints.py
└── conftest.py                     # fixtures (app, client, auth_headers, second_user)
```

### Production

Aucun environnement de production hébergé. L'application se lance en local :

```bash
pip install -r requirement.txt
python run.py   # Flask API + PWA Vanilla JS, SQLite en dev
pytest           # 70 tests, base SQLite en mémoire
```

La bascule vers MySQL en production est prévue via la variable d'environnement `DATABASE_URL` (SQLAlchemy), sans modification du code applicatif.
