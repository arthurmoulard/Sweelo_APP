# Sweelo — Stage 3 : Documentation Technique

> Application de tracking sportif et réseau social sportif pour athlètes amateurs
> **Stack :** Flask · SQLAlchemy · JWT · Vanilla JS PWA
> **Équipe :** Arthur Moulard · Valentin Pasquiet
> **Base de données :** SQLite (dev) → MySQL (prod)

---

## Table des matières

1. [User Stories & Maquettes](#1-user-stories--maquettes)
2. [Architecture Système](#2-architecture-système)
3. [Composants, Classes & Base de données](#3-composants-classes--base-de-données)
4. [Diagrammes de Séquence](#4-diagrammes-de-séquence)
5. [Spécifications API](#5-spécifications-api)
6. [Modération de contenu](#6-modération-de-contenu)
7. [SCM & QA](#7-scm--qa)
8. [Justifications Techniques](#8-justifications-techniques)

---

## 1. User Stories & Maquettes

### Méthode de priorisation : MoSCoW

#### Must Have — Cœur du MVP

| # | User Story | Priorité |
|---|------------|----------|
| US-01 | En tant qu'athlète, je veux créer un compte avec email/mot de passe, afin d'accéder à mes données personnalisées. | 🔴 Must |
| US-02 | En tant qu'athlète, je veux me connecter et obtenir un token JWT, afin d'accéder aux routes protégées. | 🔴 Must |
| US-03 | En tant qu'athlète, je veux enregistrer une activité (type, distance, durée, date), afin de suivre mes entraînements. | 🔴 Must |
| US-04 | En tant qu'athlète, je veux consulter l'historique de mes activités, afin de visualiser ma progression. | 🔴 Must |
| US-05 | En tant qu'athlète, je veux voir un feed social des activités de mes amis, afin de rester motivé. | 🔴 Must |
| US-06 | En tant qu'admin, je veux bannir ou supprimer un utilisateur, afin d'assainir la communauté. | 🔴 Must |
| US-07 | En tant qu'utilisateur, je veux signaler un post ou un commentaire, afin d'alerter les modérateurs d'un contenu inapproprié. | 🔴 Must |
| US-08 | En tant que système, je veux soumettre chaque post ou commentaire à l'OpenAI Moderation API avant insertion, afin de bloquer automatiquement les contenus toxiques. | 🔴 Must |

#### Should Have — Valeur ajoutée importante

| # | User Story | Priorité |
|---|------------|----------|
| US-09 | En tant qu'athlète, je veux ajouter des amis via leur identifiant, afin de suivre leurs activités. | 🟠 Should |
| US-10 | En tant qu'athlète, je veux liker ou commenter une activité du feed, afin d'interagir avec mes amis. | 🟠 Should |
| US-11 | En tant qu'admin, je veux consulter et traiter les signalements, afin de modérer la plateforme manuellement. | 🟠 Should |
| US-12 | En tant qu'admin, je veux supprimer un post ou un commentaire signalé, afin de modérer le contenu inapproprié. | 🟠 Should |

#### Could Have / Won't Have

| # | User Story | Priorité |
|---|------------|----------|
| US-13 | En tant qu'athlète, je veux tracker mon activité en temps réel via GPS depuis mon smartphone. | 🟡 Could |
| US-14 | En tant qu'athlète, je veux connecter ma montre via Bluetooth pour importer mes données automatiquement. | ⚪ Won't (MVP) |
| US-15 | En tant qu'athlète, je veux partager mon activité sur Instagram ou Twitter. | ⚪ Won't (MVP) |

### Maquettes — Écrans principaux

Les maquettes interactives ci-dessous couvrent l'ensemble des écrans du MVP, organisés par rôle (utilisateur et admin). Chaque écran est navigable via le menu latéral et correspond aux user stories associées.

| Écran | Contenu attendu | User Stories couvertes |
|-------|-----------------|------------------------|
| **Inscription** | Formulaire de création de compte | US-01 |
| **Connexion** | Formulaire login + retour token JWT | US-02 |
| **Log activité** | Sélection type, distance, durée, date, note | US-03 |
| **Historique** | Stats du mois, graphe semaine, liste activités filtrables | US-04 |
| **Feed social** | Activités amis, like, commentaire, bouton signaler | US-05, US-07, US-10 |
| **Admin — Utilisateurs** | Stats globales, liste utilisateurs, bannir/avertir | US-06 |
| **Admin — Modération** | File signalements, score OpenAI, actions bloquer/valider | US-08, US-11, US-12 |

## Inscription


<img width="365" height="583" alt="Capture d&#39;écran 2026-05-22 160636" src="https://github.com/user-attachments/assets/d6d9cb52-2ec2-4432-8c8d-891bdd9d83e5" />



## Connexion


<img width="374" height="537" alt="Capture d&#39;écran 2026-05-22 160645" src="https://github.com/user-attachments/assets/e5ee52b0-f30f-48e6-9a87-ce1a6d153528" />



## Enregistrer une activité


<img width="372" height="565" alt="Capture d&#39;écran 2026-05-22 160652" src="https://github.com/user-attachments/assets/9f2f45d7-2e95-4284-a246-85c0e32cd7c0" />



## Historique



<img width="375" height="521" alt="Capture d&#39;écran 2026-05-22 160715" src="https://github.com/user-attachments/assets/04377188-c3e7-4f14-9ce0-0b3ad11d5223" />


## Feed



<img width="371" height="446" alt="Capture d&#39;écran 2026-05-22 160725" src="https://github.com/user-attachments/assets/070b2aef-56bf-4bbf-82bd-e3a80031c227" />




## Modération



<img width="370" height="504" alt="Capture d&#39;écran 2026-05-22 160734" src="https://github.com/user-attachments/assets/1eb4d971-8cc3-47de-9e68-760914a909af" />


<img width="377" height="611" alt="Capture d&#39;écran 2026-05-22 160742" src="https://github.com/user-attachments/assets/8c348bdd-caf8-443d-8abc-05bd1153285d" />



---

## 2. Architecture Système

### Diagramme d'architecture haut niveau

```mermaid
graph TB
    subgraph Client["🖥️ Client — PWA Vanilla JS"]
        UI[Interface utilisateur]
        SW[Service Worker<br/>Mode offline]
    end

    subgraph Backend["⚙️ Backend — Flask API"]
        RESTX[Flask-RESTX<br/>Routes & Namespaces]
        JWT[Flask-JWT-Extended<br/>Auth & Middleware]
        FACADE[SweeloFacade<br/>Logique métier]
        REPO[Repositories<br/>UserRepo · ActivityRepo · FeedRepo · ReportRepo]
        MOD_SVC[ModerationService]
    end

    subgraph Data["🗄️ Persistance"]
        SQLITE[(SQLite<br/>Développement)]
        MYSQL[(MySQL<br/>Production)]
    end

    subgraph External["🌐 Services externes — OpenAI API"]
        MODERATION[Moderation API<br/>Analyse de contenu<br/>/v1/moderations]
    end

    UI -->|HTTPS / JSON + Bearer JWT| RESTX
    SW -.->|Cache offline| UI
    RESTX --> JWT
    JWT --> FACADE
    FACADE --> REPO
    FACADE --> MOD_SVC
    REPO -->|SQLAlchemy ORM| SQLITE
    REPO -->|SQLAlchemy ORM| MYSQL
    MOD_SVC -->|POST /v1/moderations| MODERATION
```

### Stack technique

| Couche | Technologie | Rôle |
|--------|-------------|------|
| Frontend | Vanilla JS PWA | Interface utilisateur, Service Worker, Fetch API |
| Backend | Flask + Flask-RESTX | API REST, namespaces, documentation Swagger auto |
| Auth | Flask-JWT-Extended | Tokens JWT stateless, contrôle d'accès par rôle |
| ORM | SQLAlchemy | Abstraction BDD, Repository Pattern |
| BDD dev | SQLite | Zéro configuration, portable |
| BDD prod | MySQL | Robustesse, gestion de la concurrence |
| Modération | OpenAI Moderation API | Analyse automatique du contenu avant publication |
| Hashage | bcrypt | Stockage sécurisé des mots de passe (OWASP) |

---

## 3. Composants, Classes & Base de données

### Diagramme de classes

```mermaid
classDiagram
    class User {
        +UUID id
        +String email
        +String password_hash
        +String username
        +Bool is_admin
        +Bool is_banned
        +DateTime created_at
        +create()
        +update()
        +add_friend(user_id)
        +to_dict()
    }

    class Activity {
        +UUID id
        +UUID user_id
        +String type
        +Float distance_km
        +Int duration_min
        +Date date
        +String notes
        +create()
        +delete()
        +to_dict()
    }

    class FeedPost {
        +UUID id
        +UUID activity_id
        +UUID user_id
        +Int likes_count
        +DateTime created_at
        +create()
        +like(user_id)
        +get_comments()
    }

    class Comment {
        +UUID id
        +UUID post_id
        +UUID user_id
        +String content
        +DateTime created_at
        +create()
        +delete()
    }

    class Report {
        +UUID id
        +UUID reporter_id
        +Enum target_type
        +UUID target_id
        +String reason
        +Enum status
        +DateTime created_at
        +to_dict()
    }

    class SweeloFacade {
        +UserRepository user_repo
        +ActivityRepository activity_repo
        +FeedRepository feed_repo
        +ReportRepository report_repo
        +ModerationService moderation
        +create_activity(data, user_id)
        +get_feed(user_id, page)
        +create_comment(post_id, user_id, content)
        +report_content(reporter_id, type, target_id, reason)
    }

    User "1" --> "N" Activity : possède
    User "N" --> "N" User : amis via Friendship
    Activity "1" --> "1" FeedPost : publie
    FeedPost "1" --> "N" Comment : contient
    FeedPost "1" --> "N" Report : reçoit
    Comment "1" --> "N" Report : reçoit
    SweeloFacade --> User
    SweeloFacade --> Activity
    SweeloFacade --> FeedPost
    SweeloFacade --> Report
```

### Diagramme Entité-Relation (ER)

```mermaid
erDiagram
    USERS {
        UUID id PK
        VARCHAR email UK
        VARCHAR password_hash
        VARCHAR username UK
        BOOL is_admin
        BOOL is_banned
        DATETIME created_at
    }

    ACTIVITIES {
        UUID id PK
        UUID user_id FK
        ENUM type
        FLOAT distance_km
        INT duration_min
        DATE date
        TEXT notes
    }

    FEED_POSTS {
        UUID id PK
        UUID activity_id FK
        UUID user_id FK
        INT likes_count
        DATETIME created_at
    }

    COMMENTS {
        UUID id PK
        UUID post_id FK
        UUID user_id FK
        TEXT content
        DATETIME created_at
    }

    POST_LIKES {
        UUID post_id FK
        UUID user_id FK
    }

    FRIENDSHIPS {
        UUID user_id FK
        UUID friend_id FK
        ENUM status
    }

    REPORTS {
        UUID id PK
        UUID reporter_id FK
        ENUM target_type
        UUID target_id
        VARCHAR reason
        ENUM status
        DATETIME created_at
    }

    USERS ||--o{ ACTIVITIES : "enregistre"
    ACTIVITIES ||--|| FEED_POSTS : "publie"
    FEED_POSTS ||--o{ COMMENTS : "reçoit"
    FEED_POSTS ||--o{ POST_LIKES : "reçoit"
    FEED_POSTS ||--o{ REPORTS : "est signalé via"
    COMMENTS ||--o{ REPORTS : "est signalé via"
    USERS ||--o{ POST_LIKES : "effectue"
    USERS ||--o{ COMMENTS : "écrit"
    USERS ||--o{ FRIENDSHIPS : "initie"
    USERS ||--o{ REPORTS : "soumet"
```

### Schéma détaillé des tables

| Table | Colonnes principales | Relations |
|-------|----------------------|-----------|
| `users` | id PK, email UNIQUE, password_hash, username UNIQUE, is_admin, is_banned, created_at | → activities (1-N), ↔ users (amis) |
| `activities` | id PK, user_id FK, type ENUM(run/bike/swim/walk), distance_km, duration_min, date, notes | ← users, → feed_posts (1-1) |
| `feed_posts` | id PK, activity_id FK UNIQUE, user_id FK, likes_count, created_at | ← activities, → comments (1-N), ↔ users via post_likes |
| `comments` | id PK, post_id FK, user_id FK, content, created_at | ← feed_posts, ← users |
| `post_likes` | post_id FK, user_id FK — PK composite | Table de liaison N-N |
| `friendships` | user_id FK, friend_id FK — PK composite, status ENUM(pending/accepted) | Table auto-référentielle N-N |
| `reports` | id PK, reporter_id FK, target_type ENUM(comment/post), target_id, reason, status ENUM(pending/reviewed/dismissed), created_at | ← users, ← comments ou feed_posts |

---

## 4. Diagrammes de Séquence

### Flux 1 — Enregistrement d'une activité

```mermaid
sequenceDiagram
    actor U as Athlète (PWA)
    participant API as Flask API
    participant F as SweeloFacade
    participant DB as Base de données

    U->>API: POST /api/v1/activities<br/>Authorization: Bearer JWT<br/>{type, distance_km, duration_min, date}
    API->>API: Vérifie JWT → récupère current_user
    API->>F: create_activity(data, user_id)
    F->>DB: INSERT INTO activities
    F->>DB: INSERT INTO feed_posts (publication auto)
    API-->>U: 201 Created<br/>{activity}
```

### Flux 2 — Authentification & JWT

```mermaid
sequenceDiagram
    actor U as Athlète (PWA)
    participant API as Flask API
    participant DB as Base de données
    participant JWT as Flask-JWT

    U->>API: POST /api/v1/auth/login<br/>{email, password}
    API->>DB: SELECT * FROM users WHERE email = ?
    DB-->>API: user row
    API->>API: bcrypt.checkpw(password, hash) → OK
    API->>JWT: create_access_token(user_id, is_admin)
    JWT-->>API: "eyJ..."
    API-->>U: 200 OK {access_token: "eyJ..."}
    Note over U: Token stocké en cookie httpOnly
```

### Flux 3 — Consultation du feed social

```mermaid
sequenceDiagram
    actor U as Athlète (PWA)
    participant API as Flask API
    participant F as SweeloFacade
    participant DB as Base de données

    U->>API: GET /api/v1/feed?page=1<br/>Authorization: Bearer JWT
    API->>API: Décode JWT → current_user.id
    API->>F: get_feed(user_id, page=1)
    F->>DB: SELECT friend_ids FROM friendships WHERE user_id = ? AND status = accepted
    DB-->>F: [friend_ids]
    F->>DB: SELECT feed_posts + activities + users<br/>WHERE user_id IN (friend_ids)<br/>ORDER BY created_at DESC LIMIT 20
    DB-->>F: [{post, activity, user, likes_count}]
    F->>DB: CHECK post_likes WHERE user_id = current_user
    API-->>U: 200 OK [{post, activity, user,<br/>likes_count, user_has_liked, comments_count}]
```

### Flux 4 — Soumission d'un commentaire avec modération automatique

```mermaid
sequenceDiagram
    actor U as Utilisateur (PWA)
    participant API as Flask API
    participant F as SweeloFacade
    participant MOD as ModerationService
    participant OAI as OpenAI Moderation API
    participant DB as Base de données

    U->>API: POST /api/v1/feed/{id}/comments<br/>Authorization: Bearer JWT<br/>{content: "Super run !"}
    API->>API: Décode JWT → current_user
    API->>F: create_comment(post_id, user_id, content)
    F->>MOD: is_content_safe(content)
    MOD->>OAI: POST /v1/moderations {input: "Super run !"}
    OAI-->>MOD: {flagged: false, categories: {...}}

    alt Contenu approuvé
        MOD-->>F: {safe: true}
        F->>DB: INSERT INTO comments
        API-->>U: 201 Created {comment}
    else Contenu refusé
        MOD-->>F: {safe: false, reason: "harassment"}
        F-->>API: Erreur contenu refusé
        API-->>U: 400 Bad Request<br/>{error: "Contenu refusé (harassment)"}
    end
```

### Flux 5 — Signalement & traitement admin

```mermaid
sequenceDiagram
    actor U as Utilisateur (PWA)
    actor A as Admin (PWA)
    participant API as Flask API
    participant F as SweeloFacade
    participant DB as Base de données

    U->>API: POST /api/v1/feed/{id}/report<br/>{target_type: "comment", reason: "spam"}
    API->>F: report_content(reporter_id, target_type, target_id, reason)
    F->>DB: INSERT INTO reports (status: pending)
    API-->>U: 200 OK {message: "Signalement enregistré"}

    A->>API: GET /api/v1/admin/reports
    API->>DB: SELECT * FROM reports WHERE status = pending
    DB-->>API: [{report}]
    API-->>A: 200 OK [{reports}]

    A->>API: PUT /api/v1/admin/reports/{id}<br/>{action: "reviewed"}
    API->>F: update_report_status(report_id, reviewed)
    F->>DB: UPDATE reports SET status = reviewed

    A->>API: DELETE /api/v1/admin/comments/{id}
    API->>DB: DELETE FROM comments WHERE id = ?
    API-->>A: 204 No Content
```

---

## 5. Spécifications API

### APIs externes utilisées

| Service | Endpoint | Usage | Coût |
|---------|----------|-------|------|
| **OpenAI Moderation API** | `POST /v1/moderations` | Analyse automatique du contenu avant publication | **Gratuit** |

### Endpoints — Authentification

| Méthode | Route | Auth | Body | Réponse |
|---------|-------|------|------|---------|
| `POST` | `/api/v1/auth/register` | — | `{email, password, username}` | `201 {id, email, username}` |
| `POST` | `/api/v1/auth/login` | — | `{email, password}` | `200 {access_token}` |

### Endpoints — Activités

| Méthode | Route | Auth | Body / Params | Réponse |
|---------|-------|------|---------------|---------|
| `GET` | `/api/v1/activities` | JWT | `?page=1&limit=20` | `200 [{activity}]` |
| `POST` | `/api/v1/activities` | JWT | `{type, distance_km, duration_min, date, notes}` | `201 {activity}` |
| `GET` | `/api/v1/activities/:id` | JWT | — | `200 {activity}` / `404` |
| `DELETE` | `/api/v1/activities/:id` | JWT + owner | — | `204` / `403` |

### Endpoints — Feed & Social

| Méthode | Route | Auth | Body / Params | Réponse |
|---------|-------|------|---------------|---------|
| `GET` | `/api/v1/feed` | JWT | `?page=1` | `200 [{post, activity, user, likes_count, user_has_liked, comments_count}]` |
| `POST` | `/api/v1/feed/:id/like` | JWT | — | `200 {likes_count, liked: true}` |
| `POST` | `/api/v1/feed/:id/comments` | JWT | `{content}` | `201 {comment}` / `400 si modération` |
| `POST` | `/api/v1/feed/:id/report` | JWT | `{target_type, reason}` | `200 {message}` |
| `POST` | `/api/v1/users/:id/friend` | JWT | — | `200 {status: pending}` |
| `PUT` | `/api/v1/users/:id/friend` | JWT | `{action: accept/reject}` | `200 {status: accepted}` |

### Endpoints — Profil & Statistiques

| Méthode | Route | Auth | Réponse |
|---------|-------|------|---------|
| `GET` | `/api/v1/users/me` | JWT | `200 {user, activities_count, friends_count}` |
| `PUT` | `/api/v1/users/me` | JWT | `200 {user mis à jour}` |
| `GET` | `/api/v1/users/me/stats` | JWT | `200 {total_km, total_min, weekly_summary}` |

### Endpoints — Administration & Modération

| Méthode | Route | Auth | Body | Réponse |
|---------|-------|------|------|---------|
| `GET` | `/api/v1/admin/reports` | JWT + Admin | — | `200 [{report}]` |
| `PUT` | `/api/v1/admin/reports/:id` | JWT + Admin | `{action: reviewed/dismissed}` | `200 {report}` |
| `DELETE` | `/api/v1/admin/comments/:id` | JWT + Admin | — | `204` |
| `POST` | `/api/v1/admin/users/:id/ban` | JWT + Admin | — | `200 {message}` |

### Format de réponse standard

```json
// Succès
{
  "status": "success",
  "data": { "..." : "..." }
}

// Erreur
{
  "status": "error",
  "message": "Description de l'erreur",
  "code": 401
}
```

---

## 6. Modération de contenu

### Stratégie — 3 niveaux complémentaires

| Niveau | Mécanisme | Déclencheur |
|--------|-----------|-------------|
| **Préventif** | OpenAI Moderation API (gratuite) | Avant chaque INSERT commentaire / notes d'activité |
| **Réactif** | Signalement utilisateur | Bouton "Signaler" sur post ou commentaire |
| **Manuel** | Routes admin (`is_admin`) | Traitement de la file des signalements |

### Ce que détecte l'OpenAI Moderation API

| Catégorie | Description |
|-----------|-------------|
| `hate` | Discours haineux basé sur l'identité |
| `harassment` | Harcèlement ou intimidation |
| `violence` | Contenu violent ou menaçant |
| `sexual` | Contenu sexuellement explicite |
| `self-harm` | Contenu lié à l'automutilation |
| `spam` | Contenu répétitif ou non pertinent |

### Comportement en cas de contenu refusé

- Le commentaire ou la note d'activité **n'est pas inséré en base de données**
- L'API retourne un `400 Bad Request` avec la catégorie détectée
- En cas d'erreur de l'API OpenAI : le contenu est laissé passer (**fail open**) pour ne pas bloquer l'expérience utilisateur

### Table BDD — `reports`

| Colonne | Type | Contrainte | Description |
|---------|------|------------|-------------|
| `id` | VARCHAR(36) | PK | UUID |
| `reporter_id` | VARCHAR(36) | FK → users | Utilisateur qui signale |
| `target_type` | ENUM | `comment` / `post` | Type de contenu signalé |
| `target_id` | VARCHAR(36) | — | ID du contenu signalé |
| `reason` | VARCHAR(255) | — | Raison libre du signalement |
| `status` | ENUM | `pending` / `reviewed` / `dismissed` | État du traitement admin |
| `created_at` | DATETIME | — | Date du signalement |

---

## 7. SCM & QA

### Stratégie SCM (Git)

#### Structure des branches

```mermaid
gitGraph
    commit id: "init"
    branch develop
    checkout develop
    commit id: "setup Flask"
    branch feature/user-auth
    checkout feature/user-auth
    commit id: "add JWT auth"
    commit id: "add bcrypt"
    checkout develop
    merge feature/user-auth id: "merge auth"
    branch feature/activity-tracking
    checkout feature/activity-tracking
    commit id: "add Activity model"
    checkout develop
    merge feature/activity-tracking id: "merge tracking"
    branch feature/moderation
    checkout feature/moderation
    commit id: "add ModerationService"
    commit id: "add reports table"
    checkout develop
    merge feature/moderation id: "merge moderation"
    checkout main
    merge develop id: "v1.0.0" tag: "v1.0.0"
```

#### Types de branches

| Branche | Usage |
|---------|-------|
| `main` | Code de production stable — merge via PR validée uniquement |
| `develop` | Branche d'intégration continue, toujours déployable |
| `feature/xxx` | Nouvelle fonctionnalité ex : `feature/feed-social` |
| `fix/xxx` | Correction de bug ex : `fix/feed-pagination` |
| `chore/xxx` | Config, dépendances, CI ex : `chore/add-pytest-config` |

#### Conventions de commits

| Préfixe | Usage |
|---------|-------|
| `feat:` | Nouvelle fonctionnalité |
| `fix:` | Correction de bug |
| `test:` | Ajout ou modification de tests |
| `docs:` | Documentation |
| `refactor:` | Refactoring sans changement de comportement |
| `chore:` | Config, dépendances, CI |

**Exemple :** `feat: add POST /activities endpoint`

#### Processus de merge

- Toute fonctionnalité passe par une **Pull Request** vers `develop`
- **Revue de code obligatoire** par l'autre membre de l'équipe
- Tous les tests doivent passer avant le merge
- Squash + merge recommandé pour garder l'historique propre
- Merge dans `main` uniquement pour les releases stables (tag de version)

### Stratégie QA (Tests)

| Type | Outil | Scope | Objectif |
|------|-------|-------|----------|
| **Unitaires** | `pytest` | Modèles, Façade, ModerationService (mock) | Couverture ≥ 80% |
| **Intégration** | `pytest` + Flask test client | Tous les endpoints API, JWT sur routes protégées, modération | Flux CRUD complets |
| **Manuels** | Postman (collection partagée) | Flux end-to-end, cas d'erreur (400, 401, 403, 404, 409) | Validation UX |
| **CI** | GitHub Actions | `pytest` + `flake8` lint sur chaque push | Blocage merge si échec |

#### Structure des tests

```
tests/
├── unit/
│   ├── test_user_model.py
│   ├── test_activity_model.py
│   ├── test_facade.py
│   └── test_moderation_service.py  # mock OpenAI Moderation API
├── integration/
│   ├── test_auth_endpoints.py
│   ├── test_activity_endpoints.py
│   ├── test_feed_endpoints.py
│   └── test_admin_endpoints.py
└── conftest.py                     # fixtures (app, db, JWT tokens)
```

#### Exemple de test unitaire

```python
# tests/unit/test_activity_model.py
def test_create_activity_run():
    activity = Activity(type="run", distance_km=10, duration_min=60, date="2026-05-22")
    assert activity.type == "run"
    assert activity.distance_km == 10

def test_create_activity_missing_type():
    with pytest.raises(ValueError):
        Activity(type=None, distance_km=5, duration_min=30, date="2026-05-22")
```

---

## 8. Justifications Techniques

### Flask + Flask-RESTX

**Choix :** Framework micro Python léger pour API REST.
**Justification :** Flask-RESTX impose une structure par namespaces et génère automatiquement la documentation Swagger. Django serait surdimensionné pour un MVP de 2 développeurs. Nous avions déjà utilisé Flask lors de projets précédents à Holberton, ce qui nous a permis de démarrer rapidement sans avoir à réapprendre un nouveau framework.

### SQLAlchemy (ORM) + Repository Pattern

**Choix :** ORM Python avec pattern Repository.
**Justification :** Abstraction complète de la BDD — passage de SQLite (dev) à MySQL (prod) sans modifier le code applicatif. Le Repository Pattern découple la logique métier de la persistance. SQLAlchemy faisant partie de nos outils déjà maîtrisés, nous avons pu nous concentrer sur la logique métier plutôt que sur la prise en main de l'outil.

### JWT (Flask-JWT-Extended)

**Choix :** Authentification stateless par tokens JWT.
**Justification :** Aucune session serveur à gérer — scalabilité horizontale facilitée. Le token contient l'`id`, le rôle (`is_admin`) et le statut (`is_banned`) de l'utilisateur, éliminant un aller-retour BDD supplémentaire par requête protégée. Compatible PWA sans cookie de session traditionnel. Nous avions déjà manipulé JWT dans des projets antérieurs, ce qui a facilité son intégration.

### bcrypt

**Choix :** Algorithme de hashage adaptatif pour les mots de passe.
**Justification :** bcrypt inclut un salt automatique et est résistant aux attaques brute-force et rainbow tables. Recommandation officielle de l'OWASP pour le stockage des mots de passe. Ayant déjà utilisé bcrypt dans nos projets Holberton, son intégration était naturelle et sans courbe d'apprentissage supplémentaire.

### Façade Pattern

**Choix :** Couche d'orchestration entre routes et repositories.
**Justification :** Chaque endpoint Flask appelle uniquement la `SweeloFacade`, qui orchestre les repositories et le service de modération. Cela rend le code testable unitairement sans démarrer le serveur web, et facilite l'évolution des règles métier sans toucher aux routes. Ce pattern nous était familier depuis nos projets précédents, ce qui nous a permis de l'appliquer directement sans perte de temps.

### OpenAI Moderation API — Modération de contenu

**Choix :** API gratuite d'OpenAI pour analyser le contenu avant publication.
**Justification :** La clé `OPENAI_API_KEY` est simple à configurer et l'API est gratuite. Elle couvre 6 catégories de contenu sensible et s'intègre en un seul appel HTTP. La stratégie **fail open** (laisser passer en cas d'erreur API) garantit une expérience utilisateur fluide même en cas de panne du service externe.

### PWA Vanilla JS

**Choix :** Progressive Web App en JavaScript natif sans framework.
**Justification :** Aucune dépendance frontend, chargement quasi-instantané. La Fetch API native suffit pour consommer l'API REST. Le **Service Worker** permet le mode offline — essentiel pour une app sportive utilisée en extérieur avec une connexion instable. Nous maîtrisions déjà le JavaScript vanilla depuis le début de notre cursus Holberton, ce qui nous a évité d'avoir à apprendre React ou Vue pour ce MVP.

### SQLite (dev) → MySQL (prod)

**Choix :** Double configuration base de données selon l'environnement.
**Justification :** SQLite ne nécessite aucune configuration pour le développement local (fichier unique `.db`). La migration vers MySQL en production est transparente grâce à SQLAlchemy — une seule variable d'environnement `DATABASE_URL` à changer. MySQL et SQLite faisant partie de notre stack habituelle à Holberton, nous n'avons pas eu à nous former sur de nouveaux outils.

---

*Documentation rédigée dans le cadre du cursus Holberton School — RNCP Niveau 5*
