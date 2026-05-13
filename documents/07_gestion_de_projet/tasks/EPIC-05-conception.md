# Document de Conception - EPIC-05 : Corrélation

**Date**: 8 Mai 2026  
**Statut**: Implémenté et en cours d'affinage  
**Sprint cible**: Sprint 5+  
**Priorité globale**: P1

---

## 1. Objectif

Fournir un moteur de corrélation lisible, démontrable et orienté SOC permettant de :

- regrouper des événements liés par IP source ;
- détecter des bursts d'activité dans une fenêtre temporelle ;
- corréler des événements par hostname ;
- détecter des chaînes d'attaque simples ;
- regrouper une session source → cible ;
- calculer un score de corrélation explicable sans dépendance à un moteur statistique externe.

---

## 2. Types de corrélation actifs

| Type | Description | Utilité |
|---|---|---|
| `ip_source` | Regroupe les événements ayant la même IP source | Détection d'activité répétée depuis un même attaquant |
| `temporal_burst` | Regroupe les événements proches dans le temps | Détection de rafales d'activité |
| `hostname_match` | Regroupe par hostname cible | Corrélation orientée service/hôte |
| `attack_chain` | Détecte des séquences logiques d'attaque | Reconstruction d'une progression offensive |
| `session_flow` | Regroupe par session source → cible | Vision plus proche d'un moteur SIEM |

---

## 3. Score composite

Le score de corrélation est borné entre `0` et `100` et repose sur 3 facteurs :

1. **Temporalité** : volume, proximité et intensité du burst
2. **Diversité** : nombre de types, sources et cibles distinctes
3. **Sévérité** : poids des événements critiques / élevés

Formule actuelle :

```python
score = (
    temporal_score * 0.45 +
    diversity_score * 0.30 +
    severity_score * 0.25
)
```

Le détail du score est conservé dans `score_breakdown` pour affichage analyste.

---

## 4. Détection de chaîne d'attaque

Les motifs sont volontairement simples et explicables.

Exemples :

- `network_scan -> port_scan -> brute_force -> privilege_escalation`
- `brute_force -> privilege_escalation -> data_exfiltration`

Chaque chaîne :

- respecte un délai maximal entre étapes ;
- génère un `CorrelationGroup` de type `attack_chain` ;
- conserve l'ordre des événements via `sequence_order`.

---

## 5. Corrélation de session

La corrélation `session_flow` regroupe les événements :

- partageant la même `source_ip` ;
- partageant la même `target_ip` ;
- observés dans une fenêtre courte ;
- couvrant plusieurs types d'événements.

Cette logique est inspirée des moteurs SIEM qui reconstruisent une narration d'attaque autour d'une relation source → cible.

---

## 6. Endpoints utiles

| Endpoint | Rôle |
|---|---|
| `GET /correlation` | Lister les groupes |
| `GET /correlation/summary` | Synthèse globale |
| `POST /correlation/run-ip` | Corrélation IP manuelle |
| `POST /correlation/run-temporal` | Corrélation temporelle manuelle |
| `POST /correlation/run-hostname` | Corrélation hostname manuelle |
| `POST /correlation/run-session` | Corrélation session manuelle |
| `POST /correlation/run-attack-chain` | Détection de chaînes manuelle |
| `POST /correlation/run-all-db` | Exécuter toute la corrélation sur la base |
| `GET /correlation/{id}` | Détail d'un groupe |
| `GET /correlation/{id}/events` | Événements d'un groupe |
| `GET /correlation/{id}/timeline` | Timeline séquencée |
| `PATCH /correlation/{id}/resolve` | Résolution analyste |

---

## 7. Évolutions possibles

- réglage fin des seuils de `session_flow` ;
- enrichissement des phases d'attaque ;
- liaison explicite alertes ↔ groupes ;
- filtrage avancé dans l'UI corrélation ;
- scoring plus contextuel selon le service ciblé.
