# Rapport Sprint 3 - 2026-05-06

## Synthese

Sprint 3 vise a implementer la decouverte reseau, les actifs, la detection d'alertes et l'audit trail. **23/23 tests passes**. 6 user stories terminees. GitHub Project synchronise en temps reel.

## Perimetre Sprint 3

| Story | Epic | SP | Owner | Statut | Validation QA |
|---|---|---:|---|---|---|
| US-03.1 | EPIC-03 | 5 | Ken Thompson | Done | 23/23 tests passes |
| US-03.2 | EPIC-03 | 5 | Barbara Liskov | Done | Modeles + routes + services |
| US-03.3 | EPIC-03 | 3 | Ken Thompson | Done | PortFinding + scan |
| US-04.1 | EPIC-04 | 5 | Ken Thompson | Done | Detection rules + Alert model |
| US-04.2 | EPIC-04 | 3 | Tim Berners-Lee | Done | Lifecycle alertes API |
| US-04.3 | EPIC-04 | 3 | Radia Perlman | Done | Audit trail API |

## Verification Technique

| Controle | Resultat | Preuve |
|---|---|---|
| Compilation backend | OK | `python3 -m compileall app` |
| Tests Sprint 1-2 | 14/14 passes | `tests/run_tests.py` |
| Tests Sprint 3 | 23/23 passes | `tests/test_sprint3.py` |
| **Total cumule** | **37/37 passes** | |
| GitHub Project Sync | 24/24 items OK | API GraphQL |

## Fichiers Crees Sprint 3

| Fichier | Description |
|---|---|
| `app/assets/models.py` | Modeles `Asset`, `PortFinding` |
| `app/assets/schemas.py` | Schemas Pydantic pour assets |
| `app/assets/service.py` | Service: CRUD assets, scan reseau, ports |
| `app/assets/routes.py` | Routes: GET/POST /assets, POST /scan, DELETE |
| `app/discovery/service.py` | Decouverte: ping, scan ports, guess service |
| `app/alerts/models.py` | Modeles `Alert`, `AuditLog` |
| `app/alerts/schemas.py` | Schemas Pydantic pour alertes |
| `app/alerts/service.py` | Service: CRUD alertes, detection, audit |
| `app/alerts/routes.py` | Routes: GET/PATCH /alerts, POST /detect, GET /audit |
| `tests/test_sprint3.py` | 23 tests de validation Sprint 3 |
| `documents/07_gestion_de_projet/sprint-reports/sprint-3-report-2026-05-06.md` | Ce rapport |

## Endpoints Ajoutes

| Methode | Path | Description | Auth |
|---|---|---|---|
| GET | `/assets` | Liste des actifs | JWT |
| POST | `/assets` | Creer un actif | JWT |
| POST | `/assets/scan` | Scan reseau | JWT |
| GET | `/assets/{id}` | Detail actif | JWT |
| GET | `/assets/{id}/ports` | Ports d'un actif | JWT |
| DELETE | `/assets/{id}` | Supprimer actif | JWT |
| GET | `/alerts` | Liste alertes | JWT |
| POST | `/alerts` | Creer alerte | JWT |
| GET | `/alerts/{id}` | Detail alerte | JWT |
| PATCH | `/alerts/{id}/status` | Changer statut | JWT |
| POST | `/alerts/detect` | Evaluer regles detection | JWT |
| GET | `/alerts/audit` | Journal d'audit | JWT |

## Definition of Done Sprint 3

- [x] Tous les modeles SQLAlchemy crees et compilés
- [x] Tous les schemas Pydantic valides
- [x] Toutes les routes operationnelles et protegees
- [x] Services metier implementes
- [x] Tests 37/37 passes (cumule Sprint 1-3)
- [x] Documentation EPIC mise a jour
- [x] Sprint backlog mis a jour
- [x] GitHub Project synchronise

## Cumul Projet

| Sprint | SP | Status | Tests |
|---|---:|---|---|
| Sprint 1 | 10 | Done | 14/14 |
| Sprint 2 | 13 | Done | 14/14 |
| Sprint 3 | 19 | Done | 23/23 |
| **Total** | **42/90** | **47%** | **37/37** |

## Prochain Sprint: Sprint 4

Objectif: Correlation et interface web
- US-05.1: Correlation IP source
- US-05.2: Correlation temporelle
- US-05.3: Vue correlation
- US-06.1: Dashboard synthetique
- US-06.2: Vues analyste
- US-06.3: Visualisation enrichie
