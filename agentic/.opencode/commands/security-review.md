---
description: Audit securite DevinciWatch.
agent: security-tech-lead
---

Audite la partie suivante :

$ARGUMENTS

Controle secrets, auth utilisateur, auth agent, RBAC, payloads, audit logs, routes sensibles, scenarios cyber, Docker lab et permissions OpenCode.

Rends une decision : OK, OK avec reserves ou bloquant. Indique aussi les tests ou documents manquants pour lever les reserves.

## Exemple d'utilisation

```text
/security-review Auditer EPIC-01 auth, RBAC, valeurs par défaut et absence de secrets réels
```

```text
/security-review Auditer l'auth agent prévue pour POST /telemetry/heartbeat et /telemetry/events
```
