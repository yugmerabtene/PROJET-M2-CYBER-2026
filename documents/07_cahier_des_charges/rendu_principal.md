# Cahier des charges - DevinciWatch

## 1. Objet du document

Le présent cahier des charges formalise les besoins, le périmètre, les contraintes, les exigences fonctionnelles et non fonctionnelles ainsi que les critères de validation du projet DevinciWatch.

Il a une fonction contractuelle au sein du projet : il transforme les orientations de cadrage en exigences vérifiables, suffisamment précises pour guider le développement et suffisamment lisibles pour être défendues lors d'une revue projet. Il constitue également une base de dialogue entre les dimensions produit, projet et technique.

Ce document s'appuie sur :

- le [kick-off projet (01)](../01_documents_pedagogiques/kickoff/KICKOFF.md) ;
- l'[étude de marché (02)](../02_etude_de_marche/rendu_principal.md) ;
- le [business model (03)](../03_business_model/rendu_principal.md) ;
- le [business plan (04)](../04_business_plan/rendu_principal.md) ;
- la [feuille de cadrage (05)](../05_feuille_de_cadrage/rendu_principal.md) ;
- la [gestion de projet (06)](../06_gestion_de_projet/rendu_principal.md) ;
- l'[architecture produit retenue (08)](../08_architecture/rendu_principal.md).

## 2. Fiche documentaire

| Élément | Valeur |
|---|---|
| Projet | DevinciWatch |
| Document | Cahier des charges fonctionnel et technique |
| Version | 1.1 |
| Statut | Version consolidée de cadrage MVP |
| Périmètre | Produit MVP démontrable en environnement Docker |
| Public visé | Équipe projet, parties prenantes, contributeurs techniques, responsables de validation |
| Document précédent | [Gestion de projet (06)](../06_gestion_de_projet/rendu_principal.md) |
| Document suivant | [Architecture produit (08)](../08_architecture/rendu_principal.md) |

### Historique des versions

| Version | Objet | Statut |
|---|---|---|
| 1.0 | Formalisation initiale du périmètre, des exigences et des critères d'acceptation | Référence initiale |
| 1.1 | Enrichissement professionnel : exigences numérotées, sécurité, données, recette et traçabilité | Version consolidée |

## 3. Résumé exécutif

DevinciWatch est une solution de cybersurveillance réseau orientée SOC. Le produit vise à superviser un environnement de démonstration, collecter de la télémétrie depuis un endpoint, identifier des actifs, détecter des comportements suspects, corréler des signaux répétés, produire des alertes et générer des preuves exploitables sous forme d'historique, de journaux et d'exports.

Le cahier des charges retient une logique de MVP démontrable. L'objectif n'est pas de reproduire toute la complexité d'un SIEM enterprise, mais de prouver une chaîne fonctionnelle complète : observation réseau, ingestion, persistance, détection, corrélation, visualisation, audit et export de preuve.

La réussite du produit sera évaluée sur sa capacité à être lancé dans un lab Docker reproductible, à produire des résultats observables et à expliquer clairement les choix techniques réalisés.

## 4. Contexte et problématique

Le projet répond à deux niveaux d'attente :

- un besoin de démonstration produit, défini par le périmètre MVP et les critères de validation ;
- un besoin de valorisation produit, défini par les études réalisées, le positionnement retenu et l'opportunité identifiée sur le marché.

Les organisations ciblées doivent pouvoir :

- identifier les équipements présents sur leur réseau ;
- observer le trafic et les événements pertinents ;
- détecter des comportements suspects ;
- comprendre la répétition ou la corrélation d'attaques ;
- générer des alertes actionnables ;
- produire des preuves exploitables via journalisation, historique et exports.

La problématique peut être formulée ainsi : comment produire une visibilité cyber suffisamment riche pour être utile, tout en conservant une architecture simple, testable et compatible avec un environnement de démonstration contrôlé ?

## 5. Objectifs du produit

### Objectif général

Concevoir une application web de supervision cyber réseau capable de démontrer une chaîne SOC minimale, depuis la collecte endpoint jusqu'à la production de preuves exportables.

### Objectifs opérationnels

| ID | Objectif | Résultat attendu |
|---|---|---|
| OBJ-001 | Collecter de la télémétrie depuis un endpoint supervisé | `heartbeat` et `events` reçus, persistés et consultables |
| OBJ-002 | Découvrir le périmètre réseau observable | Actifs, ports et services identifiés dans le lab |
| OBJ-003 | Détecter des comportements suspects | Alertes générées à partir de règles simples |
| OBJ-004 | Corréler des signaux répétés | Regroupement d'événements liés à une IP, une cible ou une fenêtre temporelle |
| OBJ-005 | Restituer l'information à un analyste | Dashboard, vues d'alertes, actifs, événements et corrélations |
| OBJ-006 | Produire une preuve exploitable | Export CSV ou JSON généré pendant la démonstration |
| OBJ-007 | Soutenir une démonstration reproductible | Lab Docker en 3 conteneurs opérationnel |

## 6. Périmètre du MVP

### 6.1. Fonctions incluses

- authentification utilisateur ;
- gestion des `roles` ;
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
- exports CSV et JSON ;
- visualisation géographique des attaques si le calendrier le permet ;
- affichage des IP attaquantes.

### 6.2. Fonctions hors périmètre initial

- réponse automatique avancée ;
- orchestration SOAR ;
- multi-tenant complet ;
- couverture SIEM exhaustive ;
- moteur de détection enterprise complexe ;
- déploiement distribué de production ;
- supervision de réseaux externes au lab Docker ;
- traitement de charges offensives destructrices ou malware réel.

Cette exclusion constitue un choix de maîtrise. Le périmètre initial se concentre sur les fonctionnalités qui démontrent le mieux la valeur du projet dans le temps disponible.

## 7. Parties prenantes et utilisateurs

### 7.1. Parties prenantes

| Partie prenante | Rôle dans le projet | Attentes principales |
|---|---|---|
| Équipe projet | Conception, développement, documentation et démonstration | Périmètre clair, architecture défendable, livrables cohérents |
| Responsables de validation | Évaluation de la conformité du produit aux exigences | Traçabilité, cohérence, résultats observables |
| Parties prenantes métier | Appréciation de la valeur opérationnelle | Démonstration fluide, preuves exploitables, lisibilité produit |
| Futurs utilisateurs métier | Référence de valorisation produit | Lisibilité, simplicité, valeur opérationnelle |

### 7.2. Utilisateurs cibles

| Profil | Description | Besoins principaux |
|---|---|---|
| Administrateur | Utilisateur responsable de la configuration minimale et des accès | Authentifier, gérer les `roles`, consulter l'état du système |
| Analyste | Utilisateur chargé de l'investigation et de la qualification des alertes | Voir les actifs, événements, alertes, corrélations et exports |
| Responsable validation | Utilisateur observant les scénarios de recette | Comprendre la chaîne fonctionnelle et vérifier les preuves |

## 8. Glossaire

| Terme | Définition |
|---|---|
| Actif | Équipement, hôte ou ressource réseau observable par le système |
| Alerte | Signal produit par une règle de détection ou par une corrélation |
| Audit log | Journal retraçant une action sensible ou significative |
| Corrélation | Regroupement de plusieurs événements liés par une IP, une cible, une fenêtre temporelle ou un comportement |
| Endpoint | Hôte supervisé qui produit de la télémétrie |
| Event | Événement technique remonté par l'endpoint |
| Heartbeat | Signal périodique indiquant qu'un endpoint est actif |
| MVP | Minimum Viable Product, version minimale démontrable du produit |
| SIEM | Security Information and Event Management |
| SOC | Security Operations Center |
| `serveur-soc` | Conteneur central embarquant interface web, API, base, Redis et worker pour le MVP |
| `serveur-endpoint` | Conteneur représentant l'hôte supervisé |
| `serveur-attacker` | Conteneur générant des scénarios de test contrôlés |

## 9. Hypothèses, contraintes et dépendances

### 9.1. Hypothèses

- Le projet est réalisé dans un cadre de validation produit avec une démonstration attendue.
- Le MVP doit être suffisamment complet pour montrer une chaîne fonctionnelle de supervision et de preuve.
- L'environnement Docker constitue le périmètre officiel de démonstration.
- Les scénarios offensifs restent contrôlés, non destructeurs et limités au réseau de lab.
- Les exports CSV et JSON sont prioritaires ; XML reste une extension si le calendrier le permet.

### 9.2. Contraintes

- backend Python / FastAPI imposé ;
- frontend web cohérent avec la démonstration ;
- dépôt structuré et documenté ;
- architecture défendable techniquement ;
- lab Docker reproductible ;
- livrables exploitables en revue projet ;
- cohérence obligatoire avec l'[architecture produit (08)](../08_architecture/rendu_principal.md).

### 9.3. Dépendances documentaires

- [Kick-off projet (01)](../01_documents_pedagogiques/kickoff/KICKOFF.md)
- [Étude de marché (02)](../02_etude_de_marche/rendu_principal.md)
- [Business model (03)](../03_business_model/rendu_principal.md)
- [Business plan (04)](../04_business_plan/rendu_principal.md)
- [Feuille de cadrage (05)](../05_feuille_de_cadrage/rendu_principal.md)
- [Gestion de projet (06)](../06_gestion_de_projet/rendu_principal.md)
- [Architecture produit (08)](../08_architecture/rendu_principal.md)

## 10. Exigences fonctionnelles

Les exigences fonctionnelles décrivent ce que le produit doit faire. Elles sont numérotées afin de faciliter la traçabilité avec les critères d'acceptation et les scénarios de recette.

### 10.1. Authentification et contrôle d'accès

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| F-AUTH-001 | Le système doit permettre l'authentification sécurisée des utilisateurs. | P1 | Un utilisateur valide accède au dashboard après connexion. |
| F-AUTH-002 | Le système doit distinguer les `roles` `admin` et `analyst`. | P1 | Les permissions diffèrent selon le `role`. |
| F-AUTH-003 | Le système doit restreindre les actions sensibles selon le `role`. | P1 | Un analyste ne peut pas exécuter une action réservée à l'administration. |

### 10.2. Collecte endpoint

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| F-TEL-001 | Le `serveur-endpoint` doit émettre un `heartbeat`. | P1 | Le dernier `heartbeat` est visible côté `serveur-soc`. |
| F-TEL-002 | Le `serveur-endpoint` doit remonter des événements. | P1 | Des `events` sont persistés et consultables. |
| F-TEL-003 | Le système doit collecter des journaux utiles à la détection. | P2 | Au moins une entrée de log est transformée en événement exploitable. |
| F-TEL-004 | Le système doit remonter des indicateurs de comportements suspects. | P1 | Un scénario contrôlé produit un événement suspect. |

### 10.3. Découverte réseau et actifs

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| F-DISC-001 | Le système doit scanner une plage IP définie dans le lab. | P1 | Une plage IP configurée est analysée. |
| F-DISC-002 | Le système doit identifier des équipements observables. | P1 | Au moins un actif est créé ou mis à jour. |
| F-DISC-003 | Le système doit détecter les ports ouverts quand ils sont observables. | P1 | Les ports détectés sont associés à un actif. |
| F-DISC-004 | Le système doit récupérer des informations de services quand elles sont disponibles. | P2 | Les services observés apparaissent dans le détail d'un actif. |
| F-ASSET-001 | Le système doit maintenir un inventaire d'actifs. | P1 | L'interface affiche les actifs connus. |

### 10.4. Détection et alerting

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| F-ALERT-001 | Le système doit produire des alertes issues de règles simples. | P1 | Un événement suspect génère une alerte. |
| F-ALERT-002 | Le système doit proposer une vue de liste des alertes. | P1 | Les alertes sont consultables dans l'interface. |
| F-ALERT-003 | Le système doit proposer une vue de détail d'une alerte. | P1 | Une alerte affiche son contexte, sa source et son horodatage. |
| F-ALERT-004 | Le système doit gérer un cycle de vie minimal des alertes. | P2 | Une alerte peut changer de statut ou être qualifiée. |

### 10.5. Corrélation

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| F-COR-001 | Le système doit corréler plusieurs événements provenant d'une même IP. | P1 | Plusieurs événements sont regroupés dans une corrélation. |
| F-COR-002 | Le système doit corréler des répétitions dans une fenêtre temporelle. | P2 | Une répétition produit un groupe de corrélation. |
| F-COR-003 | Le système doit associer une corrélation à une ou plusieurs alertes. | P2 | Une alerte enrichie référence un groupe de corrélation. |
| F-COR-004 | Le système doit afficher les corrélations dans l'interface. | P2 | L'analyste consulte les corrélations détectées. |

### 10.6. Interface web

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| F-UI-001 | L'interface doit proposer un dashboard de synthèse. | P1 | Le dashboard affiche des métriques utiles à la démonstration. |
| F-UI-002 | L'interface doit permettre la consultation des actifs. | P1 | La liste et le détail des actifs sont accessibles. |
| F-UI-003 | L'interface doit permettre la consultation des événements. | P1 | Les événements collectés sont visibles. |
| F-UI-004 | L'interface doit permettre la consultation des alertes. | P1 | Les alertes générées sont visibles. |
| F-UI-005 | L'interface doit permettre la consultation des journaux d'audit. | P2 | Les actions sensibles journalisées sont consultables. |
| F-UI-006 | L'interface peut afficher une carte géographique des attaques. | P3 | Une vue géographique apparaît si l'enrichissement est réalisé. |

### 10.7. Reporting et exports

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| F-EXP-001 | Le système doit produire un export CSV. | P1 | Un fichier CSV exploitable est généré. |
| F-EXP-002 | Le système doit produire un export JSON. | P1 | Un fichier JSON exploitable est généré. |
| F-EXP-003 | Le système peut produire un export XML si le calendrier le permet. | P3 | Un export XML est disponible en extension. |
| F-EXP-004 | Les exports doivent pouvoir servir de preuve opérationnelle. | P1 | L'export contient des données cohérentes avec le scénario joué. |

### 10.8. Audit et journalisation

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| F-AUD-001 | Le système doit journaliser les authentifications. | P1 | Une connexion génère une entrée d'audit. |
| F-AUD-002 | Le système doit journaliser les exports. | P1 | Un export génère une entrée d'audit. |
| F-AUD-003 | Le système doit journaliser les actions sensibles d'administration. | P2 | Une action sensible est traçable. |
| F-AUD-004 | Les journaux doivent être consultables par un profil autorisé. | P2 | Un utilisateur autorisé consulte les logs d'audit. |

## 11. Exigences non fonctionnelles

| ID | Catégorie | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|---|
| NF-QUAL-001 | Qualité | Le code doit être structuré par domaines fonctionnels. | P1 | La structure suit les modules définis dans l'architecture. |
| NF-QUAL-002 | Qualité | Les données d'entrée doivent être validées. | P1 | Un payload invalide est rejeté proprement. |
| NF-PERF-001 | Performance | Les parcours de démonstration doivent rester fluides. | P1 | Le dashboard et les vues principales répondent sans blocage perceptible. |
| NF-PERF-002 | Performance | Les traitements lourds doivent être différés. | P2 | Les tâches de détection ou d'export peuvent passer par Redis/Celery. |
| NF-OBS-001 | Observabilité | Le système doit exposer un endpoint de santé. | P1 | L'état applicatif est vérifiable. |
| NF-OBS-002 | Observabilité | Le système doit produire des logs applicatifs exploitables. | P1 | Les erreurs et actions importantes sont visibles dans les logs. |
| NF-DEP-001 | Déployabilité | Le projet doit être lançable dans un environnement Docker reproductible. | P1 | Les trois conteneurs démarrent selon la procédure prévue. |
| NF-MAINT-001 | Maintenabilité | Les conventions de nommage doivent rester cohérentes. | P1 | Les noms de modules, entités et conteneurs sont homogènes. |

## 12. Exigences de sécurité

Les exigences de sécurité s'inspirent de bonnes pratiques applicatives telles que l'OWASP ASVS, adaptées au niveau MVP du projet.

| ID | Exigence | Priorité | Critère d'acceptation |
|---|---|---|---|
| SEC-001 | L'accès à l'interface doit nécessiter une authentification. | P1 | Une page protégée n'est pas accessible sans session valide. |
| SEC-002 | Les actions sensibles doivent être contrôlées par `role`. | P1 | Un `analyst` ne peut pas effectuer une action réservée à `admin`. |
| SEC-003 | Les routes d'ingestion agent doivent être séparées des routes utilisateur. | P1 | Les endpoints agent sont identifiables et isolés fonctionnellement. |
| SEC-004 | Le `serveur-endpoint` doit s'authentifier auprès de l'API. | P1 | Une requête agent non autorisée est refusée. |
| SEC-005 | Les payloads entrants doivent être validés strictement. | P1 | Un payload mal formé produit une erreur contrôlée. |
| SEC-006 | Les secrets ne doivent pas être exposés dans le dépôt. | P1 | Aucun secret réel n'est versionné. |
| SEC-007 | Les actions sensibles doivent produire une entrée d'audit. | P1 | Les connexions, exports et actions d'administration sont tracés. |
| SEC-008 | Les scénarios offensifs doivent rester bornés au lab Docker. | P1 | Aucun test ne cible un réseau externe au lab. |
| SEC-009 | Les exports doivent être accessibles uniquement à des utilisateurs autorisés. | P2 | Un utilisateur non autorisé ne peut pas générer ou consulter un export. |

## 13. Données manipulées

| Donnée | Description | Source | Usage | Sensibilité |
|---|---|---|---|---|
| `users` | Comptes utilisateurs de l'application | Interface / initialisation | Authentification et contrôle d'accès | Élevée |
| `roles` | Rôles applicatifs (`admin`, `analyst`) | Configuration applicative | Autorisations | Élevée |
| `assets` | Actifs réseau observés | Découverte réseau / événements | Inventaire et analyse | Moyenne |
| `events` | Événements remontés par endpoint | `serveur-endpoint` | Détection, historique, corrélation | Moyenne |
| `network_findings` | Résultats de scan et observation réseau | Module découverte | Actifs, ports, services | Moyenne |
| `alerts` | Alertes générées par règles ou corrélations | Backend / worker | Investigation analyste | Moyenne |
| `correlation_groups` | Groupes d'événements liés | Worker de corrélation | Enrichissement des alertes | Moyenne |
| `attacker_profiles` | Profils d'IP ou sources attaquantes | Corrélation / enrichissement | Analyse et visualisation | Moyenne |
| `audit_logs` | Traces d'actions sensibles | API | Traçabilité et preuve | Élevée |
| `exports` | Fichiers ou métadonnées d'exports | Module reporting | Preuve et reporting | Moyenne |

## 14. Interfaces, API et flux

### 14.1. Flux principaux

| Flux | Source | Destination | Description |
|---|---|---|---|
| FLUX-001 | `serveur-endpoint` | `serveur-soc` | Envoi de `heartbeat` |
| FLUX-002 | `serveur-endpoint` | `serveur-soc` | Envoi d'événements et observations |
| FLUX-003 | Interface web | API FastAPI | Consultation des actifs, événements, alertes, exports |
| FLUX-004 | API FastAPI | PostgreSQL | Persistance et lecture des données |
| FLUX-005 | API FastAPI | Redis / Celery | Planification de traitements différés |
| FLUX-006 | Celery Worker | PostgreSQL | Création ou mise à jour d'alertes, corrélations et exports |

### 14.2. Endpoints indicatifs

| Endpoint indicatif | Usage | Priorité |
|---|---|---|
| `POST /auth/login` | Authentification utilisateur | P1 |
| `GET /auth/me` | Informations utilisateur courant | P1 |
| `POST /telemetry/heartbeat` | Réception d'un `heartbeat` endpoint | P1 |
| `POST /telemetry/events` | Réception d'événements endpoint | P1 |
| `GET /assets` | Liste des actifs | P1 |
| `GET /events` | Liste des événements | P1 |
| `GET /alerts` | Liste des alertes | P1 |
| `GET /correlations` | Liste des corrélations | P2 |
| `POST /exports` | Génération d'un export | P1 |
| `GET /audit-logs` | Consultation des journaux d'audit | P2 |
| `GET /health` | Santé applicative | P1 |

Ces endpoints restent indicatifs. Leur nommage définitif doit être validé pendant la conception technique et rester cohérent avec l'[architecture produit](../08_architecture/rendu_principal.md).

## 15. Architecture de démonstration retenue

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

Cette architecture compacte est retenue pour faciliter le lancement, la validation et la reproductibilité de la démonstration. Elle ne remet pas en cause la séparation logique entre interface, API, base de données, file de tâches et worker.

## 16. Scénarios de recette et critères d'acceptation

### 16.1. Critères d'acceptation globaux

Le produit sera considéré comme conforme si les points suivants sont démontrés :

1. un endpoint remonte correctement `heartbeat` et `events` ;
2. le système détecte des actifs, ports ou services ;
3. des comportements suspects sont observés depuis le `serveur-endpoint` ;
4. des alertes sont générées ;
5. au moins une logique de corrélation fonctionne ;
6. l'interface permet la consultation des données clés ;
7. l'historique et la journalisation sont visibles ;
8. un export exploitable est produit ;
9. la démonstration fonctionne dans le lab Docker prévu.

### 16.2. Scénarios de recette

| ID | Scénario | Préconditions | Étapes | Résultat attendu | Preuve attendue |
|---|---|---|---|---|---|
| REC-001 | Connexion utilisateur | Application démarrée, compte valide | Se connecter à l'interface | Accès au dashboard | Capture dashboard ou log d'audit |
| REC-002 | Heartbeat endpoint | `serveur-endpoint` démarré | Émettre un `heartbeat` | Heartbeat reçu et persisté | Ligne en base ou vue interface |
| REC-003 | Découverte réseau | Lab Docker actif | Lancer ou observer une découverte | Actif, port ou service détecté | Vue actif / résultat de scan |
| REC-004 | Détection suspecte | Scénario de test prêt | Générer un comportement contrôlé | Alerte créée | Vue alerte |
| REC-005 | Corrélation | Plusieurs événements similaires | Produire des événements répétés | Groupe de corrélation créé | Vue corrélation |
| REC-006 | Export preuve | Données présentes | Générer un export CSV ou JSON | Fichier exploitable produit | Fichier exporté |
| REC-007 | Audit | Action sensible exécutée | Connexion, export ou action admin | Entrée d'audit créée | Vue audit ou log applicatif |
| REC-008 | Démonstration complète | Trois conteneurs démarrés | Jouer la chaîne complète | Collecte -> alerte -> preuve visible | Démonstration de validation |

## 17. Priorisation

### Priorité 1 - indispensable

- authentification ;
- collecte endpoint ;
- découverte réseau minimale ;
- alertes ;
- historique ;
- audit minimal ;
- export CSV et JSON ;
- démonstration Docker.

### Priorité 2 - fortement souhaitable

- corrélation par IP et fenêtre temporelle ;
- métriques SOC ;
- consultation des journaux d'audit ;
- visualisation des IP attaquantes.

### Priorité 3 - extension si temps disponible

- export XML ;
- enrichissement géographique ;
- corrélation plus poussée ;
- raffinements visuels supplémentaires.

## 18. Matrice de traçabilité

| Besoin initial | Exigences associées | Critère de validation | Preuve attendue |
|---|---|---|---|
| Identifier les équipements réseau | F-DISC-001, F-DISC-002, F-ASSET-001 | Actifs visibles dans l'interface | Vue actifs / base PostgreSQL |
| Observer le trafic et les événements | F-TEL-002, F-TEL-003, F-TEL-004 | Événements persistés et consultables | Vue événements |
| Détecter des comportements suspects | F-ALERT-001, F-ALERT-002, F-ALERT-003 | Alerte générée à partir d'un scénario | Vue alerte |
| Comprendre les répétitions | F-COR-001, F-COR-002, F-COR-004 | Corrélation visible | Vue corrélation |
| Produire des preuves | F-EXP-001, F-EXP-002, F-AUD-002 | Export généré et action journalisée | Fichier CSV/JSON + audit log |
| Sécuriser l'accès | F-AUTH-001, F-AUTH-002, SEC-001, SEC-002 | Accès contrôlé par authentification et `role` | Test connexion / refus d'accès |
| Démontrer le produit | NF-DEP-001, REC-008 | Lab Docker fonctionnel | Démonstration de validation |

## 19. Livrables attendus

| Livrable | Description | Critère de validation |
|---|---|---|
| Application DevinciWatch MVP | Application web de supervision cyber | Chaîne fonctionnelle démontrable |
| Lab Docker | Environnement `serveur-soc`, `serveur-endpoint`, `serveur-attacker` | Démarrage reproductible |
| Documentation technique | Instructions et architecture | Cohérence avec les documents `07` et `08` |
| Exports de preuve | Fichiers CSV ou JSON | Exploitables en revue produit |
| Support de présentation | Support de présentation produit | Clair, structuré, défendable |
| Dépôt GitHub | Code, documentation et historique | Dépôt propre et traçable |

## 20. Références de cadrage

- [Kick-off projet (01)](../01_documents_pedagogiques/kickoff/KICKOFF.md)
- [Étude de marché (02)](../02_etude_de_marche/rendu_principal.md)
- [Business model (03)](../03_business_model/rendu_principal.md)
- [Business plan (04)](../04_business_plan/rendu_principal.md)
- [Feuille de cadrage (05)](../05_feuille_de_cadrage/rendu_principal.md)
- [Gestion de projet (06)](../06_gestion_de_projet/rendu_principal.md)
- [Architecture produit (08)](../08_architecture/rendu_principal.md)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## 21. Conclusion

Ce cahier des charges fixe un périmètre clair, vérifiable et cohérent avec le positionnement produit, la gestion de projet et l'architecture retenue. Il constitue la base opérationnelle du développement de DevinciWatch.

La version consolidée renforce la dimension professionnelle du document en introduisant des exigences numérotées, des critères d'acceptation, une matrice de traçabilité, des scénarios de recette et des exigences de sécurité adaptées au contexte cyber. Elle permet ainsi de relier explicitement le besoin initial, la conception technique, la démonstration et les preuves attendues en validation produit.
