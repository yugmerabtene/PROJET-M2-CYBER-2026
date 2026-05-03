# Cahier des charges - DevinciWatch

## 1. Objet du document

Le présent cahier des charges formalise les besoins, les contraintes, le périmètre, les exigences fonctionnelles et non fonctionnelles ainsi que les critères d'acceptation du projet DevinciWatch.

Il constitue le document de référence pour le développement du produit et s'appuie sur :

- le kick-off pédagogique ;
- l'étude de marché ;
- le business model ;
- le business plan ;
- l'architecture produit retenue.

## 2. Contexte du projet

DevinciWatch est un projet de cybersurveillance réseau orienté SOC. Son ambition est de proposer une solution pragmatique de supervision, de détection et de preuve à destination d'organisations qui ont besoin de visibilité cyber sans supporter la lourdeur d'une plateforme SIEM enterprise.

Le projet doit répondre à deux niveaux d'attente :

- un besoin pédagogique, défini par le sujet et la soutenance ;
- un besoin produit, défini par les études réalisées et le positionnement retenu.

## 3. Problématique à résoudre

Les organisations ciblées doivent pouvoir :

- identifier les équipements présents sur leur réseau ;
- observer le trafic et les événements pertinents ;
- détecter des comportements suspects ;
- comprendre la répétition ou la corrélation d'attaques ;
- générer des alertes actionnables ;
- produire des preuves exploitables via journalisation, historique et exports.

## 4. Objectifs du produit

Le produit doit permettre de :

1. collecter des données depuis un endpoint supervisé ;
2. découvrir le périmètre réseau observable ;
3. analyser le trafic, les logs et certains comportements suspects ;
4. produire des alertes simples et des alertes enrichies par corrélation ;
5. offrir une interface web moderne d'analyse ;
6. produire des exports exploitables en CSV, JSON et, si possible, XML ;
7. soutenir une démonstration claire en environnement Docker.

## 5. Périmètre fonctionnel

### 5.1. Fonctions incluses

- authentification utilisateur ;
- gestion de rôles ;
- collecte de `heartbeat` ;
- collecte d'événements ;
- découverte réseau ;
- scan IP ;
- détection de ports ouverts ;
- collecte d'informations de services ;
- observation de trafic réseau ;
- analyse de logs ;
- génération d'alertes ;
- corrélation de signaux répétés ;
- consultation d'actifs, d'événements et d'alertes ;
- historisation et journalisation ;
- métriques de supervision ;
- exports ;
- visualisation géographique des attaques ;
- affichage des IP attaquantes.

### 5.2. Fonctions hors périmètre initial

- réponse automatique avancée ;
- orchestration SOAR ;
- multi-tenant complet ;
- couverture SIEM exhaustive ;
- moteur de détection enterprise complexe.

## 6. Parties prenantes

### Utilisateurs cibles

- administrateur ;
- analyste ;
- démonstrateur / jury en contexte pédagogique.

### Parties concernées

- équipe projet ;
- encadrants pédagogiques ;
- utilisateurs de démonstration ;
- décideurs métier dans une logique future de valorisation.

## 7. Exigences fonctionnelles détaillées

### 7.1. Authentification et contrôle d'accès

Le système doit permettre :

- l'authentification sécurisée des utilisateurs ;
- la distinction entre rôles `admin` et `analyst` ;
- la restriction des actions sensibles selon le rôle.

### 7.2. Collecte endpoint

Le serveur-endpoint doit permettre :

- l'émission de `heartbeat` ;
- la remontée d'événements ;
- l'observation de trafic réseau ;
- la collecte de journaux utiles ;
- la remontée d'indicateurs de comportements suspects.

### 7.3. Découverte réseau

Le système doit permettre :

- le scan de plages IP définies ;
- l'identification d'équipements observables ;
- la détection des ports ouverts ;
- la récupération d'informations de services quand elles sont disponibles.

### 7.4. Gestion des actifs

Le système doit maintenir un inventaire d'actifs contenant au minimum :

- identifiant d'actif ;
- adresse IP ;
- ports ou services observés ;
- date de dernière observation ;
- éléments de contexte utiles à l'analyse.

### 7.5. Détection et alerting

Le système doit produire :

- des alertes issues de règles simples ;
- des alertes enrichies par corrélation ;
- un cycle de vie minimal des alertes ;
- des vues de consultation et de détail.

### 7.6. Corrélation

Le système doit corréler :

- plusieurs événements provenant d'une même IP ;
- des répétitions dans une fenêtre temporelle ;
- des séquences de comportements ;
- des attaques répétées sur une même cible ;
- des agrégats d'événements liés à une campagne ou à un pattern récurrent.

### 7.7. Interface web

L'interface doit être moderne, lisible et orientée analyste.

Elle doit permettre :

- l'affichage d'un dashboard ;
- l'affichage de métriques SOC ;
- l'accès à l'historique d'événements et d'alertes ;
- la consultation des journaux ;
- la consultation des actifs ;
- la consultation des IP attaquantes ;
- l'affichage d'une carte géographique des attaques ;
- la consultation des corrélations.

### 7.8. Reporting et exports

Le système doit permettre :

- l'export CSV ;
- l'export JSON ;
- l'export XML si possible dans le calendrier prévu ;
- la production de données exploitables pour soutenance et preuve.

### 7.9. Audit et journalisation

Le système doit journaliser au minimum :

- authentification ;
- consultation ou traitement d'alertes ;
- exports ;
- actions sensibles liées à l'administration.

## 8. Exigences non fonctionnelles

### 8.1. Sécurité

- authentification obligatoire ;
- séparation des rôles ;
- restriction des actions sensibles ;
- journalisation des opérations critiques.

### 8.2. Qualité logicielle

- code structuré ;
- architecture modulaire ;
- validation stricte des données d'entrée ;
- code testable ;
- conventions cohérentes.

### 8.3. Performance fonctionnelle

- réponse fluide sur les parcours de démonstration ;
- traitement différé des opérations lourdes ;
- persistance fiable des événements et alertes.

### 8.4. Observabilité

- endpoint de santé ;
- logs applicatifs ;
- métriques minimales de supervision.

### 8.5. Déployabilité

- environnement Docker reproductible ;
- lab de démonstration en 3 conteneurs ;
- séparation claire entre serveur SOC, endpoint et attaquant.

## 9. Architecture de démonstration retenue

L'environnement de démonstration doit comporter :

- `serveur-soc` ;
- `serveur-endpoint` ;
- `serveur-attacker`.

Le `serveur-soc` embarque pour le MVP :

- frontend web ;
- backend FastAPI ;
- PostgreSQL ;
- Redis ;
- Celery.

## 10. Données manipulées

Le système doit manipuler au minimum :

- utilisateurs ;
- rôles ;
- actifs ;
- événements ;
- résultats de découverte réseau ;
- alertes ;
- groupes de corrélation ;
- profils d'IP attaquantes ;
- journaux d'audit ;
- exports.

## 11. Critères d'acceptation

Le produit sera considéré comme conforme si les points suivants sont démontrés :

1. un endpoint remonte correctement `heartbeat` et `events` ;
2. le système détecte des actifs, ports ou services ;
3. des comportements suspects sont observés depuis le serveur-endpoint ;
4. des alertes sont générées ;
5. au moins une logique de corrélation fonctionne ;
6. l'interface permet la consultation des données clés ;
7. l'historique et la journalisation sont visibles ;
8. un export exploitable est produit ;
9. la démonstration fonctionne dans le lab Docker prévu.

## 12. Priorisation

### Priorité 1 - indispensable

- authentification ;
- collecte ;
- découverte réseau minimale ;
- alertes ;
- historique ;
- audit minimal ;
- export CSV ;
- démonstration Docker.

### Priorité 2 - fortement souhaitable

- corrélation par IP et fenêtre temporelle ;
- métriques SOC ;
- carte géographique ;
- visualisation des IP attaquantes.

### Priorité 3 - extension si temps disponible

- export XML ;
- enrichissements avancés ;
- corrélation plus poussée ;
- raffinements visuels supplémentaires.

## 13. Contraintes projet

- backend Python / FastAPI imposé ;
- frontend web cohérent avec la démonstration ;
- dépôt structuré ;
- architecture défendable ;
- démonstration claire ;
- livrables exploitables en soutenance.

## 14. Références de cadrage

- `../01_documents_pedagogiques/kickoff/KICKOFF.md`
- `../02_etude_de_marche/rendu_principal.md`
- `../03_business_model/rendu_principal.md`
- `../04_business_plan/rendu_principal.md`
- `../../product/architecture.md`

## 15. Conclusion

Ce cahier des charges fixe un périmètre clair, cohérent avec le sujet académique, le positionnement produit et l'architecture retenue. Il constitue la base opérationnelle du développement de DevinciWatch.
