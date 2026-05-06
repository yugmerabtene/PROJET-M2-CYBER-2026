# Rapport Sprint 1 - 2026-05-06

## Synthese

Sprint 1 vise a poser le socle applicatif securise de DevinciWatch et a rendre le lab Docker verifiable. L'increment existe partiellement : backend FastAPI, authentification JWT, endpoint `/health`, agent endpoint, simulateur attacker et `docker-compose.yml` sont presents. Le sprint ne peut pas etre declare `Done` car les tests, preuves, verification Docker et synchronisation GitHub Project restent incomplets ou bloques par l'environnement local.

## Perimetre Sprint 1

| Story | Epic | SP | Owner | Statut recommande | Decision |
|---|---|---:|---|---|---|
| US-01.1 | EPIC-01 | 5 | Barbara Liskov | In Review | Auth codee, preuves et tests manquants |
| US-01.2 | EPIC-01 | 3 | Barbara Liskov | In Review | Helpers RBAC presents, tests de refus manquants |
| US-01.3 | EPIC-01 | 2 | Ken Thompson | In Review | `/health` present, test et documentation a finaliser |
| US-08.1 | EPIC-08 | 5 | Linus Torvalds | In Review | Compose present, verification Docker bloquee localement |

## Verification Technique

| Controle | Resultat | Preuve |
|---|---|---|
| Compilation backend Python | OK | `python3 -m compileall app` |
| Compilation agent endpoint | OK | `python3 -m py_compile agent.py` |
| Compilation attacker | OK | `python3 -m py_compile scenario.py` |
| Validation Docker Compose | Bloquee | `docker: commande introuvable` |
| Synchronisation GitHub Project via CLI | Bloquee | `gh: commande introuvable` |
| Etat Git local | OK | Branche `main...origin/main`, pas de modification avant rapport |

## Etat Produit Constate

- Backend FastAPI operationnel en squelette avec `GET /health`, `POST /auth/login`, `GET /auth/me`.
- Modele `User`, hash bcrypt, JWT et dependances RBAC presents.
- Agent endpoint envoie des heartbeats et events vers `/telemetry/heartbeat` et `/telemetry/events`.
- Les endpoints telemetry n'existent pas encore cote backend, donc la boucle agent vers SOC est rompue.
- Redis et Celery sont declares dans les dependances et dans Docker, mais aucun worker n'est implemente.
- Les modules `telemetry`, `assets`, `alerts`, `audit`, `correlation`, `discovery`, `reports` sont encore vides.

## Risques Et Blocages

| Niveau | Sujet | Impact | Action recommandee |
|---|---|---|---|
| Critique | Telemetry backend absent | L'agent ne peut pas alimenter le SOC | Prioriser EPIC-02 des le Sprint 2 |
| Eleve | Tests Sprint 1 absents | Stories non acceptables selon Definition of Done | Ajouter tests auth, RBAC et health |
| Eleve | Docker indisponible localement | Lab non verifie | Installer Docker ou verifier sur une machine equipee |
| Eleve | GitHub CLI indisponible | Project non synchronisable en temps reel | Installer `gh` ou fournir une methode API valide |
| Moyen | Secrets par defaut en dev | Risque si reutilises hors lab | Forcer variables en environnement non-dev |

## GitHub Project

Project cible : `DevinciWatch Scrum Board`.

Etat actuel : synchronisation automatique impossible dans cet environnement car `gh` n'est pas installe. Les fichiers locaux restent la source de suivi temporaire :

- `documents/07_gestion_de_projet/tasks/sprint-backlog.md`
- `documents/07_gestion_de_projet/tasks/EPIC-01-socle-applicatif.md`
- `documents/07_gestion_de_projet/tasks/EPIC-08-lab-docker-demonstration.md`

Actions requises pour synchronisation temps reel :

1. Installer GitHub CLI `gh` dans l'environnement.
2. Authentifier `gh` avec les droits repository et project.
3. Completer les numeros d'issues dans les fichiers EPIC.
4. Mettre a jour les statuts Project a chaque changement de story.

## Decision Fin De Sprint

Sprint 1 reste en `In Review`.

Les stories ne doivent pas passer en `Done` tant que les preuves suivantes ne sont pas produites :

- tests auth passants ;
- tests `/health` passants ;
- preuve d'acces refuse sans token et de refus RBAC ;
- verification Docker Compose ou justification d'indisponibilite ;
- revue securite minimale auth/RBAC/config ;
- issues GitHub reliees au Project board.

## Priorite Sprint 2

Objectif recommande : fermer la boucle agent vers SOC.

- Implementer `POST /telemetry/heartbeat` avec authentification agent.
- Implementer `POST /telemetry/events` avec validation Pydantic.
- Ajouter modeles PostgreSQL minimaux pour agents, heartbeats et events.
- Ajouter routes de consultation protegees par JWT.
- Ajouter tests API et preuve d'ingestion.
