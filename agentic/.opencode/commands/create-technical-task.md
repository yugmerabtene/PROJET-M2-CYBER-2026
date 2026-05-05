---
description: Prepare une issue GitHub Technical Task liee a une user story.
agent: github-project-manager
---

Prepare la tache technique suivante :

$ARGUMENTS

Produis le titre, body GitHub, parent user story, owner, composant, estimation, status, documentation attendue et lien avec la Definition of Done. Ne mentionne jamais d'IA comme auteur, source ou origine.

## Exemple d'utilisation

```text
/create-technical-task T-02.1.1 Parent US-02.1 Créer HeartbeatSchema Pydantic, Owner Ken Thompson, Backend - FastAPI route
```

```text
/create-technical-task T-01.3.1 Parent US-01.3 Ajouter test pytest GET /health, Owner Margaret Hamilton, QA - Test case
```
