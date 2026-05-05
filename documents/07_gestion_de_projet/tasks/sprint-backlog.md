# Sprint Backlog - DevinciWatch

**Lien**: [Gestion de projet §11](../rendu_principal.md#11-découpage-prévisionnel-par-sprint)

## Sprint Actuel Recommandé

Sprint 1 - Poser le socle applicatif sécurisé.

## Sprint 1

| Story | Epic | SP | Owner | Status recommandé | Commentaire |
|---|---|---:|---|---|---|
| US-01.1 | EPIC-01 | 5 | Barbara Liskov | In Review | Auth codée, tests et preuve manquants |
| US-01.2 | EPIC-01 | 3 | Barbara Liskov | In Review | RBAC helper présent, test refus admin manquant |
| US-01.3 | EPIC-01 | 2 | Ken Thompson | In Review | `/health` présent, test et documentation manquants |
| US-08.1 | EPIC-08 | 5 | Linus Torvalds | In Review | Docker Compose présent, démarrage à vérifier |

## Backlog Prochain

| Story | Epic | SP | Sprint cible | Status recommandé | Blocage principal |
|---|---|---:|---|---|---|
| US-02.1 | EPIC-02 | 3 | Sprint 2 | Backlog | Backend telemetry absent |
| US-02.2 | EPIC-02 | 5 | Sprint 2 | Backlog | Modèles events absents |
| US-02.3 | EPIC-02 | 5 | Sprint 2 | Backlog | Auth agent helper non branché |
| US-03.1 | EPIC-03 | 5 | Sprint 2-3 | Backlog | Discovery/assets absents |

## Definition Of Done Sprint 1

- [ ] Tests auth présents et passants
- [ ] Tests `/health` présents et passants
- [ ] Preuve RBAC refus analyst/admin produite
- [ ] Docker Compose démarré et vérifié
- [ ] Documentation lancement minimale à jour
- [ ] Issues GitHub créées et reliées au Project board
- [ ] README ou note technique mis à jour pour chaque changement produit
- [ ] `.env.example` à jour pour chaque variable utilisée
- [ ] Preuve de validation rattachée à chaque story terminée
- [ ] Revue sécurité documentée pour auth, RBAC, agent et Docker lab

## Règle Documentation Continue

Une story ne passe pas en `Done` sans documentation minimale, preuve associée ou justification explicite indiquant que la documentation n'est pas nécessaire.

## GitHub Project Sync

- Project cible : `DevinciWatch Scrum Board`
- Colonnes : `Backlog`, `Sprint Ready`, `In Progress`, `In Review`, `Done`
- À faire : compléter les numéros d'issues dans chaque fichier EPIC
