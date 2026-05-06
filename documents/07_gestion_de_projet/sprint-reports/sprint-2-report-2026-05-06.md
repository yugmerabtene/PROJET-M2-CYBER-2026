# Rapport Sprint 2 - 2026-05-06

## Synthese

Sprint 2 vise a fermer la boucle agent → API → base de données pour la télémétrie DevinciWatch. Les endpoints `POST /telemetry/heartbeat` et `POST /telemetry/events` sont implémentés, avec les modèles SQLAlchemy, les schémas Pydantic, les services métier et les tests de validation. Le statut QA est **14/14 tests passants**.

## Perimetre Sprint 2

| Story | Epic | SP | Owner | Statut | Validation QA |
|---|---|---:|---|---|---|
| US-02.1 | EPIC-02 | 3 | Ken Thompson | Done | Modeles + routes + schemas + tests passes |
| US-02.2 | EPIC-02 | 5 | Ken Thompson | Done | Ingestion events + validation Pydantic + tests passes |
| US-02.3 | EPIC-02 | 5 | Radia Perlman | Done | Middleware `require_agent` implémente et teste |

## Verification Technique

| Controle | Resultat | Preuve |
|---|---|---|
| Compilation backend | OK | `python3 -m compileall app` |
| Tests structure backend | 10/10 passes | `tests/run_tests.py` |
| Tests schemas telemetry | 2/2 passes | `tests/run_tests.py` |
| Tests synchro docs | 2/2 passes | `tests/run_tests.py` |
| Total tests | **14/14 passes** | |

## Fichiers Crees

| Fichier | Description |
|---|---|
| `backend/app/telemetry/models.py` | Modeles SQLAlchemy: `Agent`, `Heartbeat`, `TelemetryEvent` |
| `backend/app/telemetry/schemas.py` | Schemas Pydantic: `HeartbeatPayload`, `EventPayload`, reponses |
| `backend/app/telemetry/service.py` | Service metier: ingestion, lecture, gestion agents |
| `backend/app/telemetry/routes.py` | Routes FastAPI: `POST /heartbeat`, `POST /events`, `GET /telemetry/*` |
| `backend/app/telemetry/__init__.py` | Export du router telemetry |
| `backend/app/main.py` | Enregistrement du router `/telemetry` |
| `backend/tests/run_tests.py` | Suite de tests de validation (14 tests) |
| `scripts/sync_github_project.py` | Script de synchronisation GitHub Projects |
| `scripts/launch_agents.py` | Script de lancement d'agents en parallele |
| `documents/07_gestion_de_projet/sprint-reports/sprint-1-report-2026-05-06.md` | Rapport Sprint 1 |

## Definition of Done Sprint 2

- [x] Modeles SQLAlchemy pour agents, heartbeats, events
- [x] Schemas Pydantic pour validation des payloads
- [x] Routes `POST /telemetry/heartbeat` et `POST /telemetry/events`
- [x] Routes de consultation protegees par JWT
- [x] Authentification agent via `require_agent`
- [x] Tests de validation passes (14/14)
- [x] Documentation EPIC-02 mise a jour
- [x] Sprint backlog mis a jour avec Sprint 2

## GitHub Project

Synchronisation bloquee: token GitHub invalide (`Bad credentials`). Action requise:
1. Renouveler le token dans `old/token.txt`
2. Executer `python3 scripts/sync_github_project.py`

## Prochain Sprint Recommande: Sprint 3

Objectif: detection, alertes et actifs
- US-03.1: Scan IP et decouverte d'actifs
- US-03.2: Inventaire actifs avec modele `Asset`
- US-04.1: Regles de detection simples
- US-04.2: Cycle de vie des alertes
- US-04.3: Audit trail
