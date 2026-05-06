# EPIC-07 - Reporting, exports et preuves

**Lien**: [Gestion de projet §8](../rendu_principal.md#8-product-backlog-structuré) | [§9 Features](../rendu_principal.md#9-features-par-epic)

## Objectif
Produire des exports CSV/JSON et des preuves de validation (Priorité P1)

## User Stories

| ID | User Story | SP | Sprint | Owner | Issue # |
|---|---|---|---|---|---|
| US-07.1 | Export CSV (alertes/events) | 3 | Sprint 4-5 | Barbara Liskov | |
| US-07.2 | Export JSON (structuré) | 3 | Sprint 5 | Barbara Liskov | |
| US-07.3 | Preuve scénario (lien export) | 3 | Sprint 5 | Margaret Hamilton | |

## Tasks Techniques (US-07.1 - CSV)

- [x] Generation CSV (Python csv module) - Barbara Liskov
- [x] Endpoint `GET /export/csv` (FastAPI) - Barbara Liskov
- [x] Telechargement fichier - Tim Berners-Lee
- [x] Log audit export - Radia Perlman
- [x] Tests export CSV - Margaret Hamilton

## Tasks Techniques (US-07.2 - JSON)

- [x] Generation JSON structure - Barbara Liskov
- [x] Endpoint `GET /export/json` - Barbara Liskov
- [x] Metadata export - Barbara Liskov
- [x] Tests export JSON - Margaret Hamilton

## Tasks Techniques (US-07.3 - Preuve)

- [x] Nommage export (timestamp/scenario) - Linus Torvalds
- [x] Metadata scenario - Margaret Hamilton
- [x] Documentation preuve - Linus Torvalds
- [x] Capture export + scenario - Margaret Hamilton

## Definition of Ready (US-07.1)

- [ ] Format CSV défini
- [ ] Endpoint `/export` prêt
- [ ] Log audit configuré

## Definition of Done (US-07.1)

- [ ] CSV généré et téléchargeable
- [ ] Log audit de l'export
- [ ] Preuve: fichier CSV exploitable

## Acceptance Criteria

| Critère | Preuve attendue |
|---|---|
| Export CSV | Fichier téléchargé, colonnes correctes |
| Export JSON | JSON structuré, métadonnées |
| Preuve liée | Export rattaché au scénario |

## GitHub Project

- Status actuel recommandé : `Done`
- Labels recommandés : `epic`, `user-story`, `backend`, `reports`, `audit`
- Issues GitHub : à compléter dans la colonne `Issue #`
