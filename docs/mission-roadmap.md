# Mission 1 – Résumé et plan d’action synthétique

## 1. Résumé de ce qui doit être fait

Dans ce projet, il s’agit de **concevoir et implémenter une infrastructure de données hybride** combinant :

- un moteur de calcul distribué (**Spark**) pour l’ETL de données volumineuses,
- un moteur de streaming (**Redpanda**) pour les flux temps réel,
- une intégration **on-premise ↔ cloud** (architecture hybride).

Les objectifs pédagogiques globaux sont de :

- **Modéliser une architecture de données hybride** et sélectionner les composants cloud adaptés.
- **Représenter visuellement** l’infrastructure (schémas d’architecture et flux de données).
- **Extraire, transformer et charger** des données (pipelines ETL batch et temps réel).
- **Mettre en œuvre un pipeline temps réel** avec Redpanda et PySpark.
- **Évaluer la compatibilité** des composants avec le SI existant (on-premise / cloud).
- **Documenter** le travail (diagrammes, justification des choix, autoévaluation, etc.).

Les livrables finaux incluront notamment :

- Une **sélection argumentée de composants cloud** pour une architecture hybride.
- Un **schéma d’architecture** illustrant les flux de données entre le SI on-premise et le cloud.
- Un **pipeline ETL opérationnel** utilisant Spark et Redpanda (POC).
- Une **documentation structurée** (diagrammes, explications techniques, éventuellement vidéo démo, fiche d’autoévaluation).

Deux exercices structurent la mise en pratique :

1. **Exercice 1** : modélisation d’une **infrastructure hybride dans le cloud** (côté architecture, choix de services, interopérabilité, sécurité, etc.).
2. **Exercice 2** : mise en œuvre d’un **cas d’usage temps réel** (gestion de tickets clients) avec **Redpanda + PySpark**, incluant la conteneurisation (Docker / Docker Compose) et l’export / stockage des résultats dans le cloud.

## 2. Plan d’action succinct (Mission 1)

### Étape 1 – Prise en main du contexte et des exigences

- Relire en détail les documents :
  - `Mission.pdf` (vision globale, objectifs).
  - `Exercice1.pdf` (modélisation d’infrastructure hybride).
  - `Exercice2.pdf` (pipeline temps réel Redpanda + PySpark).
  - `Livrables.pdf` (liste précise des sorties attendues et critères de validation).
- Noter les **contraintes SI** (on-premise, sécurité, volumétrie, SLA) et les **exigences métier**.

### Étape 2 – Définition du périmètre technique

- Choisir l’**environnement de travail** (Linux Debian + VSCode, Docker).
- Lister les **technologies cibles** et versions (Spark, Redpanda, Docker/Compose, éventuellement AWS ou autre cloud).
- Identifier les **sources de données** (on-premise, fichiers, flux simulés) et les **cibles de stockage** (objet, data warehouse, etc.).

### Étape 3 – Préparation de l’Exercice 1 (architecture hybride)

- Définir une **proposition d’architecture cible** :
  - Composants on-premise (bases, AD, stockage).
  - Composants cloud (stockage objet, data warehouse, services réseau, sécurité).
  - Couche streaming (Redpanda), couche traitement batch/streaming (Spark).
- Produire un **premier draft de schéma d’architecture** (outil au choix, mais documentable en Markdown).
- Commencer à **argumenter les choix techniques** (scalabilité, coûts, sécurité, compatibilité SI).

### Étape 4 – Préparation de l’Exercice 2 (pipeline Redpanda + PySpark)

- Concevoir le **flux fonctionnel** du cas d’usage “tickets clients” :
  - Production de tickets (générateur d’événements).
  - Ingestion dans Redpanda (topics).
  - Traitement avec PySpark (transformations, agrégations, enrichissement).
  - Export / écriture vers un stockage cible.
- Définir la **stratégie de conteneurisation** :
  - Dockerfile pour l’application PySpark.
  - Docker Compose pour orchestrer Redpanda + Spark + éventuels services annexes.
- Préparer l’**organisation du repo** (chemins relatifs, modules Python, scripts de déploiement).

### Étape 5 – Planification des livrables

- Construire une **check-list des livrables** à partir de `Livrables.pdf` (schémas, code, diagrammes Mermaid, vidéo éventuelle, autoévaluation).
- Définir un **ordre de réalisation** :
  1. Architecture logique (Exercice 1) → schémas + choix composants.
  2. POC pipeline temps réel (Exercice 2) → code + conteneurisation.
  3. Documentation finale (Markdown, diagrammes Mermaid, autoévaluation, préparation bilan mentor).

