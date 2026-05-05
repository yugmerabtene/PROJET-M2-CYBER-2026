---
description: Prepare le changement de statut GitHub Project d'une story ou task.
agent: github-project-manager
---

Prepare le changement de statut suivant :

$ARGUMENTS

Verifie la Definition of Ready/Done, les tests, la preuve, la documentation et la securite avant de proposer `Sprint Ready`, `In Progress`, `In Review` ou `Done`.

## Exemple d'utilisation

```text
/move-story US-01.3 vers In Review
```

```text
/move-story US-08.1 vers Done seulement si preuve docker compose ps et documentation lancement existent
```
