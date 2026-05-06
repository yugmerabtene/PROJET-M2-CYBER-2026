# EPIC-03 - Découverte réseau et actifs

**Lien**: [Gestion de projet §8](../rendu_principal.md#8-product-backlog-structuré) | [§9 Features](../rendu_principal.md#9-features-par-epic)

## Objectif
Identifier actifs, ports et services observables dans le lab (Priorité P1)

## User Stories

| ID | User Story | SP | Sprint | Owner | Issue # |
|---|---|---|---|---|---|
| US-03.1 | Scan IP (découverte) | 5 | Sprint 2-3 | Ken Thompson | |
| US-03.2 | Inventaire actifs | 5 | Sprint 3 | Barbara Liskov | |
| US-03.3 | Ports et services | 3 | Sprint 3 | Ken Thompson | |

## Tasks Techniques (US-03.1 - Scan IP)

- [x] Scan contrôlé (limites IP lab) - Ken Thompson
- [x] Modèle `Asset` PostgreSQL - Barbara Liskov
- [x] Route `POST /scan` (FastAPI) - Ken Thompson
- [x] Association IP → Asset - Barbara Liskov
- [x] Vue liste actifs (API + UI) - Tim Berners-Lee
- [x] Tests scan contrôlé - Margaret Hamilton

## Tasks Techniques (US-03.2 - Inventaire)

- [x] Création actif depuis événements - Barbara Liskov
- [x] Route `GET /assets` (API) - Barbara Liskov
- [x] Vue détail actif (UI) - Tim Berners-Lee
- [x] Mise à jour actif (heartbeat/events) - Ken Thompson

## Tasks Techniques (US-03.3 - Ports/Services)

- [x] Scan ports (nmap/ scapy simplifié) - Ken Thompson
- [x] Modèle `PortFinding` - Barbara Liskov
- [x] Association actif → ports - Ken Thompson
- [x] Affichage ports/services - Tim Berners-Lee

## Definition of Ready (US-03.1)

- [x] Plage IP lab définie
- [x] Scan contrôlé autorisé
- [x] Modèle asset lié
- [x] Affichage liste prévu

## Definition of Done (US-03.1)

- [x] Actif créé après scan
- [x] IP/ports/services visibles
- [x] Scan limité au lab Docker
- [x] Preuve: actif dans dashboard

## Acceptance Criteria

| Critère | Preuve attendue |
|---|---|
| Actifs visibles | IP + dernière observation |
| Ports associés | Actif montre ports ouverts |
| Scan limité | Pas de scan hors lab Docker |

## GitHub Project

- Status actuel recommandé : `Done`
- Labels recommandés : `epic`, `user-story`, `backend`, `assets`, `discovery`
- Issues GitHub : à compléter dans la colonne `Issue #`
