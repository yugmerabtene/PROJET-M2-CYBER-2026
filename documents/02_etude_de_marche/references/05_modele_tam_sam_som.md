# 05 - Modèle TAM/SAM/SOM (bottom-up)

## Formule de travail

Par segment :

`SOM_segment = N_org × t_need × t_fit × t_access × ACV`

Avec :

- `N_org` : nombre d'organisations
- `t_need` : part avec besoin cyber réseau prioritaire
- `t_fit` : part techniquement/organisationnellement compatible
- `t_access` : part atteignable commercialement à 24-36 mois
- `ACV` : valeur annuelle moyenne contrat

Cette approche bottom-up est préférée à une estimation purement macroéconomique, car elle oblige à expliciter les hypothèses de conversion, d'accès commercial et de valeur annuelle moyenne.

## Hypothèses retenues

- Besoin valide par signaux FR/BE/CH.
- Pression compliance durable (NIS2).
- Tension talents cyber persistante.
- Bande ACV de travail : 9k à 24k EUR/an selon segment.

## Lecture décisionnelle

- Le résultat est surtout sensible à `t_access`, `ACV` et churn.
- Le modèle est utile pour prioriser les segments avant accélération commerciale.

Le modèle doit être lu comme un outil d'aide à la décision et non comme une prévision certaine. Sa valeur réside dans la comparaison des segments, l'identification des variables sensibles et la préparation du [business model](../../03_business_model/rendu_principal.md).

## Usage attendu

- Alimenter le futur business model avec hypothèses tracées.
- Mettre à jour les coefficients après retours POC/relation terrain.

Les annexes chiffrées associées sont conservées dans le dossier [annexes de l'étude](../annexes/).
