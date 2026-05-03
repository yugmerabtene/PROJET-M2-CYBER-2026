# Gestion de projet - DevinciWatch

## 1. Objet du document

Ce document définit l'organisation et les modalités de pilotage du projet DevinciWatch. Il transforme le cadrage stratégique en dispositif d'exécution : méthode de travail, responsabilités, jalons, suivi des risques et critères de décision.

Il sert à préciser :

- la méthode de travail ;
- les rôles ;
- les jalons ;
- les risques ;
- les mécanismes de suivi.

Son objectif est de garantir que la progression du projet reste lisible, mesurable et cohérente avec les attentes produit, le périmètre MVP et les contraintes de démonstration.

## 2. Position dans la chronologie projet

Ce document intervient après :

- le [kick-off](../01_documents_pedagogiques/kickoff/KICKOFF.md) ;
- l'[étude de marché](../02_etude_de_marche/rendu_principal.md) ;
- le [business model](../03_business_model/rendu_principal.md) ;
- le [business plan](../04_business_plan/rendu_principal.md) ;
- la [feuille de cadrage](../05_feuille_de_cadrage/rendu_principal.md).

Il précède :

- le [cahier des charges](../07_cahier_des_charges/rendu_principal.md) ;
- l'[architecture détaillée](../08_architecture/rendu_principal.md) ;
- le développement du produit.

## 3. Méthode de travail retenue

La méthode retenue est une approche itérative et pragmatique, adaptée à un projet produit avec démonstration attendue. Elle privilégie des incréments courts, vérifiables et directement reliés à la chaîne de valeur du produit : collecte, détection, corrélation, alerte, preuve et restitution.

Principes de pilotage :

- avancer par incréments fonctionnels ;
- garder un MVP démontrable rapidement ;
- documenter les décisions ;
- prioriser les fonctions visibles en démonstration produit ;
- contrôler la dérive du périmètre.

## 4. Organisation cible

Les responsabilités projet doivent couvrir au minimum :

- pilotage global ;
- architecture et backend ;
- interface web ;
- collecte / endpoint / scénarios de test ;
- documentation / démonstration / qualité.

Même si les rôles exacts peuvent évoluer, la répartition des responsabilités doit rester explicite. Cette exigence évite les angles morts classiques des projets techniques : fonctionnalités développées sans propriétaire, documentation produite trop tard, ou démonstration préparée après la stabilisation du produit.

## 5. Gouvernance

### Décisions structurantes

Doivent être validées sur :

- le périmètre MVP ;
- l'architecture retenue ;
- la stratégie de démonstration ;
- les critères d'acceptation ;
- la gestion des risques critiques.

### Réunions et suivi

Cadence recommandée :

- point court de suivi régulier ;
- revue d'avancement hebdomadaire ;
- point de synchronisation avant toute décision structurante.

## 6. Découpage de l'exécution

### Phase 1 - cadrage

- consolidation des besoins ;
- feuille de cadrage ;
- gestion de projet ;
- cahier des charges ;
- architecture.

### Phase 2 - socle technique

- backend FastAPI ;
- base de données ;
- structure du lab Docker ;
- collecte endpoint minimale.

### Phase 3 - capacités cœur produit

- découverte réseau ;
- actifs ;
- événements ;
- alertes ;
- audit.

### Phase 4 - enrichissement analyste

- corrélation ;
- métriques ;
- historique ;
- exports ;
- visualisation enrichie.

### Phase 5 - finalisation validation

- stabilisation ;
- démonstration ;
- documentation finale ;
- support de présentation.

## 7. Jalons projet

Jalons recommandés :

1. cadrage validé ;
2. architecture validée ;
3. socle technique opérationnel ;
4. chaîne collecte -> alerte fonctionnelle ;
5. interface web démontrable ;
6. corrélation visible ;
7. exports et audit prêts ;
8. démonstration finale stabilisée.

Chaque jalon doit être associé à une preuve concrète : document validé, fonctionnalité exécutable, scénario reproductible, capture de résultat ou export exploitable. Cette logique de preuve permet de relier le pilotage projet à la validation finale.

## 8. Livrables de pilotage

- feuille de cadrage ;
- gestion de projet ;
- cahier des charges ;
- architecture ;
- documentation technique ;
- support de démonstration.

## 9. Risques projet

Risques principaux :

- dérive du périmètre ;
- sous-estimation de la corrélation ;
- surcharge du serveur SOC de démonstration ;
- complexité excessive du frontend ;
- manque de temps sur les tests et la stabilisation.

## 10. Mesures de maîtrise

- MVP strictement priorisé ;
- architecture simple à démontrer ;
- revues régulières d'avancement ;
- suivi explicite des jalons ;
- documentation tenue à jour au fil de l'exécution.

## 11. Indicateurs de suivi projet

Indicateurs recommandés :

- avancement par lot ;
- nombre de jalons validés ;
- stabilité de la démonstration ;
- couverture des fonctions MVP ;
- nombre de risques ouverts / maîtrisés.

## 12. Dépendances documentaires

- [Feuille de cadrage](../05_feuille_de_cadrage/rendu_principal.md)
- [Cahier des charges](../07_cahier_des_charges/rendu_principal.md)
- [Architecture](../08_architecture/rendu_principal.md)
- [Business plan](../04_business_plan/rendu_principal.md)

## 13. Conclusion

La gestion de projet retenue pour DevinciWatch vise à maintenir une exécution lisible, priorisée et démontrable. Elle sert de pont entre le cadrage stratégique, les exigences détaillées et la mise en œuvre technique. Sa qualité sera mesurée à la capacité de l'équipe à arbitrer rapidement, à documenter les décisions et à produire une démonstration stable, cohérente et défendable.
