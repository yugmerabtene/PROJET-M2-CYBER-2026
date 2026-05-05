---
name: documentation-workflow
description: Appliquer une documentation continue docs-as-code pour README, EPICs, preuves, commandes, variables et Definition of Done DevinciWatch.
compatibility: opencode
metadata:
  area: documentation
  workflow: docs-as-code
---

# Skill Documentation Workflow

## What I Do

Garantir que chaque increment code ou pilote reste documente, relancable et defendable en revue projet.

## When To Use

- Une story passe `In Review` ou `Done`.
- Un endpoint, schema, variable, Dockerfile ou service change.
- Une preuve de validation est produite.
- Une sprint review est preparee.

## Documentation Matrix

- Endpoint API : README backend ou section EPIC avec methode, chemin, auth, payload, reponse.
- Variable env : `.env.example` et procedure de lancement.
- Docker : `product/README.md`, EPIC-08 ou troubleshooting.
- Test : commande, resultat attendu, preuve.
- Securite : risque, controle, decision audit.
- GitHub Project : Issue #, statut, owner, sprint, SP.

## Workflow

1. Identifier story et fichiers touches.
2. Verifier documentation proche du code.
3. Verifier liens relatifs et chemins.
4. Verifier preuve DoD.
5. Signaler docs manquantes ou obsoletes.
6. Proposer mise a jour minimale.

## Definition Of Done Documentation

- Documentation utile et minimale.
- Commandes exactes.
- Variables documentees.
- Preuve rattachee a la story.
- Liens non casses.
- Pas de mention interdite liee a une IA.

## Output Format

Fichiers verifies, docs a jour, docs manquantes, preuves, decision : OK, OK avec reserves ou bloquant.
