---
description: Audite le backend FastAPI existant par rapport aux user stories.
agent: project-manager-tech
---

Audite le backend existant pour :

$ARGUMENTS

Compare le code dans `product/backend` avec les user stories dans `documents/07_gestion_de_projet/tasks/`. Liste ce qui est implemente, partiel, manquant, les tests absents, la documentation absente et les risques.

## Exemple d'utilisation

```text
/audit-existing-backend Comparer EPIC-01 au backend actuel et lister tests/docs manquants
```

```text
/audit-existing-backend Vérifier si EPIC-02 telemetry est réellement implémentée côté FastAPI
```
