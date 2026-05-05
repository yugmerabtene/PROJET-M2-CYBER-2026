---
name: devinciwatch-project
description: Comprendre DevinciWatch, son MVP SOC, ses epics, ses exigences, ses roles projet et ses contraintes de demonstration Docker.
compatibility: opencode
metadata:
  audience: devinciwatch-team
  workflow: scrum-mvp
---

# Skill DevinciWatch Project

## What I Do

Donner le contexte projet minimal et fiable pour toute decision de developpement, test, documentation, securite ou GitHub Project.

## When To Use

Utiliser cette skill avant de planifier une story, modifier le produit, auditer une exigence ou preparer une sprint review.

## Source Of Truth

- `documents/06_cahier_des_charges/rendu_principal.md`
- `documents/07_gestion_de_projet/rendu_principal.md`
- `documents/07_gestion_de_projet/tasks/`
- `documents/08_architecture/rendu_principal.md`
- `product/`
- `documents/07_gestion_de_projet/.github-project-management/PROJECT_SETUP.md`

## MVP Scope

Le MVP demontre une chaine SOC minimale : auth, roles, heartbeat, events, assets, alertes, audit, correlation, dashboard, exports et lab Docker reproductible.

Hors perimetre initial : SOAR avance, multi-tenant complet, SIEM enterprise, reseaux externes au lab, charges offensives destructrices.

## Roles Projet

- Ada Lovelace : priorisation et acceptation produit.
- Grace Hopper : Scrum, blockers, DoR/DoD.
- Alan Turing : jalons, risques, livrables, coherence.
- Barbara Liskov : backend API, modeles, PostgreSQL.
- Ken Thompson : ingestion, detection, workers, correlation.
- Tim Berners-Lee : frontend dashboard et parcours analyste.
- Margaret Hamilton : tests, recette, preuves.
- Linus Torvalds : Docker, integration, reproductibilite.
- Radia Perlman : securite, scenarios controles, RBAC, audit.

## Workflow

1. Identifier epic, feature, story, sprint et owner.
2. Verifier le cahier des charges et l'architecture.
3. Verifier le fichier EPIC local.
4. Decouper en petite tache testable.
5. Prevoir tests, securite, documentation et preuve.
6. Synchroniser GitHub Project si necessaire.

## Definition Of Done Projet

- Comportement implemente.
- Criteres d'acceptation verifies.
- Tests ou preuve disponibles.
- Documentation minimale a jour.
- Securite auditee si sensible.
- GitHub Project et fichier EPIC alignes.

## Constraints

- Ne pas developper toute l'application d'un coup.
- Ne pas sortir du lab Docker sans validation.
- Ne jamais exposer de secret.
- Ne jamais mentionner d'IA comme auteur, source ou origine dans les livrables Git/GitHub.

## Output Format

Toujours restituer : story concernee, valeur produit, fichiers, tests, documentation, risques et prochaine action.
