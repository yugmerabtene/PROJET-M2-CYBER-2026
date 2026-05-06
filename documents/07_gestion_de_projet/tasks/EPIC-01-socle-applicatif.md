# EPIC-01 - Socle applicatif et sécurité

**Lien**: [Gestion de projet §8](../rendu_principal.md#8-product-backlog-structuré) | [§9 Features](../rendu_principal.md#9-features-par-epic)

## Objectif
Poser les bases FastAPI, authentification, rôles, configuration et santé applicative (Priorité P1)

## User Stories

| ID | User Story | SP | Sprint | Owner | Issue # |
|---|---|---|---|---|---|
| US-01.1 | Authentification utilisateur | 5 | Sprint 1 | Barbara Liskov | |
| US-01.2 | Contrôle d'accès (rôles admin/analyst) | 3 | Sprint 1 | Barbara Liskov | |
| US-01.3 | Santé applicative (/health endpoint) | 2 | Sprint 1 | Ken Thompson | |

## Tasks Techniques (US-01.1 - Authentification)

- [x] Créer modèle `User` (SQLAlchemy) - Barbara Liskov
- [x] Implémenter route `POST /login` (FastAPI) - Barbara Liskov
- [x] Gérer JWT token/session - Barbara Liskov
- [x] Protéger routes privées avec middleware - Ken Thompson
- [x] Tests unitaires auth - Margaret Hamilton
- [x] Documentation API auth - Linus Torvalds

## Tasks Techniques (US-01.2 - Rôles)

- [x] Définir `admin` / `analyst` - Barbara Liskov
- [x] Middleware contrôle d'accès - Ken Thompson
- [x] Tests refus d'action - Margaret Hamilton
- [x] Documentation rôles - Linus Torvalds

## Tasks Techniques (US-01.3 - Santé)

- [x] Créer endpoint `GET /health` - Ken Thompson
- [x] Logger erreurs basiques - Ken Thompson
- [x] Tests endpoint santé - Margaret Hamilton
- [x] Documentation `/health` - Linus Torvalds

## Definition of Ready (US-01.1)

- [x] Schéma utilisateur défini
- [x] Route `/login` créée dans `serveur-soc`
- [x] Payload JWT prêt
- [x] Test de connexion initial configuré

## Definition of Done (US-01.1)

- [x] Connexion valide acceptée
- [x] Token JWT retourné
- [x] Route `/me` renvoie utilisateur
- [x] Accès refusé sans token
- [x] Preuve: capture login réussi/échoué

## Acceptance Criteria

| Critère | Preuve attendue |
|---|---|
| Connexion valide | Token JWT reçu, 200 OK |
| Connexion invalide | 401 Unauthorized |
| Accès sans token | 403 Forbidden |
| Route `/me` | JSON utilisateur connecté |

## GitHub Project

- Status actuel recommandé : `Done`
- Labels recommandés : `epic`, `user-story`, `backend`, `security`, `qa`
- Issues GitHub : à compléter dans la colonne `Issue #`
