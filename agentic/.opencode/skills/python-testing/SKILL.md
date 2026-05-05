---
name: python-testing
description: Creer des tests pytest reproductibles pour FastAPI, auth, RBAC, auth agent, payloads, Docker lab et preuves DevinciWatch.
compatibility: opencode
metadata:
  framework: pytest
  area: qa
---

# Skill Python Testing

## What I Do

Transformer les criteres d'acceptation en tests executables et preuves de validation.

## When To Use

- Toute route API nouvelle ou modifiee.
- Auth/RBAC/auth agent.
- Payloads invalides.
- Regression avant sprint review.
- Validation de preuve pour Definition of Done.

## Inputs Expected

- User story.
- Endpoint ou module.
- Criteres d'acceptation.
- Commande de test cible.

## Workflow

1. Identifier comportement nominal.
2. Identifier erreurs attendues.
3. Tester auth et roles si necessaire.
4. Verifier JSON attendu.
5. Isoler base de donnees ou utiliser fixture controlee.
6. Documenter commande et resultat attendu.

## Test Checklist

- Cas valide.
- Cas payload invalide.
- Cas non authentifie.
- Cas role insuffisant si RBAC.
- Pas d'appel OpenAI.
- Pas de scan externe.
- Pas de dependance a un ordre d'execution fragile.
- Preuve rattachee a la story.

## Preferred Tools

- `pytest`
- FastAPI `TestClient` ou `httpx`
- fixtures pytest pour config et DB de test.

## Output Format

Tests ajoutes, story couverte, commande, resultat attendu, preuve, limites.
