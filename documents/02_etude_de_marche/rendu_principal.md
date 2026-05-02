# Étude de marché - DevinciWatch

## 1. Objet du document

La présente étude de marché a pour objectif de démontrer la pertinence économique et stratégique de DevinciWatch, solution de supervision et d'analyse cyber réseau orientée usage. Elle s'inscrit dans le cadre du projet pédagogique défini par le kick-off et par le syllabus, qui demandent explicitement une étude de marché, un modèle économique et une stratégie d'entrée sur le marché.

Cette étude répond à quatre questions structurantes :

1. Le besoin adressé est-il réel, durable et suffisamment prioritaire pour des organisations clientes ?
2. Quels segments présentent le meilleur équilibre entre besoin, accessibilité commerciale et capacité de paiement ?
3. Comment positionner la solution face aux alternatives existantes ?
4. Quelle trajectoire d'entrée sur le marché paraît la plus crédible à court et moyen terme ?

## 2. Rappel du besoin initial

Le projet DevinciWatch vise à concevoir un outil de supervision et d'analyse réseau capable de :

- détecter les équipements connectés ;
- scanner des plages d'adresses IP ;
- identifier les ports ouverts ;
- récupérer des informations sur les services réseau ;
- observer le trafic ;
- détecter des comportements suspects ou malveillants ;
- générer des alertes ;
- produire des exports exploitables, notamment en JSON et CSV.

L'enjeu n'est donc pas seulement technique. Il s'agit de transformer ce socle fonctionnel en offre lisible, utile et défendable sur un marché où les clients attendent à la fois de la détection, de la réactivité et de la traçabilité.

## 3. Hypothèse centrale de marché

L'hypothèse retenue est la suivante : il existe une place de marché pour une solution de supervision cyber réseau plus simple à déployer et à exploiter que les stacks SIEM/XDR lourdes, tout en étant plus industrialisée et plus orientée résultat qu'un assemblage open source maintenu en interne.

Cette hypothèse repose sur trois constats convergents :

- la pression cyber reste élevée dans les pays cibles ;
- la pression réglementaire pousse à mieux détecter, tracer et démontrer ;
- la pénurie de compétences cyber favorise les offres qui réduisent la complexité opérationnelle.

## 4. Analyse du contexte et de la demande

### 4.1. Une menace durable et documentée

Les données collectées dans les annexes montrent une intensité élevée et persistante de la menace cyber sur le périmètre prioritaire France, Belgique et Suisse francophone.

En France, l'ANSSI a traité 3 586 événements de sécurité en 2025, dont 2 209 signalements et 1 366 incidents [S01]. Sur le même marché, Cybermalveillance.gouv.fr a accompagné plus de 500 000 victimes, avec une progression de 107 % des violations de données et de 70 % du phishing [S02].

En Belgique, le Centre for Cybersecurity Belgium fait état de 556 notifications de cyberattaques, 635 notifications NIS2, 105 cas de ransomware et 63 attaques DDoS sur l'année 2025 [S21]. Les incidents signalés progressent de 70 % et les incidents cyber de 58 % [S22].

En Suisse, les rapports semestriels du NCSC recensent 35 727 signalements sur le premier semestre, dont 58 % liés à la fraude, puis 29 006 signalements volontaires sur la période suivante [S23][S24].

### 4.2. Une pression réglementaire qui transforme le besoin en priorité

La directive NIS2 étend les obligations de gestion du risque et de notification à 18 secteurs critiques [S05]. Cette évolution ne crée pas seulement une contrainte documentaire ; elle renforce le besoin d'outils capables de fournir des éléments probants : journaux exploitables, alertes structurées, visibilité opérationnelle et reporting.

Dans cette logique, une solution comme DevinciWatch doit être pensée non seulement comme un outil de surveillance, mais comme un outil d'exécution et de preuve.

### 4.3. Une difficulté structurelle de recrutement et d'exploitation

L'ENISA souligne que 76 % des organisations font face à des difficultés de recrutement sur les profils cyber et 71 % à des difficultés de rétention [S13]. Cette tension a une conséquence directe : la valeur d'une solution n'est pas seulement fonction de sa couverture technique, mais de sa capacité à être réellement opérée par une équipe réduite.

De plus, Mandiant relève un dwell time médian mondial de 11 jours, avec une forte présence des exploits comme vecteur initial (33 %) et des identifiants compromis (16 %) [S04]. Ces données renforcent l'intérêt d'une solution capable d'accélérer la détection et la qualification opérationnelle.

## 5. Périmètre de marché retenu

### 5.1. Périmètre géographique

Le périmètre prioritaire retenu est constitué de la France, de la Belgique et de la Suisse francophone. Ce choix est justifié par :

- la disponibilité de sources publiques solides et récentes ;
- une proximité réglementaire et linguistique favorable au démarrage ;
- un tissu d'organisations exposées aux mêmes enjeux de cybersécurité, de conformité et de manque de compétences.

### 5.2. Segments visés

Trois segments ont été retenus :

1. les PME de 50 à 249 employés ;
2. les ETI de 250 à 1 000 employés ;
3. les organisations sensibles, notamment dans la santé, l'éducation, le secteur public local et les services numériques.

Ces segments présentent un point commun décisif : ils ont souvent besoin d'une meilleure supervision, mais ne disposent pas toujours des ressources pour opérer une plateforme lourde ou un SOC avancé.

## 6. Segmentation, ciblage et positionnement

### 6.1. Critères de ciblage

Le ciblage a été construit à partir de quatre critères :

- niveau d'exposition cyber ;
- intensité de la contrainte de conformité ;
- insuffisance ou absence de capacité SOC interne ;
- capacité à absorber un abonnement annuel B2B.

### 6.2. Cibles prioritaires

Les cibles prioritaires sont les organisations qui cumulent les caractéristiques suivantes :

- infrastructure réseau suffisamment structurée pour que la supervision crée de la valeur ;
- besoin de visibilité et de reporting ;
- capacité de décision relativement courte ;
- maturité suffisante pour industrialiser un usage, mais insuffisante pour déployer un SIEM enterprise complet.

### 6.3. Positionnement recommandé

Le positionnement recommandé est le suivant :

> DevinciWatch est une solution de supervision cyber réseau pragmatique, conçue pour des équipes réduites, qui fournit des alertes actionnables, une visibilité exploitable et des preuves exportables sans la complexité d'une plateforme SIEM enterprise.

Ce positionnement repose sur quatre piliers de valeur :

- simplicité de mise en œuvre ;
- réduction du temps de détection et de qualification ;
- lisibilité économique ;
- capacité native à produire de la preuve.

## 7. Analyse concurrentielle

### 7.1. SIEM et XDR cloud enterprise

Les solutions de type Datadog, Splunk, Microsoft Sentinel ou Elastic Security bénéficient d'une couverture fonctionnelle large et d'un écosystème mature. En revanche, elles présentent souvent, pour la cible PME/ETI, trois limites majeures :

- un coût parfois difficile à anticiper ;
- une dépendance à des compétences de paramétrage et d'exploitation ;
- une charge de conduite du changement non négligeable.

Les données de benchmark montrent par exemple des modèles tarifaires liés au volume d'événements ou au nombre d'hôtes, ce qui peut accroître l'imprévisibilité budgétaire [S09][S10].

### 7.2. Stacks open source de type SOC

Les approches construites autour de Wazuh, Suricata, Zeek, ELK ou Security Onion offrent une grande souplesse et un coût de licence faible. Elles restent toutefois plus exigeantes à industrialiser et à maintenir. Le coût visible est bas, mais le coût caché d'exploitation peut être élevé.

Le benchmark conservé en annexe confirme cet arbitrage. Le prix catalogue Wazuh Cloud à 100 agents, 250 agents et 500 agents donne un repère utile, mais ne suffit pas à refléter le coût total d'usage [S08].

### 7.3. MSSP et SOC externalisés

Les MSSP répondent bien au besoin d'externalisation de la compétence, mais ils peuvent réduire le contrôle direct, allonger certains temps de boucle et augmenter le coût récurrent selon le niveau d'accompagnement attendu.

### 7.4. Espace de différenciation de DevinciWatch

L'espace de différenciation défendable n'est pas la guerre de fonctionnalités. Il réside dans la combinaison suivante :

- déploiement plus rapide ;
- coût plus lisible ;
- gouvernance plus simple ;
- production native d'alertes et d'exports exploitables.

La proposition de valeur doit donc rester centrée sur le résultat opérationnel et sur la preuve, pas sur l'accumulation fonctionnelle.

## 8. Modélisation TAM / SAM / SOM

Le modèle retenu en annexe s'appuie sur une approche bottom-up :

`SOM_segment = N_org × t_need × t_fit × t_access × ACV`

Cette approche est plus pertinente qu'une estimation purement macro, car elle introduit des variables de réalisme commercial : besoin, compatibilité, accès au segment et valeur annuelle moyenne du contrat.

Les hypothèses principales sont les suivantes :

- horizon de pénétration : 24 à 36 mois ;
- ACV de travail : de 9 000 à 24 000 EUR par an selon le segment ;
- forte sensibilité à l'accès commercial, au prix moyen et au churn.

Cette modélisation ne constitue pas une prévision automatique ; elle sert à hiérarchiser les segments et à structurer les décisions de go-to-market.

## 9. Stratégie d'entrée sur le marché

Trois options ont été analysées :

1. vente directe ;
2. distribution par partenaires de type MSSP ou intégrateurs ;
3. modèle hybride.

L'analyse comparative conservée en annexe conduit à recommander un modèle hybride. Celui-ci permet :

- de garder un canal direct pour apprendre vite ;
- d'accélérer la diffusion grâce à des partenaires sélectionnés ;
- de réduire le risque de dépendance à un canal unique.

La stratégie recommandée consiste à sécuriser un minimum de pipeline direct tout en structurant 2 à 3 partenariats ciblés.

## 10. Risques de marché identifiés

Les principaux risques de marché sont les suivants :

- une conversion POC vers production inférieure aux hypothèses ;
- un coût d'acquisition trop élevé sur certaines verticales ;
- un positionnement insuffisamment différencié ;
- une valeur perçue diluée si le produit devient trop large trop tôt.

Ces risques appellent une exécution disciplinée : qualification stricte, cadrage du POC, pilotage des KPI et clarté du message commercial.

## 11. Conclusion générale

L'étude de marché valide l'existence d'une opportunité crédible pour DevinciWatch. Le marché n'est pas en manque d'outils ; il est en manque de solutions réellement exploitables, économiquement lisibles et capables de transformer la conformité et la surveillance en action opérationnelle.

La priorité n'est donc pas de rivaliser frontalement avec les plateformes les plus complètes du marché. Elle est de proposer une solution claire, utile et démontrable pour des organisations qui doivent améliorer leur supervision sans complexifier davantage leur exploitation.

## 12. Références mobilisées

### Références externes

- [S01] ANSSI, Panorama de la cybermenace 2025.
- [S02] Cybermalveillance.gouv.fr, Rapport d'activité 2025.
- [S04] Google Cloud / Mandiant, M-Trends 2025.
- [S05] Commission européenne, Directive NIS2.
- [S08] Wazuh Cloud Pricing.
- [S09] Datadog Cloud SIEM Pricing.
- [S10] Datadog Workload Protection Pricing.
- [S13] ENISA, NIS Investments 2025 - communication et données associées.
- [S21] Centre for Cybersecurity Belgium, chiffres clés 2025.
- [S22] Centre for Cybersecurity Belgium, réalité cyber 2025.
- [S23] NCSC Suisse, rapport semestriel 2025/1.
- [S24] NCSC Suisse, rapport semestriel 2025/2.

### Références internes et annexes d'étude

- `references/01_cadrage_reference.md`
- `references/02_analyse_demande_et_contexte.md`
- `references/03_segmentation_ciblage_positionnement.md`
- `references/04_benchmark_concurrence.md`
- `references/05_modele_tam_sam_som.md`
- `references/06_strategie_entree_marche.md`
- `references/07_risques_kpi_et_preuves.md`
- `references/08_sources_reference.md`
- `README.md`

### Registre complet des sources antérieures conservées

- `../90_references_transverses/source_register.csv`
- `../90_references_transverses/source_quality_matrix.csv`

Le registre complet conserve l'ensemble des références exploitées antérieurement dans l'étude consolidée, notamment les sources institutionnelles et sectorielles S01 à S26. Il constitue la base de traçabilité détaillée des chiffres et constats mobilisés dans le présent document.

## 13. Annexes chiffrées

- `../90_references_transverses/source_register.csv`
- `../90_references_transverses/source_quality_matrix.csv`
- `annexes/tam_sam_som_bottomup_v2.csv`
- `annexes/competition_benchmark_v2.csv`
- `annexes/gtm_comparison_matrix.csv`
- `annexes/kpi_template_business_model.csv`
- `annexes/sensitivity_model_template.csv`
