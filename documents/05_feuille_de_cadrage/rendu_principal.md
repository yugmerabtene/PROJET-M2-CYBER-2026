# Feuille de cadrage - DevinciWatch

## 1. Identité du projet

- **Nom du projet** : DevinciWatch
- **Nature** : projet de cybersurveillance réseau orienté SOC
- **Finalité** : concevoir un produit démontrable de supervision, détection, corrélation et preuve

## 2. Contexte

Le projet s'inscrit dans un cadre académique de cybersécurité avec des attendus techniques, méthodologiques et de valorisation. Il doit démontrer la capacité à transformer un besoin de supervision réseau en produit structuré, défendable et démontrable.

La feuille de cadrage joue ici un rôle de document-pivot. Elle traduit les enseignements issus de l'[étude de marché](../02_etude_de_marche/rendu_principal.md), du [business model](../03_business_model/rendu_principal.md) et du [business plan](../04_business_plan/rendu_principal.md) en décisions de périmètre, de priorisation et d'exécution. Elle permet également de préparer le passage vers le [cahier des charges](../07_cahier_des_charges/rendu_principal.md) et l'[architecture](../08_architecture/rendu_principal.md).

## 3. Besoin principal

Mettre à disposition une solution capable de :

- superviser un environnement réseau ;
- identifier des actifs et des services ;
- observer le trafic et les journaux ;
- détecter et corréler des comportements suspects ;
- produire des alertes, des historiques et des exports ;
- fournir des éléments de preuve en démonstration.

## 4. Problème adressé

Les structures ciblées ont besoin de visibilité, de simplicité d'exploitation et de preuve, sans recourir à une plateforme trop lourde ou difficile à opérer. Le problème adressé n'est donc pas seulement l'absence d'information technique ; il concerne aussi la capacité à qualifier cette information, à la présenter clairement et à la transformer en éléments exploitables pour une décision ou une soutenance.

## 5. Objectifs projet

### Objectifs fonctionnels

- collecte endpoint ;
- découverte réseau ;
- alertes ;
- corrélation ;
- interface web ;
- métriques ;
- exports ;
- journalisation ;
- cartographie des attaques.

### Objectifs pédagogiques

- démontrer une architecture cohérente ;
- produire un dépôt clair ;
- soutenir un raisonnement de conception ;
- présenter une solution techniquement et fonctionnellement maîtrisée.

## 6. Périmètre

### Inclus

- `serveur-soc`
- `serveur-endpoint`
- `serveur-attacker`
- lab Docker de démonstration
- backend FastAPI
- frontend intégré au serveur SOC pour le MVP

### Exclu du premier périmètre

- réponse automatique avancée ;
- architecture d'exploitation distribuée complète ;
- multi-tenant ;
- SIEM enterprise complet.

## 7. Utilisateurs cibles

- analyste SOC junior ou intermédiaire ;
- administrateur ;
- jury / démonstrateur en soutenance.

## 8. Proposition de valeur projet

DevinciWatch propose une supervision cyber réseau pragmatique, démontrable et exploitable, combinant visibilité, alertes, corrélation, historique et preuve dans une architecture simple à expliquer et à mettre en œuvre.

La valeur du projet repose sur une articulation entre rigueur technique et lisibilité opérationnelle : l'utilisateur doit pouvoir comprendre ce qui est observé, pourquoi une alerte est produite, comment les événements sont reliés entre eux et quelles preuves peuvent être exportées.

## 9. Architecture de référence retenue

Le produit s'appuie sur :

- Python ;
- FastAPI ;
- PostgreSQL ;
- Redis ;
- Celery ;
- lab Docker de démonstration en 3 conteneurs.

Référence : [Architecture produit (08)](../08_architecture/rendu_principal.md)

## 10. Livrables attendus

- produit fonctionnel démontrable ;
- dépôt GitHub structuré ;
- documentation claire ;
- exports de preuve ;
- support de présentation ;
- démonstration soutenance.

## 11. Critères de succès

Le projet sera jugé réussi si :

- la chaîne complète collecte -> détection -> corrélation -> alerte -> preuve fonctionne ;
- l'interface web permet une lecture claire de la situation ;
- les scénarios de démonstration sont reproductibles ;
- le dépôt permet de comprendre et défendre l'architecture ;
- les livrables sont cohérents entre eux.

## 12. Risques principaux

- dérive du périmètre ;
- sous-estimation de la complexité de corrélation ;
- trop forte ambition visuelle du frontend ;
- surcharge du conteneur `serveur-soc` pour la démonstration ;
- manque de temps sur les tests et la finition.

## 13. Mesures de maîtrise

- priorisation stricte du MVP ;
- corrélation simple mais démontrable ;
- architecture modulaire ;
- environnement Docker reproductible ;
- documentation de référence maintenue à jour.

## 14. Décisions structurantes déjà prises

- architecture produit de référence rédigée ;
- frontend intégré au même conteneur que le backend pour le MVP ;
- démonstration en 3 conteneurs ;
- focus sur supervision, corrélation, historique, preuves et exports ;
- orientation produit cohérente avec les études réalisées.

Ces décisions doivent rester stables pendant la phase MVP. Toute extension fonctionnelle devra être évaluée au regard de son apport démonstratif, de sa faisabilité dans le calendrier et de son impact sur la simplicité de l'architecture.

## 15. Dépendances documentaires

- [Kick-off pédagogique (01)](../01_documents_pedagogiques/kickoff/KICKOFF.md)
- [Étude de marché (02)](../02_etude_de_marche/rendu_principal.md)
- [Business model (03)](../03_business_model/rendu_principal.md)
- [Business plan (04)](../04_business_plan/rendu_principal.md)
- [Gestion de projet (06)](../06_gestion_de_projet/rendu_principal.md)
- [Cahier des charges (07)](../07_cahier_des_charges/rendu_principal.md)
- [Architecture produit (08)](../08_architecture/rendu_principal.md)

## 16. Feuille de route courte

1. Phase 1 - Cadrage : consolider le cadrage, finaliser la gestion de projet, le cahier des charges et l'architecture ;
2. Phase 2 - Socle technique : mettre en place le backend FastAPI, la base de données, le lab Docker et la collecte endpoint minimale ;
3. Phase 3 - Cœur produit : intégrer la découverte réseau, les actifs, les événements, les alertes et l'audit ;
4. Phase 4 - Enrichissement analyste : ajouter la corrélation, les métriques, l'historique, les exports et la visualisation ;
5. Phase 5 - Finalisation soutenance : stabiliser la démonstration, la documentation finale et le support.

## 17. Conclusion

Cette feuille de cadrage fixe une vision opérationnelle commune du projet. Elle permet de relier le besoin, la valeur, l'architecture, les livrables et les priorités d'exécution dans une même base de pilotage. Elle prépare directement le [cahier des charges (07)](../07_cahier_des_charges/rendu_principal.md) et l'[architecture détaillée (08)](../08_architecture/rendu_principal.md), en cohérence avec la [gestion de projet (06)](../06_gestion_de_projet/rendu_principal.md).
