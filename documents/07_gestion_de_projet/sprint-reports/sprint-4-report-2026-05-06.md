# Rapport Sprint 4 - 2026-05-06

## Synthese

Sprint 4 implemente la correlation d'evenements et le dashboard SOC. **54/54 tests passants**. 6 user stories terminees.

## Perimetre Sprint 4

| Story | Epic | SP | Owner | Statut | QA |
|---|---|---:|---|---|---|
| US-05.1 | EPIC-05 | 8 | Ken Thompson | Done | ✅ Correlation IP |
| US-05.2 | EPIC-05 | 8 | Ken Thompson | Done | ✅ Correlation temporelle |
| US-05.3 | EPIC-05 | 5 | Tim Berners-Lee | Done | ✅ Vue API |
| US-06.1 | EPIC-06 | 5 | Tim Berners-Lee | Done | ✅ Dashboard API |
| US-06.2 | EPIC-06 | 5 | Tim Berners-Lee | Done | ✅ Vues API |
| US-06.3 | EPIC-06 | 3 | Tim Berners-Lee | Done | ✅ API enrichie |

## Endpoints Ajoutes

| Methode | Path | Description |
|---|---|---|
| GET | `/correlation` | Groupes de correlation |
| POST | `/correlation/run-ip` | Correlation par IP |
| POST | `/correlation/run-temporal` | Correlation temporelle |
| GET | `/correlation/{id}` | Detail groupe |
| GET | `/correlation/{id}/events` | Evenements du groupe |
| PATCH | `/correlation/{id}/resolve` | Resoudre groupe |
| GET | `/correlation/summary` | Synthese correlation |
| GET | `/reports/dashboard` | Dashboard SOC complet |
| GET | `/reports/dashboard/alerts` | Repartition alertes |
| GET | `/reports/dashboard/events` | Repartition evenements |
| GET | `/reports/dashboard/assets` | Repartition actifs |
| GET | `/reports/export/alerts/csv` | Export alertes CSV |
| GET | `/reports/export/events/csv` | Export evenements CSV |
| GET | `/reports/export/assets/csv` | Export actifs CSV |
| GET | `/reports/export/{res}/json` | Export JSON |

## Cumul Projet

| Sprint | SP | Status | Tests | Endpoints |
|---|---:|---|---|---|
| Sprint 1 | 10 | Done | 14 | 3 |
| Sprint 2 | 13 | Done | 14 | 9 |
| Sprint 3 | 19 | Done | 23 | 12 |
| Sprint 4 | 29 | Done | 17 | 15 |
| **Total** | **71/90** | **79%** | **54** | **39** |

## Restant Sprint 5 (19 SP)

- EPIC-07: Reporting final (9 SP) - exports avancés, preuves
- EPIC-08: Lab Docker complet (10 SP) - scénarios, documentation
