# EPIC-05 - Corrélation et enrichissement analyste

**Lien**: [Gestion de projet §8](../rendu_principal.md#8-product-backlog-structuré) | [§9 Features](../rendu_principal.md#9-features-par-epic)

## Objectif
Regrouper des événements liés pour améliorer la lisibilité SOC (Priorité P2)

## User Stories

| ID | User Story | SP | Sprint | Owner | Issue # |
|---|---|---|---|---|---|
| US-05.1 | Corrélation IP source | 8 | Sprint 4 | Ken Thompson | |
| US-05.2 | Corrélation temporelle | 8 | Sprint 4 | Ken Thompson | |
| US-05.3 | Vue corrélation | 5 | Sprint 4 | Tim Berners-Lee | |

## Tasks Techniques (US-05.1 - IP)

- [x] Règle corrélation IP - Ken Thompson
- [x] Modèle `CorrelationGroup` - Barbara Liskov
- [x] Association events → groupe - Ken Thompson
- [x] Endpoint corrélations (API) - Barbara Liskov
- [x] Vue groupes IP (UI) - Tim Berners-Lee
- [x] Tests corrélation IP - Margaret Hamilton

## Tasks Techniques (US-05.2 - Temporelle)

- [x] Paramètre fenêtre temporelle - Ken Thompson
- [x] Requête temporelle PostgreSQL - Barbara Liskov
- [x] Scoring simple corrélation - Ken Thompson
- [x] Tests scénario temporel - Margaret Hamilton

## Tasks Techniques (US-05.3 - Vue)

- [x] Vue consultation corrélations - Tim Berners-Lee
- [x] Lien alerte → corrélation - Tim Berners-Lee
- [x] Explication corrélation (UI) - Tim Berners-Lee

## Definition of Ready (US-05.1)

- [x] Logique de regroupement codée
- [x] Requête PostgreSQL prête
- [x] Vue corrélation prévue

## Definition of Done (US-05.1)

- [x] Groupe créé pour événements liés
- [x] IP source affichée
- [x] Historique consultable
- [x] Preuve: groupe visible dashboard

## Acceptance Criteria

| Critère | Preuve attendue |
|---|---|
| Corrélation IP | Events liés → groupe créé |
| Corrélation temporelle | Répétition visible fenêtre |
| Vue consultable | Analyste voit groupe + détail |

## GitHub Project

- Status actuel recommandé : `Done`
- Labels recommandés : `epic`, `user-story`, `backend`, `correlation`
- Issues GitHub : à compléter dans la colonne `Issue #`
