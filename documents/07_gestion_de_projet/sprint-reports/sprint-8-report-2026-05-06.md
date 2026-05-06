# Rapport Sprint 8 - Detection d'anomalies ML - 2026-05-06

## Synthese

Sprint 8 ajoute une couche de detection d'anomalies par Machine Learning (Isolation Forest) pour completer la correlation basee sur les regles. Cette extension P3 identifie des patterns anormaux non couverts par les regles de detection existantes.

## Perimetre Sprint 8 (Extension P3)

| Story | Epic | SP | Owner | Statut | Issue |
|---|---|---:|---|---|---|
| ML-001 | EPIC-05 | 5 | Ken Thompson | Done | #32 |
| ML-002 | EPIC-05 | 3 | Ken Thompson | Done | #33 |
| ML-003 | EPIC-06 | 3 | Tim Berners-Lee | Done | #34 |

## Realisations

### ML-001: Detection d'anomalies avec Isolation Forest
- Nouveau module `app/ml/` cree
- `IsolationForest` de scikit-learn avec contamination a 10%
- Features encodees: severity, event_type, heure/minute, hash IP source/cible
- Modele entraine sur les evenements de la base PostgreSQL
- Endpoint `POST /correlation/ml-detect` pour detection batch

### ML-002: Integration ML dans la correlation
- Endpoint `POST /correlation/{id}/ml-enrich` pour enrichir un groupe
- Score d'anomalie moyen calcule par groupe
- Boost de severite automatique si score > 0.5 (ex: medium → high)
- Fonction `enrich_with_ml_scores()` dans `correlation/service.py`

### ML-003: Dashboard ML anomaly detection
- Panneau ML ajoute en tete de la page Correlations
- Bouton "Lancer l'analyse ML" avec summary en temps reel
- Affichage: total events, anomalies, taux d'anomalie, score moyen
- Barre de progression ML sur chaque carte de correlation
- Bouton "Analyser avec ML" sur les groupes non encore analyses

## Verification Technique

| Controle | Resultat | Preuve |
|---|---|---|
| Installation sklearn | OK | `scikit-learn==1.5.2` dans requirements.txt |
| Docker rebuild | OK | Container recree avec succes |
| ML Summary endpoint | OK | 473 events analyses, 47 anomalies detectees (9.9%) |
| ML Enrich endpoint | OK | Group #1 enrichi: 9 anomalies, score 0.473 |
| Correlation temporelle | OK | 1 groupe cree avec 96 events |
| GitHub Project sync | OK | 32 issues total, toutes en Done |

## Resultats ML sur les donnees actuelles

```json
{
  "total": 473,
  "anomalies": 47,
  "anomaly_rate": 0.099,
  "avg_score": 0.455,
  "model_ready": true
}
```

- **473 evenements** analyses
- **47 anomalies** detectees (9.9% - proche de la contamination cible de 10%)
- **Score moyen**: 0.455 (modere, les attaques simulees sont bien capturees par les regles)

## Dependances ajoutees

```
scikit-learn==1.5.2
numpy==2.1.3
```

## GitHub Project

Project: `DevinciWatch Scrum Board` (https://github.com/users/yugmerabtene/projects/8/views/1)

**32 issues total**, toutes marquees `Done`.

## Risques Et Blocages

| Niveau | Sujet | Impact | Action |
|---|---|---|---|
| Faible | Taille image Docker augmente (~200MB avec sklearn) | Image plus lourde | Acceptable pour MVP |
| Faible | Modele non persiste entre redemarrages | Re-entrainement necessaire | Normal pour MVP |

## Decision Fin De Sprint

Sprint 8 (ML) est **Done**. La detection d'anomalies ML complemente efficacement la correlation rule-based.

## Statut Global du Projet

| EPIC | Objectif | Statut |
|---|---|---|
| EPIC-01 | Socle applicatif et securite | ✅ Done |
| EPIC-02 | Collecte endpoint et telemetrie | ✅ Done |
| EPIC-03 | Decouverte reseau et actifs | ✅ Done |
| EPIC-04 | Detection, alertes et audit | ✅ Done |
| EPIC-05 | Correlation et enrichissement | ✅ Done + ML |
| EPIC-06 | Interface web et visualisation | ✅ Done + ML UI |
| EPIC-07 | Reporting, exports et preuves | ✅ Done |
| EPIC-08 | Lab Docker, demonstration | ✅ Done |

**Total: 118/118 SP** — **32/32 issues Done** — **8/8 EPICs**
