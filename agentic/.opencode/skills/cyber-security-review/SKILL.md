---
name: cyber-security-review
description: Auditer DevinciWatch : secrets, RBAC, auth agent, payloads, logs, audit trail, Docker lab et scenarios offensifs controles.
compatibility: opencode
metadata:
  area: security
  mode: review-only
---

# Skill Cyber Security Review

## What I Do

Identifier les risques qui bloquent ou fragilisent la demonstration cyber et proposer des corrections actionnables.

## When To Use

- Auth utilisateur ou JWT.
- RBAC admin/analyst.
- Auth agent et routes telemetry.
- Exports, audit logs, alertes.
- Docker lab, scan, attacker.
- Avant passage `Done` d'une story sensible.

## Controls

- Secrets et `.env`.
- Valeurs par defaut sensibles.
- Separation route utilisateur / route agent.
- Validation Pydantic.
- 401/403 coherents.
- Logs non sensibles.
- Audit obligatoire.
- Scan borne au lab Docker.
- Dependances risquees.
- Tests securite presents.

## Decision Model

- `OK` : aucun risque bloquant.
- `OK avec reserves` : risque acceptable avec action suivie.
- `Bloquant` : risque incompatible avec MVP ou demonstration.

## Output Format

Risques critiques, moyens, faibles, fichiers, corrections, tests/docs manquants, decision.
