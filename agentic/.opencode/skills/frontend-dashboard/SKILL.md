---
name: frontend-dashboard
description: Construire le frontend DevinciWatch : dashboard SOC, vues analyste, navigation, etats vides, contrats API, exports et preuves visuelles.
compatibility: opencode
metadata:
  area: frontend
  role: tim-berners-lee
---

# Skill Frontend Dashboard

## What I Do

Guider la conception et l'implementation des vues frontend DevinciWatch pour qu'elles soient lisibles, testables et utiles en demonstration SOC.

## When To Use

- Dashboard EPIC-06.
- Vues actifs, events, alertes, audit et correlations.
- Navigation analyste.
- Parcours export CSV/JSON.
- Etats vides, erreurs, chargement et preuves visuelles.

## Inputs Expected

- User story ou task.
- Contrat API disponible ou attendu.
- Donnees a afficher.
- Criteres d'acceptation.
- Preuve visuelle attendue.

## Source Of Truth

- `documents/06_cahier_des_charges/rendu_principal.md`
- `documents/07_gestion_de_projet/rendu_principal.md`
- `documents/07_gestion_de_projet/tasks/`
- `documents/08_architecture/rendu_principal.md`
- `website/`
- `product/`

## UX Principles

- Prioriser la lisibilite analyste.
- Afficher clairement le statut, la severite et le contexte.
- Eviter les effets visuels inutiles.
- Gerer les donnees absentes.
- Rendre la preuve exploitable en revue projet.
- Conserver le langage visuel existant du depot.

## Workflow

1. Identifier le parcours utilisateur : admin, analyste ou responsable validation.
2. Verifier le contrat API avec backend si necessaire.
3. Definir les donnees affichees et leurs etats.
4. Implementer petit increment UI.
5. Prevoir test manuel, capture ou preuve.
6. Documenter vue, endpoint consomme et limites.

## Checklist

- Route ou page identifiee.
- Donnees API documentees.
- Etat chargement gere.
- Etat erreur gere.
- Etat vide gere.
- Labels et textes comprehensibles.
- Responsive desktop/mobile verifie si UI web reelle.
- Export ou action sensible auditable si applicable.

## Documentation Checklist

- Vue ajoutee ou modifiee.
- Endpoint consomme.
- Champs affiches.
- Scenario de preuve.
- Limites restantes.

## Output Format

Story, vue, contrat API, etats geres, tests/preuve, documentation, limites.
