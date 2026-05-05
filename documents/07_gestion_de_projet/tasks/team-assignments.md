# Team Assignments - DevinciWatch

**Lien**: [Gestion de projet §4](../rendu_principal.md#4-équipe-projet-et-rôles) | [RACI](../rendu_principal.md#responsabilités-raci-simplifiées)

## Rôles Scrum

| Personne | Rôle | Responsabilités GitHub Project |
|---|---|---|
| Ada Lovelace | Product Owner | Priorisation backlog, acceptation user stories |
| Grace Hopper | Scrum Master | Statuts, blockers, Sprint Ready, cérémonies |
| Alan Turing | Chef de projet | Jalons, risques, cohérence livrables |

## Rôles Techniques

| Personne | Rôle | Labels principaux | Validation |
|---|---|---|---|
| Barbara Liskov | Backend 1 | `backend`, `database`, `auth` | Margaret Hamilton |
| Ken Thompson | Backend 2 | `backend`, `telemetry`, `workers`, `detection` | Margaret Hamilton |
| Tim Berners-Lee | Frontend | `frontend`, `dashboard`, `ui` | Ada Lovelace |
| Margaret Hamilton | QA | `qa`, `test`, `evidence` | Ada Lovelace |
| Linus Torvalds | DevOps | `devops`, `docker`, `ci` | Margaret Hamilton |
| Radia Perlman | Cybersécurité | `security`, `rbac`, `audit` | Ada Lovelace |

## Règles D'assignation

- Une user story doit avoir un owner principal.
- Une task technique doit avoir un owner technique.
- Une story ne passe pas en `Done` sans validation QA ou preuve équivalente.
- Une story sensible ne passe pas en `Done` sans revue sécurité.
- Les issues GitHub doivent rester alignées avec les fichiers EPIC.

## Champs GitHub Project

| Champ | Valeurs |
|---|---|
| Epic | `EPIC-01` à `EPIC-08` |
| Story Points | `1`, `2`, `3`, `5`, `8`, `13` |
| Sprint | `Sprint 1` à `Sprint 5` |
| Owner | Noms de l'équipe ci-dessus |
| Status | `Backlog`, `Sprint Ready`, `In Progress`, `In Review`, `Done` |
