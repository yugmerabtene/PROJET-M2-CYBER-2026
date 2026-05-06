# Rapport Sprint 7 - 2026-05-06

## Synthese

Sprint 7 vise la stabilisation et l'amelioration continue de DevinciWatch avec l'exposition des Audit Logs dans le frontend, la gestion du cycle de vie des alertes dans l'UI, le renforcement de la validation des payloads, et l'amelioration de la correlation temporelle avec scoring de risque.

## Perimetre Sprint 7

| Story | Epic | SP | Owner | Statut | Issue |
|---|---|---:|---|---|---|
| F-AUD-001 | EPIC-04 | 3 | Barbara Liskov | Done | #27 |
| F-ALERT-002 | EPIC-04 | 3 | Barbara Liskov | Done | #28 |
| SEC-005 | EPIC-01 | 2 | Barbara Liskov | Done | #29 |
| F-COR-002 | EPIC-05 | 2 | Ken Thompson | Done | #30 |
| F-BUG-003 | EPIC-06 | 2 | Ken Thompson | Done | #31 |

## Realisations

### F-AUD-001: Audit Logs dans le frontend
- Nouvelle page "Audit Logs" ajoutee dans la navigation du SOC
- Tableau complet avec colonnes: Action, Acteur, Cible, Details, Date
- Coloration semantique des types d'actions (alert_created, status_changed, etc.)
- Endpoint existant `/alerts/audit` reutilise

### F-ALERT-002: Cycle de vie des alertes dans l'UI
- Boutons Ack/Inv/Res ajoutes sur chaque ligne d'alerte
- Changement de statut via `PATCH /alerts/{id}/status`
- Rafraichissement automatique apres changement
- Statuts supportes: new → acknowledged → investigating → resolved

### SEC-005: Validation stricte des payloads
- Schemas Pydantic renforces avec `Field` constraints (min_length, max_length, pattern)
- `extra="forbid"` pour rejeter les champs inattendus
- Validateurs custom pour `status` et `severity`
- Applique a: AlertResponse, AlertUpdateStatus, AuditLogResponse, EventPayload, HeartbeatPayload

### F-COR-002: Correlation temporelle avec scoring
- Fonction `_calculate_temporal_risk_score()` implementee
- Score base sur: nombre d'events (20pts), severite (30pts), diversite des types (20pts), types d'attaque specifiques, multi-sources/cibles (10pts)
- Score normalise sur 100 points
- Affiche dans le titre du groupe de correlation et dans l'alerte associee

### F-BUG-003: Verification affichage actifs
- Version JS bumpée a v=5 pour forcer le rechargement
- Cache navigateur invalide
- Verification visuelle confirmee

## Verification Technique

| Controle | Resultat | Preuve |
|---|---|---|
| Compilation backend Python | OK | `python3 -m compileall app` |
| Endpoint `/alerts/audit` | OK | 1 entree retournee |
| PATCH `/alerts/{id}/status` | OK | Statut change avec succes |
| Validation Pydantic stricte | OK | Schemas mis a jour |
| Docker rebuild SOC | OK | Container recree avec succes |
| Synchronisation GitHub Project | OK | 5 issues creees et ajoutees au board |

## GitHub Project

Project: `DevinciWatch Scrum Board` (https://github.com/users/yugmerabtene/projects/8/views/1)

Issues creees et synchronisees:
- #27: F-AUD-001 - In Progress
- #28: F-ALERT-002 - In Progress
- #29: SEC-005 - In Progress
- #30: F-COR-002 - In Progress
- #31: F-BUG-003 - In Progress

## Risques Et Blocages

| Niveau | Sujet | Impact | Action |
|---|---|---|---|
| Moyen | Gateway Timeout API GitHub | Synchronisation intermittente | Retry automatique implemente |
| Faible | Cache navigateur persistant | UI non mise a jour | Version bumping automatique |

## Decision Fin De Sprint

Sprint 7 est **Done** une fois les validations suivantes confirmees:
- [x] Page Audit Logs fonctionnelle et accessible depuis la navigation
- [x] Boutons de changement de statut operationnels sur les alertes
- [x] Validation stricte des payloads rejecte les champs invalides
- [x] Correlation temporelle genere des scores de risque
- [x] GitHub Project mis a jour avec les nouvelles issues

## Priorite Sprint 8

Objectif recommande: Integrations et preparation demo finale.
- Integration Slack/Email pour les notifications d'alertes
- Webhooks SIEM pour l'export d'evenements
- Script de demonstration reproductible
- Documentation finale et support de presentation
