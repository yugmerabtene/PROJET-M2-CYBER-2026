# Rapport Sprint 5 - 2026-05-06

## Synthese

Sprint 5 finalise le MVP DevinciWatch avec le scenario runner, le lien exports-scenarios et la documentation. **71/71 tests passants**. 5 user stories terminees.

**MVP COMPLET**: 90 SP, 8 EPIC, 24 user stories, 39 endpoints, 71 tests.

## Perimetre Sprint 5

| Story | Epic | SP | Owner | Statut | QA |
|---|---|---:|---|---|---|
| US-07.1 | EPIC-07 | 3 | Barbara Liskov | Done | ✅ Exports CSV |
| US-07.2 | EPIC-07 | 3 | Barbara Liskov | Done | ✅ Exports JSON |
| US-07.3 | EPIC-07 | 3 | Margaret Hamilton | Done | ✅ Lien scenario |
| US-08.2 | EPIC-08 | 5 | Radia Perlman | Done | ✅ Scenario runner |
| US-08.3 | EPIC-08 | 3 | Linus Torvalds | Done | ✅ Documentation |

## Scenario Runner (US-08.2)

Chain complete implementee dans `scenarios/scenario_runner.py`:
1. **Phase 1**: Agent + heartbeat
2. **Phase 2**: Assets cibles (target, lateral, attacker)
3. **Phase 3**: 25 events brute force SSH
4. **Phase 4**: Event breach successful
5. **Phase 5**: 10 events lateral movement
6. **Phase 6**: 2 alertes (brute force + lateral)
7. **Phase 7**: 2 groupes de correlation (IP + temporel)
8. **Phase 8**: Audit logs

## Cumul Projet

| Sprint | SP | Status | Tests | Endpoints |
|---|---:|---|---|---|
| Sprint 1 | 10 | Done | 14 | 3 |
| Sprint 2 | 13 | Done | 14 | 9 |
| Sprint 3 | 19 | Done | 23 | 12 |
| Sprint 4 | 29 | Done | 17 | 15 |
| Sprint 5 | 19 | Done | 17 | 39 |
| **Total** | **90/90** | **100%** | **71** | **39** |

## EPIC Completes

| EPIC | Objectif | Status |
|---|---|---|
| EPIC-01 | Socle applicatif et securite | ✅ Done |
| EPIC-02 | Collecte endpoint et telemetrie | ✅ Done |
| EPIC-03 | Decouverte reseau et actifs | ✅ Done |
| EPIC-04 | Detection, alertes et audit | ✅ Done |
| EPIC-05 | Correlation et enrichissement | ✅ Done |
| EPIC-06 | Interface web et visualisation | ✅ Done |
| EPIC-07 | Reporting, exports et preuves | ✅ Done |
| EPIC-08 | Lab Docker, demonstration et documentation | ✅ Done |

## GitHub Project Sync

- Project: https://github.com/users/yugmerabtene/projects/8/views/1
- 24 issues creees et positionnees
- Toutes les issues (Sprint 1-5) marquees **Done**
- Status mis a jour via API GraphQL
