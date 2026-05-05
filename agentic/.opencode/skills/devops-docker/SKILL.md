---
name: devops-docker
description: Maintenir Docker Compose, .env.example, scripts, logs, healthchecks et reproductibilite du lab DevinciWatch.
compatibility: opencode
metadata:
  area: devops
  lab: docker-compose
---

# Skill DevOps Docker

## What I Do

Rendre le lab DevinciWatch relancable localement et exploitable en demonstration.

## When To Use

- Changement `product/docker-compose.yml`.
- Ajout variable d'environnement.
- Verification EPIC-08.
- Preparation demo ou sprint review.
- Troubleshooting de lancement.

## Lab Target

- `serveur-soc`
- `serveur-endpoint`
- `serveur-attacker`
- PostgreSQL
- Redis

## Workflow

1. Identifier service et story.
2. Verifier Dockerfile et contexte de build.
3. Verifier variables `.env.example`.
4. Verifier reseau Docker dedie.
5. Prevoir commandes de lancement, logs et verification.
6. Documenter risques et troubleshooting.

## Checklist

- Aucun secret reel.
- `.env.example` complet.
- Ports documentes.
- Healthcheck ou endpoint de verification.
- Commande `docker compose up --build` documentee.
- Commande `docker compose ps` ou logs pour preuve.
- Pas de suppression volume sans validation.

## Output Format

Fichiers, variables, commandes, verification, preuve, risques.
