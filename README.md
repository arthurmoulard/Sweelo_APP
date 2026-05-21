# SWEELO — Stage 3: Technical Documentation

> Application de tracking sportif, défis sociaux et coaching IA pour athlètes amateurs  
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
6. [SCM & QA](#6-scm--qa)
7. [Justifications Techniques](#7-justifications-techniques)

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
| US-06 | En tant qu'athlète, je veux créer ou rejoindre un défi (distance, durée, calories), afin de me mesurer à mes amis. | 🔴 Must |
| US-07 | En tant qu'athlète, je veux voir le classement d'un défi en temps réel, afin de connaître ma position. | 🔴 Must |

#### Should Have — Valeur ajoutée importante

| # | User Story | Priorité |
|---|------------|----------|
| US-08 | En tant qu'athlète, je veux recevoir une recommandation de coaching IA après chaque activité, afin d'améliorer mes performances. | 🟠 Should |
| US-09 | En tant qu'athlète, je veux gagner des points à chaque activité enregistrée, afin de débloquer des récompenses. | 🟠 Should |
| US-10 | En tant qu'athlète, je veux ajouter des amis via leur identifiant, afin de suivre leurs activités. | 🟠 Should |
| US-11 | En tant qu'athlète, je veux liker ou commenter une activité du feed, afin d'interagir avec mes amis. | 🟠 Should |

#### Could Have / Won't Have

| # | User Story | Priorité |
|---|------------|----------|
| US-12 | En tant qu'athlète, je veux tracker mon activité en temps réel via GPS depuis mon smartphone. | 🟡 Could |
| US-13 | En tant qu'athlète, je veux connecter ma montre via Bluetooth pour importer mes données automatiquement. | ⚪ Won't (MVP) |
| US-14 | En tant qu'athlète, je veux partager mon activité sur Instagram ou Twitter. | ⚪ Won't (MVP) |

### Maquettes — Écrans principaux

Les 4 écrans ci-dessous sont à réaliser sur Figma et à joindre en annexe :

| Écran | Contenu attendu | User Stories couvertes |
|-------|-----------------|------------------------|
| **Dashboard** | Résumé semaine, dernière activité, points cumulés, bouton "Enregistrer" | US-03, US-04, US-09 |
| **Feed social** | Liste activités amis, bouton like/commentaire, carte d'activité | US-05, US-11 |
| **Défis** | Mes défis actifs, classement, bouton rejoindre/créer | US-06, US-07 |
| **Profil** | Stats personnelles, historique, badges/récompenses, liste amis | US-04, US-09, US-10 |

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
        REPO[Repositories<br/>UserRepo · ActivityRepo<br/>ChallengeRepo · FeedRepo]
        AI_SVC[AICoachingService]
    end

    subgraph Data["🗄️ Persistance"]
        SQLITE[(SQLite<br/>Développement)]
        MYSQL[(MySQL<br/>Production)]
    end

    subgraph External["🌐 Services externes"]
        OPENAI[OpenAI API<br/>GPT-4o<br/>Coaching IA]
    end

    UI -->|HTTPS / JSON + Bearer JWT| RESTX
    SW -.->|Cache offline| UI
    RESTX --> JWT
    JWT --> FACADE
    FACADE --> REPO
    FACADE --> AI_SVC
    REPO -->|SQLAlchemy ORM| SQLITE
    REPO -->|SQLAlchemy ORM| MYSQL
    AI_SVC -->|POST /chat/completions| OPENAI
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
| Coaching IA | OpenAI API (GPT-4o) | Génération de recommandations post-activité |
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
        +Int total_points
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
        +Int calories
        +Date date
        +String notes
        +create()
        +delete()
        +compute_points()
        +to_dict()
    }

    class Challenge {
        +UUID id
        +String title
        +UUID creator_id
        +Enum type
        +Float target_value
        +Date start_date
        +Date end_date
        +Bool is_active
        +create()
        +join(user_id)
        +get_leaderboard()
        +to_dict()
    }

    class ChallengeParticipant {
        +UUID id
        +UUID challenge_id
        +UUID user_id
        +Float current_value
        +DateTime joined_at
        +update_progress()
        +get_rank()
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

    class AICoaching {
        +UUID id
        +UUID activity_id
        +String recommendation
        +DateTime generated_at
        +generate(activity)
        +to_dict()
    }

    class SweeloFacade {
        +UserRepository user_repo
        +ActivityRepository activity_repo
        +ChallengeRepository challenge_repo
        +FeedRepository feed_repo
        +AICoachingService ai_service
        +create_activity(data, user_id)
        +join_challenge(challenge_id, user_id)
        +get_feed(user_id, page)
        +get_coaching(activity_id)
    }

    User "1" --> "N" Activity : possède
    User "1" --> "N" Challenge : crée
    User "N" --> "N" Challenge : participe via ChallengeParticipant
    User "N" --> "N" User : amis via Friendship
    Activity "1" --> "1" FeedPost : publie
    Activity "1" --> "1" AICoaching : génère
    FeedPost "1" --> "N" Comment : contient
    Challenge "1" --> "N" ChallengeParticipant : regroupe
    SweeloFacade --> User
    SweeloFacade --> Activity
    SweeloFacade --> Challenge
    SweeloFacade --> FeedPost
    SweeloFacade --> AICoaching
```

### Diagramme Entité-Relation (ER)

```mermaid
erDiagram
    USERS {
        UUID id PK
        VARCHAR email UK
        VARCHAR password_hash
        VARCHAR username UK
        INT total_points
        DATETIME created_at
    }

    ACTIVITIES {
        UUID id PK
        UUID user_id FK
        ENUM type
        FLOAT distance_km
        INT duration_min
        INT calories
        DATE date
        TEXT notes
    }

    CHALLENGES {
        UUID id PK
        VARCHAR title
        UUID creator_id FK
        ENUM type
        FLOAT target_value
        DATE start_date
        DATE end_date
        BOOL is_active
    }

    CHALLENGE_PARTICIPANTS {
        UUID id PK
        UUID challenge_id FK
        UUID user_id FK
        FLOAT current_value
        DATETIME joined_at
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

    AI_COACHING {
        UUID id PK
        UUID activity_id FK
        TEXT recommendation
        DATETIME generated_at
    }

    USERS ||--o{ ACTIVITIES : "enregistre"
    USERS ||--o{ CHALLENGES : "crée"
    USERS ||--o{ CHALLENGE_PARTICIPANTS : "participe"
    CHALLENGES ||--o{ CHALLENGE_PARTICIPANTS : "regroupe"
    ACTIVITIES ||--|| FEED_POSTS : "publie"
    ACTIVITIES ||--o| AI_COACHING : "génère"
    FEED_POSTS ||--o{ COMMENTS : "reçoit"
    FEED_POSTS ||--o{ POST_LIKES : "reçoit"
    USERS ||--o{ POST_LIKES : "effectue"
    USERS ||--o{ COMMENTS : "écrit"
    USERS ||--o{ FRIENDSHIPS : "initie"
```

### Schéma détaillé des tables

| Table | Colonnes principales | Relations |
|-------|----------------------|-----------|
| `users` | id PK, email UNIQUE, password_hash, username UNIQUE, total_points, created_at | → activities (1-N), → challenges (créateur), ↔ users (amis) |
| `activities` | id PK, user_id FK, type ENUM(run/bike/swim/walk), distance_km, duration_min, calories, date, notes | ← users, → feed_posts (1-1), → ai_coaching (1-1) |
| `challenges` | id PK, title, creator_id FK, type ENUM(distance/duration/calories), target_value, start_date, end_date, is_active | ← users, ↔ users via challenge_participants |
| `challenge_participants` | id PK, challenge_id FK, user_id FK, current_value, joined_at | Table de liaison + progression |
| `feed_posts` | id PK, activity_id FK UNIQUE, user_id FK, likes_count, created_at | ← activities, → comments (1-N), ↔ users via post_likes |
| `comments` | id PK, post_id FK, user_id FK, content, created_at | ← feed_posts, ← users |
| `post_likes` | post_id FK, user_id FK — PK composite | Table de liaison N-N |
| `friendships` | user_id FK, friend_id FK — PK composite, status ENUM(pending/accepted) | Table auto-référentielle N-N |
| `ai_coaching` | id PK, activity_id FK UNIQUE, recommendation TEXT, generated_at | ← activities |

---

## 4. Diagrammes de Séquence

### Flux 1 — Enregistrement d'une activité + coaching IA

```mermaid
sequenceDiagram
    actor U as Athlète (PWA)
    participant API as Flask API
    participant F as SweeloFacade
    participant DB as Base de données
    participant AI as OpenAI API

    U->>API: POST /api/v1/activities<br/>Authorization: Bearer JWT<br/>{type, distance_km, duration_min, date}
    API->>API: Vérifie JWT → récupère current_user
    API->>F: create_activity(data, user_id)
    F->>DB: INSERT INTO activities
    F->>DB: compute_points() → UPDATE users.total_points
    F->>DB: INSERT INTO feed_posts (publication auto)
    F->>AI: POST /chat/completions<br/>{prompt avec stats activité}
    AI-->>F: 200 OK {recommendation: "..."}
    F->>DB: INSERT INTO ai_coaching
    API-->>U: 201 Created<br/>{activity, coaching_tip, points_earned}
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

### Flux 3 — Rejoindre un défi & mise à jour du classement

```mermaid
sequenceDiagram
    actor U as Athlète (PWA)
    participant API as Flask API
    participant F as SweeloFacade
    participant DB as Base de données

    U->>API: POST /api/v1/challenges/{id}/join<br/>Authorization: Bearer JWT
    API->>API: Décode JWT → current_user
    API->>F: join_challenge(challenge_id, user_id)
    F->>DB: SELECT challenge WHERE id = ? AND is_active = True
    DB-->>F: challenge row
    F->>DB: CHECK challenge_participants (déjà inscrit ?)
    F->>DB: INSERT INTO challenge_participants
    F->>DB: Calcule current_value depuis activités existantes
    F->>DB: UPDATE challenge_participants SET current_value
    F->>DB: SELECT leaderboard ORDER BY current_value DESC
    DB-->>F: [{rank, username, value}]
    API-->>U: 200 OK {rank, current_value, leaderboard}
```

### Flux 4 — Consultation du feed social

```mermaid
sequenceDiagram
    actor U as Athlète (PWA)
    participant API as Flask API
    participant F as SweeloFacade
    participant DB as Base de données

    U->>API: GET /api/v1/feed?page=1<br/>Authorization: Bearer JWT
    API->>API: Décode JWT → current_user.id
    API->>F: get_feed(user_id, page=1)
    F->>DB: SELECT friend_ids FROM friendships<br/>WHERE user_id = ? AND status = 'accepted'
    DB-->>F: [friend_ids]
    F->>DB: SELECT feed_posts + activities + users<br/>WHERE user_id IN (friend_ids)<br/>ORDER BY created_at DESC LIMIT 20
    DB-->>F: [{post, activity, user, likes_count}]
    F->>DB: CHECK post_likes WHERE user_id = current_user (pour user_has_liked)
    API-->>U: 200 OK [{post, activity, user,<br/>likes_count, user_has_liked, comments_count}]
```

---

## 5. Spécifications API

### APIs externes utilisées

| Service | Endpoint utilisé | Usage | Justification |
|---------|-----------------|-------|---------------|
| **OpenAI API** (GPT-4o) | `POST /v1/chat/completions` | Génération de recommandations coaching après chaque activité | Modèle puissant pour analyse contextuelle sportive. Appel côté serveur pour protéger la clé API. Réponse mise en cache en BDD. |

### Endpoints internes — Authentification

| Méthode | Route | Auth | Body | Réponse |
|---------|-------|------|------|---------|
| `POST` | `/api/v1/auth/register` | — | `{email, password, username}` | `201 {id, email, username}` |
| `POST` | `/api/v1/auth/login` | — | `{email, password}` | `200 {access_token}` |

### Endpoints internes — Activités

| Méthode | Route | Auth | Body / Params | Réponse |
|---------|-------|------|---------------|---------|
| `GET` | `/api/v1/activities` | JWT | `?page=1&limit=20` | `200 [{activity}]` de l'user courant |
| `POST` | `/api/v1/activities` | JWT | `{type, distance_km, duration_min, calories, date, notes}` | `201 {activity, coaching_tip, points_earned}` |
| `GET` | `/api/v1/activities/:id` | JWT | — | `200 {activity + coaching}` / `404` |
| `DELETE` | `/api/v1/activities/:id` | JWT + owner | — | `204` / `403` |

### Endpoints internes — Défis

| Méthode | Route | Auth | Body / Params | Réponse |
|---------|-------|------|---------------|---------|
| `GET` | `/api/v1/challenges` | JWT | `?active=true` | `200 [{challenge, participants_count}]` |
| `POST` | `/api/v1/challenges` | JWT | `{title, type, target_value, start_date, end_date}` | `201 {challenge}` |
| `POST` | `/api/v1/challenges/:id/join` | JWT | — | `200 {rank, current_value, leaderboard}` |
| `GET` | `/api/v1/challenges/:id/leaderboard` | JWT | — | `200 [{rank, username, value}]` |

### Endpoints internes — Feed & Social

| Méthode | Route | Auth | Body / Params | Réponse |
|---------|-------|------|---------------|---------|
| `GET` | `/api/v1/feed` | JWT | `?page=1` | `200 [{post, activity, user, likes_count, user_has_liked, comments_count}]` |
| `POST` | `/api/v1/feed/:id/like` | JWT | — | `200 {likes_count, liked: true}` |
| `POST` | `/api/v1/feed/:id/comments` | JWT | `{content}` | `201 {comment}` |
| `POST` | `/api/v1/users/:id/friend` | JWT | — | `200 {status: "pending"}` |
| `PUT` | `/api/v1/users/:id/friend` | JWT | `{action: "accept"/"reject"}` | `200 {status: "accepted"}` |

### Endpoints internes — Profil & Statistiques

| Méthode | Route | Auth | Réponse |
|---------|-------|------|---------|
| `GET` | `/api/v1/users/me` | JWT | `200 {user, total_points, activities_count, friends_count}` |
| `PUT` | `/api/v1/users/me` | JWT | `200 {user mis à jour}` |
| `GET` | `/api/v1/users/me/stats` | JWT | `200 {total_km, total_min, total_calories, weekly_summary}` |

### Format de réponse standard

```json
// Succès
{
  "status": "success",
  "data": { ... }
}

// Erreur
{
  "status": "error",
  "message": "Description de l'erreur",
  "code": 401
}
```

---

## 6. SCM & QA

### Stratégie SCM (Git)

#### Branches

```
main
 └── develop
      ├── feature/user-auth
      ├── feature/activity-tracking
      ├── feature/challenge-leaderboard
      ├── feature/feed-social
      ├── feature/ai-coaching
      ├── fix/feed-pagination
      └── chore/add-pytest-config
```

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
    commit id: "add AI coaching"
    checkout develop
    merge feature/activity-tracking id: "merge tracking"
    checkout main
    merge develop id: "v1.0.0" tag: "v1.0.0"
```

#### Conventions de commits

| Préfixe | Usage |
|---------|-------|
| `feat:` | Nouvelle fonctionnalité |
| `fix:` | Correction de bug |
| `test:` | Ajout ou modification de tests |
| `docs:` | Documentation |
| `refactor:` | Refactoring sans changement de comportement |
| `chore:` | Config, dépendances, CI |

**Exemple :** `feat: add POST /activities endpoint with AI coaching`

#### Processus de merge

- Toute fonctionnalité passe par une **Pull Request** vers `develop`
- **Revue de code obligatoire** par l'autre membre de l'équipe
- Tous les tests doivent passer avant le merge
- Squash + merge recommandé pour garder l'historique propre
- Merge dans `main` uniquement pour les releases stables (tag de version)

### Stratégie QA (Tests)

#### Types de tests

| Type | Outil | Scope | Objectif |
|------|-------|-------|----------|
| **Unitaires** | `pytest` | Modèles, Façade, calcul de points, service IA (mock) | Couverture ≥ 80% |
| **Intégration** | `pytest` + Flask test client | Tous les endpoints API, JWT sur routes protégées | Flux CRUD complets |
| **Manuels** | Postman (collection partagée) | Flux end-to-end, cas d'erreur (401, 403, 404, 409) | Validation UX |
| **CI** | GitHub Actions | `pytest` + `flake8` lint sur chaque push | Blocage merge si échec |

#### Structure des tests

```
tests/
├── unit/
│   ├── test_user_model.py
│   ├── test_activity_model.py
│   ├── test_challenge_model.py
│   ├── test_facade.py
│   └── test_ai_service.py       # mock OpenAI
├── integration/
│   ├── test_auth_endpoints.py
│   ├── test_activity_endpoints.py
│   ├── test_challenge_endpoints.py
│   └── test_feed_endpoints.py
└── conftest.py                  # fixtures (app, db, JWT tokens)
```

#### Exemple de test unitaire

```python
# tests/unit/test_activity_model.py
def test_compute_points_run():
    activity = Activity(type="run", distance_km=10, duration_min=60)
    assert activity.compute_points() == 100  # 10 pts/km

def test_compute_points_minimum():
    activity = Activity(type="walk", distance_km=0.5, duration_min=10)
    assert activity.compute_points() >= 5  # points minimum
```

---

## 7. Justifications Techniques

### Flask + Flask-RESTX

**Choix :** Framework micro Python léger pour API REST.  
**Justification :** Flask-RESTX impose une structure par namespaces et génère automatiquement la documentation Swagger. Django serait surdimensionné pour un MVP de 2 développeurs sans beaucoup d'ORM natif — Flask laisse le contrôle total sur l'architecture.

### SQLAlchemy (ORM) + Repository Pattern

**Choix :** ORM Python avec pattern Repository.  
**Justification :** Abstraction complète de la BDD — passage de SQLite (dev) à MySQL (prod) sans modifier le code applicatif. Le Repository Pattern découple la logique métier de la persistance, permettant de tester avec une `InMemoryRepository` sans base de données réelle.

### JWT (Flask-JWT-Extended)

**Choix :** Authentification stateless par tokens JWT.  
**Justification :** Aucune session serveur à gérer — scalabilité horizontale facilitée. Le token contient l'`id` et le rôle (`is_admin`) de l'utilisateur, éliminant un aller-retour BDD supplémentaire par requête protégée. Compatible PWA sans cookie de session traditionnel.

### bcrypt

**Choix :** Algorithme de hashage adaptatif pour les mots de passe.  
**Justification :** bcrypt inclut un salt automatique et est résistant aux attaques brute-force et rainbow tables grâce à son coût computationnel réglable. Recommandation officielle de l'OWASP pour le stockage des mots de passe. Supérieur à SHA-256 ou MD5 pour cet usage.

### Façade Pattern

**Choix :** Couche d'orchestration entre routes et repositories.  
**Justification :** Chaque endpoint Flask appelle uniquement la `SweeloFacade`, qui orchestre les repositories et services externes (IA). Cela rend le code testable unitairement sans démarrer le serveur web, et facilite l'évolution des règles métier sans toucher aux routes.

### OpenAI API (GPT-4o) — Coaching IA

**Choix :** API externe LLM pour les recommandations sportives personnalisées.  
**Justification :** GPT-4o offre une capacité de contextualisation supérieure pour l'analyse sportive. L'appel est effectué **côté serveur** (via Flask) pour protéger la clé API. La recommandation générée est mise en cache en BDD dans `ai_coaching`, évitant des appels redondants pour la même activité.

### PWA Vanilla JS

**Choix :** Progressive Web App en JavaScript natif sans framework.  
**Justification :** Aucune dépendance frontend, chargement quasi-instantané. La Fetch API native suffit pour consommer l'API REST. Le **Service Worker** permet le mode offline — essentiel pour une app sportive utilisée en extérieur avec une connexion instable. React ou Vue ajouteraient une complexité de build non justifiée pour le MVP.

### SQLite (dev) → MySQL (prod)

**Choix :** Double configuration base de données selon l'environnement.  
**Justification :** SQLite ne nécessite aucune configuration pour le développement local (fichier unique `.db`). La migration vers MySQL en production est transparente grâce à SQLAlchemy — une seule variable d'environnement `DATABASE_URL` à changer. MySQL gère la concurrence multi-utilisateurs et les volumes de données attendus en production.

---

*Documentation rédigée dans le cadre du cursus Holberton School — RNCP Niveau 5*