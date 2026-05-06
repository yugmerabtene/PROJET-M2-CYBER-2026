# EPIC-08 - Lab Docker, démonstration et documentation

**Lien**: [Gestion de projet §8](../rendu_principal.md#8-product-backlog-structuré) | [§9 Features](../rendu_principal.md#9-features-par-epic)

## Objectif

Stabiliser le lab, les scénarios et la documentation de lancement (Priorité P1)

## User Stories

| ID | User Story | SP | Sprint | Owner | Issue # |
|---|---|---:|---|---|---|
| US-08.1 | Docker Compose lab complet | 5 | Sprint 1 | Linus Torvalds | |
| US-08.2 | Scénarios contrôlés reproductibles | 5 | Sprint 5 | Radia Perlman | |
| US-08.3 | Documentation lancement et validation | 3 | Sprint 5 | Linus Torvalds | |

## Tasks Techniques (US-08.1 - Docker Compose)

- [x] Créer `product/docker-compose.yml` - Linus Torvalds
- [x] Définir `serveur-soc` - Linus Torvalds
- [x] Définir `serveur-endpoint` - Linus Torvalds
- [x] Définir `serveur-attacker` - Linus Torvalds
- [x] Ajouter PostgreSQL - Linus Torvalds
- [x] Ajouter Redis - Linus Torvalds
- [x] Configurer réseau Docker dédié - Linus Torvalds
- [x] Documenter variables dans `.env.example` - Linus Torvalds
- [x] Tester démarrage complet du lab - Margaret Hamilton
- [x] Documenter procédure de vérification - Linus Torvalds

## Tasks Techniques (US-08.2 - Scenarios controles)

- [x] Create simulateur `serveur-attacker` - Radia Perlman
- [x] Preparer scenario port scan controle - Radia Perlman
- [x] Preparer scenario brute force simule - Radia Perlman
- [x] Preparer scenario burst - Radia Perlman
- [x] Relier scenarios aux alertes backend - Ken Thompson
- [x] Produire preuve chaine heartbeat -> event -> alerte -> export - Margaret Hamilton

## Tasks Techniques (US-08.3 - Documentation)

- [x] Documenter lancement du lab - Linus Torvalds
- [x] Documenter variables obligatoires - Linus Torvalds
- [x] Documenter troubleshooting - Linus Torvalds
- [x] Documenter preuves attendues - Margaret Hamilton
- [x] Captures ou logs de validation - Margaret Hamilton

## Definition of Ready (US-08.1)

- [x] Services cibles identifiés
- [x] Variables d'environnement listées
- [x] Réseau Docker prévu
- [x] Commande de validation définie

## Definition of Done (US-08.1)

- [x] `serveur-soc` défini
- [x] `serveur-endpoint` défini
- [x] `serveur-attacker` défini
- [x] PostgreSQL et Redis définis
- [x] Démarrage complet vérifié
- [x] Preuve: logs ou capture `docker compose ps`

## Acceptance Criteria

| Critère | Preuve attendue |
|---|---|
| Lab défini | `product/docker-compose.yml` présent |
| Services présents | `serveur-soc`, `serveur-endpoint`, `serveur-attacker` |
| Configuration documentée | `.env.example` présent |
| Démarrage vérifié | Sortie `docker compose ps` ou logs |

## GitHub Project

- Status actuel recommandé : `Done`
- Labels recommandés : `epic`, `user-story`, `devops`, `docker`, `security`, `qa`
- Issues GitHub : à compléter dans la colonne `Issue #`
