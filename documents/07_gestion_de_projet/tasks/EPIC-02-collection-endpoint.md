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

- [ ] Schéma Pydantic `HeartbeatSchema` - Ken Thompson
- [ ] Route `POST /heartbeat` (FastAPI) - Ken Thompson
- [ ] Persistance PostgreSQL (modèle `Heartbeat`) - Barbara Liskov
- [ ] Vue liste dernier heartbeat (API) - Tim Berners-Lee
- [ ] Tests ingestion heartbeat - Margaret Hamilton
- [x] Agent secret configuré - Linus Torvalds

## Tasks Techniques (US-02.2 - Events)

- [ ] Schéma `EventSchema` - Ken Thompson
- [ ] Route `POST /events` - Ken Thompson
- [ ] Validation payload JSON - Radia Perlman
- [ ] Persistance events PostgreSQL - Barbara Liskov
- [ ] Vue liste events (API + UI) - Tim Berners-Lee
- [ ] Tests events - Margaret Hamilton

## Tasks Techniques (US-02.3 - Auth Agent)

- [x] Définir secret agent (config/env) - Radia Perlman
- [ ] Middleware auth agent (API key) - Ken Thompson
- [ ] Rejet requêtes non autorisées - Ken Thompson
- [ ] Logs tentatives auth - Margaret Hamilton

## Definition of Ready (US-02.1)

- [ ] Schéma heartbeat défini
- [ ] Route `/heartbeat` existe dans `serveur-soc`
- [ ] Format JSON validé
- [x] Agent secret configuré

## Definition of Done (US-02.1)

- [ ] Dernier heartbeat visible côté `serveur-soc`
- [ ] Timestamp persistant PostgreSQL
- [ ] Agent authentifié
- [ ] JSON valide reçu
- [ ] Preuve: heartbeat dans dashboard

## Acceptance Criteria

| Critère | Preuve attendue |
|---|---|
| Heartbeat reçu | 200 OK, JSON persisté |
| Heartbeat visible | Dashboard affiche dernier heartbeat |
| Agent non auth | 401 Unauthorized |

## GitHub Project

- Status actuel recommandé : `Backlog`
- Labels recommandés : `epic`, `user-story`, `backend`, `telemetry`, `security`
- Issues GitHub : à compléter dans la colonne `Issue #`
