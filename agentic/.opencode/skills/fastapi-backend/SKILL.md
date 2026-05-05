---
name: fastapi-backend
description: Construire et stabiliser le backend FastAPI DevinciWatch avec routes, schemas Pydantic, services, SQLAlchemy, auth, telemetry et tests.
compatibility: opencode
metadata:
  stack: fastapi-sqlalchemy-pydantic
  area: backend
---

# Skill FastAPI Backend

## What I Do

Guider les changements backend FastAPI pour rester simples, testables, securises et alignes avec les user stories.

## When To Use

- Creation ou modification d'endpoint.
- Ajout de schema Pydantic, modele SQLAlchemy, service ou dependance.
- Stabilisation auth, telemetry, assets, alerts, reports, audit ou correlation.
- Correction d'un comportement backend lie a une story.

## Inputs Expected

- User story ou task technique.
- Endpoint ou module cible.
- Criteres d'acceptation.
- Contraintes auth/RBAC/agent.

## Structure Target

```text
product/backend/app/
├── main.py
├── core/
├── auth/
├── telemetry/
├── discovery/
├── assets/
├── alerts/
├── correlation/
├── reports/
└── audit/
```

## Technical Workflow

1. Lire le module existant.
2. Definir schema Pydantic pour entrees/sorties.
3. Garder router mince : validation, dependances, appel service.
4. Mettre logique metier dans service.
5. Ajouter modele/repository seulement si persistance requise.
6. Brancher router dans `app/main.py`.
7. Ajouter tests unitaires/API.
8. Documenter endpoint, payload, auth et erreurs.

## Checklist

- Route protegee si non publique.
- Route agent separee des routes utilisateur.
- Payload invalide teste.
- 401/403 teste si auth requise.
- Aucun secret hardcode hors valeur placeholder documentee.
- `.env.example` mis a jour si nouvelle variable.
- Aucun appel reseau externe en test.

## Current State Notes

Auth et `/health` existent partiellement. Telemetry, assets, alerts, correlation, reports et audit doivent etre ajoutes increment par increment.

## Output Format

Fichiers modifies, story couverte, comportement, tests, documentation, limites.
