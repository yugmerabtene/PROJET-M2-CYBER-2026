# Architecture definitive - DevinciWatch

## 1. Statut du document

Ce document fixe l'architecture de reference du produit DevinciWatch.

Sauf decision explicite ulterieure, cette architecture est consideree comme l'architecture definitive de depart pour le redeveloppement de l'application.

Le document distingue volontairement deux niveaux :

- l'architecture produit cible ;
- l'architecture de demonstration Docker retenue pour le MVP et la soutenance.

## 2. Objectif

Ce document définit l'architecture cible du produit DevinciWatch.

L'objectif est de concevoir une application de cybersurveillance réseau orientée SOC, capable de :

- recevoir de la télémétrie depuis un agent ;
- persister des événements et un inventaire d'actifs ;
- détecter des comportements suspects ;
- générer des alertes actionnables ;
- exposer une interface web d'analyse ;
- produire des exports et des éléments de preuve.

L'architecture doit rester :

- propre ;
- défendable en soutenance ;
- réaliste pour un MVP ;
- extensible pour les itérations suivantes.

## 3. Stack cible

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic

### Base de données

- PostgreSQL

### Traitements asynchrones

- Redis
- Celery

### Frontend

- frontend web integre au meme conteneur que le backend pour le MVP
- interface web servie par le serveur SOC

### Conteneurisation et démo

- Docker Compose
- topologie de demonstration en 3 conteneurs

### Topologie Docker retenue

- un conteneur `serveur-soc`
- un conteneur `serveur-endpoint`
- un conteneur `serveur-attacker`

## 4. Principes d'architecture

Les principes retenus sont les suivants :

- séparation claire entre collecte, traitement, stockage et présentation ;
- organisation par domaines fonctionnels ;
- logique métier centralisée côté backend ;
- traitements lourds ou différés sortis du chemin synchrone ;
- traçabilité native des actions sensibles ;
- structure adaptée à une démonstration rapide, mais suffisamment propre pour évoluer ;
- environnement de test reproductible via conteneurs séparés ;
- simulation contrôlée de comportements suspects sans embarquer de code destructeur réel.

## 5. Architecture logicielle

![Architecture logicielle](architecture-software.svg)

```text
[Endpoint Agent] -- heartbeat / events --> [Control Server]
[Web App] -------- REST / JWT --------> [Control Server]
[Control Server] - logique interne ---> [FastAPI API]
[Control Server] - logique interne ---> [PostgreSQL]
[Control Server] - logique interne ---> [Redis]
[Control Server] - logique interne ---> [Celery Worker]
[Celery Worker] ----------------------> [PostgreSQL]
```

## 6. Lecture de l'architecture logicielle

- l'utilisateur accede uniquement a l'application web ;
- l'application web est hebergee dans le meme conteneur que l'API pour le MVP ;
- le serveur-endpoint envoie ses donnees uniquement au serveur-soc ;
- le serveur-attacker ne parle pas directement a l'interface ;
- PostgreSQL, Redis et Celery restent logiquement separes, mais sont embarques dans le serveur-soc pour la demonstration ;
- la logique produit reste separee par composants, meme si l'emballage Docker de demo est compact.

## 7. Architecture reseau Docker

![Architecture reseau Docker](architecture-docker-network.svg)

L'environnement de developpement et de demonstration est retenu sous la forme de trois conteneurs :

1. un conteneur `serveur-soc` ;
2. un conteneur `serveur-endpoint` ;
3. un conteneur `serveur-attacker`.

Le conteneur `serveur-soc` centralise l'application web, l'API FastAPI, PostgreSQL, Redis et le worker Celery pour simplifier le MVP et la soutenance.

```text
DOCKER HOST
  reseau interne : devinciwatch_net

  [Poste analyste]
         |
         | HTTP / HTTPS
         v
  [serveur-soc]
         |
         +--> Frontend Web
         +--> FastAPI API
         +--> PostgreSQL
         +--> Redis
         +--> Celery Worker

  [serveur-endpoint] -------------> [serveur-soc]
         ^
         |
         | trafic reseau, logs, comportements suspects
         |
  [serveur-attacker]

  [serveur-attacker] -- trafic controle --> [serveur-endpoint]
```

### Roles des conteneurs de test

#### `serveur-soc`

Responsabilites :

- exposer l'application ;
- servir l'API ;
- servir le frontend de demonstration ;
- centraliser les appels fonctionnels ;
- embarquer PostgreSQL, Redis et Celery pour la demonstration.

Composants internes embarques :

- FastAPI API ;
- Frontend Web ;
- PostgreSQL ;
- Redis ;
- Celery Worker ;

#### `serveur-endpoint`

Responsabilites :

- jouer le role d'un hote supervise ;
- observer le trafic reseau sur l'interface du conteneur ;
- collecter et parser les fichiers log utiles ;
- relever les comportements suspects locaux ;
- remonter `heartbeat` et `events` vers `serveur-soc`.

#### `serveur-attacker`

Responsabilites :

- produire des scenarios de test ;
- simuler des comportements suspects controles ;
- generer du trafic ou des comportements attendus pour la detection sur le serveur-endpoint.

Contraintes :

- pas de charge destructive reelle ;
- pas de code malware reel ;
- scenarios strictement previsibles et demonstrables.

## 8. Diagramme de sequence principal

![Diagramme de sequence](architecture-sequence.svg)

```text
1. Agent -> Control Server : POST /telemetry/heartbeat
2. Control Server -> PostgreSQL : persistence du heartbeat

3. Agent -> Control Server : POST /telemetry/events
4. Control Server -> PostgreSQL : persistence des evenements
5. Control Server -> Redis : mise en file d'une tache de detection
6. Redis -> Celery Worker : dispatch de la tache
7. Celery Worker -> PostgreSQL : mise a jour assets / evaluation des regles / creation des alertes

8. Web App -> Control Server : consultation assets / alerts / events / reports
9. Control Server -> PostgreSQL : lecture des donnees
10. Control Server -> Web App : reponse
```

## 9. Composants principaux

### 9.1 Agent de collecte

Rôle :

- collecter des `heartbeat` ;
- observer le trafic reseau ;
- analyser des fichiers log ;
- relever des comportements suspects ;
- pousser les donnees vers l'API.

Contraintes :

- simple ;
- robuste ;
- peu couplé au reste du système.

### 9.2 API Backend FastAPI

Rôle :

- authentifier les utilisateurs ;
- recevoir les données agent ;
- exposer les endpoints métiers ;
- valider et normaliser les payloads ;
- piloter les règles métier ;
- retourner les données au frontend.

L'API constitue le point central du systeme et sera hebergee dans le conteneur `serveur-soc`.

### 9.3 Base PostgreSQL

Rôle :

- stocker les utilisateurs ;
- stocker les actifs ;
- stocker les événements ;
- stocker les alertes ;
- stocker les journaux d'audit ;
- stocker les informations utiles aux exports et rapports.

PostgreSQL est la source de verite fonctionnelle et sera embarquee dans `serveur-soc` pour la phase MVP de demonstration.

### 9.4 Redis + Worker Celery

Rôle :

- sortir du chemin synchrone les traitements non immédiats ;
- exécuter les règles de détection ;
- recalculer certains indicateurs ;
- générer des exports ;
- préparer certains rapports ou tâches différées.

Redis et Celery seront egalement embarques dans `serveur-soc` pour la phase MVP de demonstration.

### 9.5 Frontend web

Rôle :

- authentification ;
- visualisation du dashboard ;
- consultation des actifs ;
- consultation des événements ;
- consultation et traitement des alertes ;
- déclenchement d'exports.

Le frontend est integre au meme conteneur que le backend pour le MVP et ne doit parler qu'a l'API locale du serveur-soc.

### 9.6 Simulateur de test

Rôle :

- executer des scenarios de test de securite controles ;
- alimenter l'agent ou le serveur en comportements observables ;
- produire des preuves de detection pour la demonstration.

Ce composant existe pour le lab Docker de test, pas pour la production. Il sera heberge dans le conteneur `serveur-attacker`.

## 10. Capacites fonctionnelles reseau imposees par le projet

L'architecture doit couvrir explicitement les capacites demandees dans le kick-off :

- detection des equipements connectes ;
- scan de plage IP ;
- identification des ports ouverts ;
- recuperation d'informations sur les services reseau ;
- observation du trafic reseau ;
- detection de comportements suspects ou malveillants.

Ces capacites seront portees principalement par le serveur-endpoint et par les modules backend associes a la telemetry, aux assets et aux alerts.

## 11. Découpage fonctionnel du backend

Le backend doit être organisé par domaines métier.

Modules recommandés :

- `auth`
- `telemetry`
- `discovery`
- `assets`
- `alerts`
- `reports`
- `audit`
- `core`

### `auth`

Responsabilités :

- login ;
- génération et validation des tokens ;
- endpoint `/me` ;
- gestion des rôles.

### `telemetry`

Responsabilités :

- réception de `heartbeat` ;
- réception d'événements ;
- validation des payloads ;
- normalisation minimale avant persistance.

### `discovery`

Responsabilités :

- scan de plages IP ;
- identification des ports ouverts ;
- recuperation d'informations de services reseau ;
- collecte d'observations liees au trafic reseau ;
- transmission de ces resultats au module `assets` et au module `alerts`.

### `assets`

Responsabilités :

- création et mise à jour de l'inventaire ;
- enrichissement de base des actifs ;
- consultation des actifs par l'interface.

### `alerts`

Responsabilités :

- création d'alertes depuis les règles ;
- consultation ;
- détail ;
- traitement analyste ;
- cycle de vie des statuts.

### `reports`

Responsabilités :

- synthèse de KPI ;
- exports CSV ;
- vue exploitable pour la démonstration et la preuve.

### `audit`

Responsabilités :

- journalisation des actions sensibles ;
- conservation des traces ;
- consultation restreinte.

### `core`

Responsabilités :

- configuration ;
- sécurité transverse ;
- dépendances communes ;
- utilitaires partagés.

## 12. Structure logique FastAPI recommandée

Structure cible :

```text
app/
  main.py
  core/
  auth/
  telemetry/
  discovery/
  assets/
  alerts/
  reports/
  audit/
```

Chaque module devrait à terme contenir :

- routes FastAPI ;
- schémas Pydantic ;
- services métier ;
- accès aux données ;
- tests associés.

## 13. Flux de test en environnement Docker

Scenario de demonstration recommande :

1. `serveur-soc`, `serveur-endpoint` et `serveur-attacker` demarrent ;
2. `serveur-endpoint` s'enregistre et emet un `heartbeat` ;
3. `serveur-endpoint` execute ou planifie une phase de decouverte reseau initiale : scan IP, ports ouverts et services observes ;
4. `serveur-attacker` declenche un scenario controle ;
5. `serveur-endpoint` observe le trafic, les logs ou les comportements attendus ;
6. l'API persiste les evenements et les resultats de decouverte ;
7. le worker evalue les regles ;
8. une ou plusieurs alertes sont generees ;
9. l'analyste visualise le resultat dans l'interface ;
10. un export ou un audit peut etre produit pour preuve.

## 14. Modèle de données fonctionnel

Entités principales à prévoir :

- `users`
- `roles`
- `assets`
- `events`
- `network_findings`
- `alerts`
- `audit_logs`
- `exports`

Relations principales :

- un événement peut être lié à un actif ;
- un resultat de scan ou d'observation reseau peut etre lie a un actif ;
- une alerte peut être liée à un actif et à un ou plusieurs événements ;
- une action utilisateur sensible doit produire une entrée d'audit.

## 15. Exigences non fonctionnelles

### Sécurité

- authentification obligatoire côté interface ;
- séparation des rôles `admin` / `analyst` ;
- protection des actions sensibles ;
- journalisation des opérations critiques.

### Qualité

- structure modulaire ;
- validation stricte des données d'entrée ;
- logique métier testable ;
- conventions homogènes.

### Observabilité

- endpoint de santé ;
- logs applicatifs structurés ;
- indicateurs simples pour la démonstration.

### Déploiement

- environnement local reproductible ;
- séparation nette entre configuration et code ;
- capacité à démontrer l'application en conditions réalistes ;
- possibilité de lancer un lab Docker complet avec serveur-soc, serveur-endpoint et serveur-attacker.

### Isolation du lab de test

- reseau Docker dedie ;
- aucun acces inutile hors du reseau de lab ;
- scenarios de test bornes et documentes.

## 16. MVP recommandé

Le premier incrément produit devrait couvrir :

1. authentification ;
2. ingestion `heartbeat` ;
3. ingestion `events` ;
4. collecte de trafic, logs et signaux suspects cote endpoint ;
5. scan IP et identification basique de ports/services ;
6. persistance PostgreSQL ;
7. inventaire d'actifs simple ;
8. règles de détection minimales ;
9. liste et détail d'alertes ;
10. export CSV ;
11. audit minimal ;
12. lab Docker de demonstration en 3 conteneurs.

## 17. Architecture Docker retenue pour la demonstration

Architecture retenue de demonstration :

- `serveur-soc`
- `serveur-endpoint`
- `serveur-attacker`

Cette architecture est retenue comme architecture de test officielle du projet pour les phases de developpement, de demonstration et de validation fonctionnelle.

## 18. Pourquoi cette architecture est adaptée au sujet

Cette architecture est adaptée parce qu'elle :

- correspond directement aux attendus du kick-off ;
- est cohérente avec une implémentation Python/FastAPI ;
- sépare correctement les responsabilités ;
- permet une démonstration claire en soutenance ;
- reste assez simple pour un projet académique ;
- prepare une montée en qualité sans complexité excessive ;
- permet un environnement de test réaliste et reproductible ;
- couvre explicitement les besoins de scan, ports, services, trafic et detection ;
- rend visible toute la chaine detection -> alerte -> preuve.

## 19. Conclusion

L'architecture definitive retenue pour DevinciWatch est une architecture web modulaire centree sur FastAPI, PostgreSQL, Redis et un worker asynchrone, avec un environnement Docker de test compose de trois conteneurs : `serveur-soc`, `serveur-endpoint` et `serveur-attacker`.

Elle est adaptee au sujet, defendable techniquement, exploitable pedagogiquement et suffisamment propre pour servir de base definitive au redeveloppement du produit.
