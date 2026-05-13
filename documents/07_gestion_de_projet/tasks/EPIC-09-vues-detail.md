# EPIC-09 - Vues detail et investigation analyste

**Lien**: [Gestion de projet §8](../rendu_principal.md#8-product-backlog-structuré) | [§9 Features](../rendu_principal.md#9-features-par-epic)

## Objectif
Permettre a l'analyste de cliquer sur les elements (correlations, evenements, alertes) pour acceder a des vues detail completes avec contexte, timeline et actions (Priorité P2)

## User Stories

| ID | User Story | SP | Sprint | Owner | Issue # |
|---|---|---:|---|---|---|
| US-09.1 | Detail d'un groupe de correlation | 5 | Sprint 9 | Tim Berners-Lee | |
| US-09.2 | Detail d'un evenement | 3 | Sprint 9 | Tim Berners-Lee | |
| US-09.3 | Detail d'une alerte | 5 | Sprint 9 | Tim Berners-Lee | |
| US-09.4 | Actions depuis les vues detail | 3 | Sprint 9 | Tim Berners-Lee | |

## Tasks Techniques (US-09.1 - Detail correlation)

- [ ] Endpoint `GET /correlation/{id}` avec events du groupe - Ken Thompson
- [ ] Endpoint `GET /correlation/{id}/events` - Ken Thompson
- [ ] Modal/panel detail correlation (UI) - Tim Berners-Lee
- [ ] Affichage events correles dans le detail - Tim Berners-Lee
- [ ] Score de corrélation affiche dans le detail - Tim Berners-Lee
- [ ] Tests detail correlation - Margaret Hamilton

## Tasks Techniques (US-09.2 - Detail event)

- [ ] Endpoint `GET /telemetry/events/{id}` - Barbara Liskov
- [ ] Modal/panel detail evenement (UI) - Tim Berners-Lee
- [ ] Affichage raw_payload JSON - Tim Berners-Lee
- [ ] Lien vers alerte liee si existante - Tim Berners-Lee
- [ ] Tests detail event - Margaret Hamilton

## Tasks Techniques (US-09.3 - Detail alerte)

- [ ] Endpoint `GET /alerts/{id}` enrichi (events lies, correlation) - Barbara Liskov
- [ ] Modal/panel detail alerte (UI) - Tim Berners-Lee
- [ ] Timeline de l'alerte (events sources) - Tim Berners-Lee
- [ ] Lien vers groupe de correlation - Tim Berners-Lee
- [ ] Score de corrélation dans le detail - Tim Berners-Lee
- [ ] Tests detail alerte - Margaret Hamilton

## Tasks Techniques (US-09.4 - Actions detail)

- [ ] Changement de statut depuis le detail alerte - Tim Berners-Lee
- [ ] Resolution de correlation depuis le detail - Tim Berners-Lee
- [ ] Export d'un evenement/alerte individuel - Tim Berners-Lee
- [ ] Navigation entre elements lies (event → alerte → correlation) - Tim Berners-Lee
- [ ] Tests actions - Margaret Hamilton

## Definition of Ready (US-09.1)

- [ ] Groupe de correlation existe en base
- [ ] Events correles associes au groupe
- [ ] Contrat API detail defini

## Definition of Done (US-09.1)

- [ ] Clic sur groupe ouvre vue detail
- [ ] Events correles affiches avec contexte
- [ ] Score de corrélation visible si disponible
- [ ] Preuve: capture detail correlation

## Acceptance Criteria

| Critère | Preuve attendue |
|---|---|
| Detail correlation | Vue complete avec events correles |
| Detail evenement | Raw payload + contexte affiches |
| Detail alerte | Timeline + events sources + correlation |
| Actions | Statut changeable depuis les vues detail |

## GitHub Project

- Status actuel recommandé : `In Progress`
- Labels recommandés : `epic`, `user-story`, `frontend`, `investigation`
- Issues GitHub : à compléter dans la colonne `Issue #`
