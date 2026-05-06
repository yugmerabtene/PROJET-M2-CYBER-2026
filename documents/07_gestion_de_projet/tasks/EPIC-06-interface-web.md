# EPIC-06 - Interface web et visualisation

**Lien**: [Gestion de projet §8](../rendu_principal.md#8-product-backlog-structuré) | [§9 Features](../rendu_principal.md#9-features-par-epic)

## Objectif
Fournir un dashboard et des vues analyste exploitables (Priorité P1)

## User Stories

| ID | User Story | SP | Sprint | Owner | Issue # |
|---|---|---|---|---|---|
| US-06.1 | Dashboard synthétique | 5 | Sprint 4 | Tim Berners-Lee | |
| US-06.2 | Vues analyste (actifs/events/alertes) | 5 | Sprint 4 | Tim Berners-Lee | |
| US-06.3 | Visualisation enrichie (IP attaquantes) | 3 | Sprint 4 | Tim Berners-Lee | |

## Tasks Techniques (US-06.1 - Dashboard)

- [x] Définir métriques (events, alertes, endpoints) - Tim Berners-Lee
- [x] Endpoint `GET /summary` (FastAPI) - Barbara Liskov
- [x] Composants UI dashboard - Tim Berners-Lee
- [x] Navigation dashboard - Tim Berners-Lee
- [x] Tests UI dashboard - Margaret Hamilton

## Tasks Techniques (US-06.2 - Vues analyste)

- [x] Navigation entre vues API - Tim Berners-Lee
- [x] Vues liste + detail API (actifs, events, alertes) - Tim Berners-Lee
- [x] Etats vides (empty states) - Tim Berners-Lee
- [x] Parcours analyste complet - Tim Berners-Lee

## Tasks Techniques (US-06.3 - IP attaquantes)

- [x] Agrégation IP sources - Ken Thompson
- [x] Endpoint `/attackers` (API) - Barbara Liskov
- [x] Vue IP attaquantes (UI) - Tim Berners-Lee
- [x] Fréquence affichée - Tim Berners-Lee

## Definition of Ready (US-06.1)

- [x] Composants UI de base
- [x] Endpoint `/summary` prêt
- [x] Navigation dashboard prévue

## Definition of Done (US-06.1)

- [x] Métriques affichées (events, alertes, exports)
- [x] Navigation fluide
- [x] Exports visibles
- [x] Preuve: captures dashboard

## Acceptance Criteria

| Critère | Preuve attendue |
|---|---|
| Dashboard fonctionnel | Métriques clés affichées |
| Parcours analyste | Navigation actifs→events→alertes |
| IP attaquantes | Sources fréquentes visibles |

## GitHub Project

- Status actuel recommandé : `Done`
- Labels recommandés : `epic`, `user-story`, `frontend`, `dashboard`
- Issues GitHub : à compléter dans la colonne `Issue #`
