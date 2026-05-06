# EPIC-02 - Collecte endpoint et télémétrie

**Lien**: [Gestion de projet §8](../rendu_principal.md#8-product-backlog-structuré) | [§9 Features](../rendu_principal.md#9-features-par-epic)

## Objectif
Recevoir `heartbeat` et `events` depuis le `serveur-endpoint` (Priorité P1)

## User Stories

| ID | User Story | SP | Sprint | Owner | Issue # |
|---|---|---|---|---|---|
| US-02.1 | Heartbeat endpoint | 3 | Sprint 2 | Ken Thompson | |
| US-02.2 | Events ingestion | 5 | Sprint 2 | Ken Thompson | |
| US-02.3 | Auth agent (secret) | 5 | Sprint 2 | Radia Perlman | |

## Tasks Techniques (US-02.1 - Heartbeat)

- [x] Schéma Pydantic `HeartbeatSchema` - Ken Thompson
- [x] Route `POST /heartbeat` (FastAPI) - Ken Thompson
- [x] Persistance PostgreSQL (modèle `Heartbeat`) - Barbara Liskov
- [x] Vue liste dernier heartbeat (API) - Tim Berners-Lee
- [x] Tests ingestion heartbeat - Margaret Hamilton
- [x] Agent secret configuré - Linus Torvalds

## Tasks Techniques (US-02.2 - Events)

- [x] Schéma `EventSchema` - Ken Thompson
- [x] Route `POST /events` - Ken Thompson
- [x] Validation payload JSON - Radia Perlman
- [x] Persistance events PostgreSQL - Barbara Liskov
- [x] Vue liste events (API + UI) - Tim Berners-Lee
- [x] Tests events - Margaret Hamilton

## Tasks Techniques (US-02.3 - Auth Agent)

- [x] Définir secret agent (config/env) - Radia Perlman
- [x] Middleware auth agent (API key) - Ken Thompson
- [x] Rejet requêtes non autorisées - Ken Thompson
- [x] Logs tentatives auth - Margaret Hamilton

## Definition of Ready (US-02.1)

- [x] Schéma heartbeat défini
- [x] Route `/heartbeat` existe dans `serveur-soc`
- [x] Format JSON validé
- [x] Agent secret configuré

## Definition of Done (US-02.1)

- [x] Dernier heartbeat visible côté `serveur-soc`
- [x] Timestamp persistant PostgreSQL
- [x] Agent authentifié
- [x] JSON valide reçu
- [x] Preuve: heartbeat dans dashboard

## Acceptance Criteria

| Critère | Preuve attendue |
|---|---|
| Heartbeat reçu | 200 OK, JSON persisté |
| Heartbeat visible | Dashboard affiche dernier heartbeat |
| Agent non auth | 401 Unauthorized |

## GitHub Project

- Status actuel recommandé : `Done`
- Labels recommandés : `epic`, `user-story`, `backend`, `telemetry`, `security`
- Issues GitHub : à compléter dans la colonne `Issue #`
