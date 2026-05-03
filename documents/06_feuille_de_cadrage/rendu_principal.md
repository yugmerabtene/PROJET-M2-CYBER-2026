# Feuille de cadrage - DevinciWatch

## 1. Identité du projet

- **Nom du projet** : DevinciWatch
- **Nature** : projet de cybersurveillance réseau orienté SOC
- **Finalité** : concevoir un produit démontrable de supervision, détection, corrélation et preuve

## 2. Contexte

Le projet s'inscrit dans un cadre académique de cybersécurité avec des attendus techniques, méthodologiques et de valorisation. Il doit démontrer la capacité à transformer un besoin de supervision réseau en produit structuré, défendable et démontrable.

## 3. Besoin principal

Mettre à disposition une solution capable de :

- superviser un environnement réseau ;
- identifier des actifs et des services ;
- observer le trafic et les journaux ;
- détecter et corréler des comportements suspects ;
- produire des alertes, des historiques et des exports ;
- fournir des éléments de preuve en démonstration.

## 4. Problème adressé

Les structures ciblées ont besoin de visibilité, de simplicité d'exploitation et de preuve, sans recourir à une plateforme trop lourde ou difficile à opérer.

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

## 9. Architecture de référence retenue

Le produit s'appuie sur :

- Python ;
- FastAPI ;
- PostgreSQL ;
- Redis ;
- Celery ;
- lab Docker de démonstration en 3 conteneurs.

Référence : `../../product/architecture.md`

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

## 15. Dépendances documentaires

- `../01_documents_pedagogiques/kickoff/KICKOFF.md`
- `../02_etude_de_marche/rendu_principal.md`
- `../03_business_model/rendu_principal.md`
- `../04_business_plan/rendu_principal.md`
- `../05_cahier_des_charges/rendu_principal.md`
- `../../product/architecture.md`

## 16. Feuille de route courte

1. stabiliser le cadrage fonctionnel ;
2. démarrer le socle backend ;
3. intégrer collecte et persistance ;
4. intégrer découverte et détection ;
5. intégrer corrélation ;
6. construire l'interface web ;
7. préparer la démonstration et les exports.

## 17. Conclusion

Cette feuille de cadrage fixe une vision opérationnelle commune du projet. Elle permet de relier le besoin, la valeur, l'architecture, les livrables et les priorités d'exécution dans une même base de pilotage.
