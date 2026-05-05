---
description: Produit l'etat d'un sprint depuis les fichiers tasks et GitHub Project si disponible.
agent: github-project-manager
---

Analyse le sprint suivant :

$ARGUMENTS

Produis SP planifies, SP termines, blockers, stories par statut, owners, preuves, documentation manquante et ecarts avec `documents/07_gestion_de_projet/rendu_principal.md`.

## Exemple d'utilisation

```text
/sprint-status Sprint 1
```

```text
/sprint-status Sprint 2 avec focus sur EPIC-02 et blockers telemetry
```
