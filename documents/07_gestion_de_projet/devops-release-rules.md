# Règles DevOps - Release Management

## Objectif
Assurer des livraisons régulières, tracables et stables du projet DevinciWatch.

## Règles de Release

### 1. Cadence des releases
- Une **release régulière** doit être publiée sur le repository.
- Cadence recommandée : **1 release par sprint** ou **1 release stable toutes les 1 à 2 semaines**.
- Chaque release doit être taguée avec un versionnement **SemVer** : `vMAJOR.MINOR.PATCH` (ex: `v0.6.0`).

### 2. Contenu d'une release
Chaque release doit inclure :

#### Obligatoire
- **Changelog clair** listant :
  - Nouvelles fonctionnalités
  - Corrections de bugs
  - Changements de schéma DB (migrations)
  - Impacts Docker (nouveaux services, variables d'environnement)
  - Endpoints API ajoutés/modifiés
  - Tests validés

#### Recommandé
- Lien vers les EPICs/US associés
- Captures d'écran pour les changements UI majeurs
- Notes de migration si applicable

### 3. Processus de création
1. **Validation pré-release** :
   - Tests Docker passés (`docker compose up` fonctionnel)
   - Endpoints critiques validés
   - DB migrations testées

2. **Création du tag** :
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z: <description>"
   git push origin vX.Y.Z
   ```

3. **GitHub Release** :
   - Titre : `vX.Y.Z - <Nom de la release>`
   - Description : Générée à partir du changelog
   - Pièces jointes : Fichiers de migration SQL si applicable

### 4. Critères de bloquage
Aucune release ne peut être créée si :
- Les tests Docker échouent
- Une migration DB est incorrecte
- Des credentials sont exposés dans le code
- Le `CHANGELOG.md` est vide pour cette version

### 5. Versioning spécifique
- **MAJOR (X)** : Changements incompatibles (ex: v1.0.0 → v2.0.0)
- **MINOR (Y)** : Nouvelles fonctionnalités rétrocompatibles (ex: v0.5.0 → v0.6.0)
- **PATCH (Z)** : Corrections de bugs rétrocompatibles (ex: v0.5.0 → v0.5.1)

### 6. Releases incrémentales pour grosses features
Pour des EPICs majeurs (comme EPIC-05 Corrélation ou EPIC-11 Attack Lab) :
- Livrer en **releases incrémentales** (v0.6.0, v0.7.0, v0.8.0)
- Ne pas attendre la complétion totale pour une grosse release unique
- Chaque release doit être utilisable de manière autonome

### 7. Automatisation (futur)
- GitHub Actions pour création automatique de release
- Génération automatique du changelog depuis les commits
- Tests automatiques pré-release

## Exemple de CHANGELOG.md

```markdown
# Changelog

## [v0.6.0] - 2026-05-08
### Added
- EPIC-05: Nouveaux champs de corrélation (correlation_score, hostname, attack_chain)
- EPIC-11: Attack Lab backend avec job runner
- i18n: Support 6 langues (FR, EN, ES, DE, AR, IT)

### Changed
- DB: Nouvelles colonnes correlation_groups et correlated_events

### Technical
- Docker: attacker enrichi avec nmap, nikto, ffuf, hydra
- Frontend: Alpine.js avec système i18n dynamique
```

## Responsabilités
- **Lead Dev** : Validation finale avant release
- **DevOps** : Création des tags, GitHub Releases
- **QA** : Validation Docker et tests
