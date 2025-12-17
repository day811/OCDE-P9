# Exercice 1 – Détail des étapes 2 et 3 : choix à évaluer

Basé sur ma lecture de l'Exercice 1, voici une analyse structurée des décisions architecturales qui restent à prendre.

## Vue d'ensemble des étapes 2 et 3

L'Exercice 1 se décompose en trois étapes :

1. **Étape 1 (complétée)** : Identification des composants cloud – tu as déjà compris la direction.
2. **Étape 2** : Représentation visuelle de l'infrastructure (schéma avec Draw.io ou Lucidchart).
3. **Étape 3** : Évaluation de la compatibilité (document 400–1200 mots sur sécurité, interopérabilité, scalabilité, coûts).

## Étape 2 – Représentation visuelle de l'infrastructure hybride

### Éléments PRESCRITS et NON NÉGOCIABLES

L'exercice mandate explicitement :

- **Redpanda** comme plateforme de streaming (non négociable).
- **AWS** comme provider cloud (mentionné dans le contexte : *« en particulier avec les services AWS »*).
- **Stockage d'objets** pour données non structurées.
- **Data warehouse cloud** pour centraliser l'analytique.
- **Extension d'Active Directory** au cloud pour gestion unifiée des identités.
- **Flux de données temps réel et batch** avec indications de protocoles.
- **Points de synchronisation** entre on-premise et cloud.
- **Sécurisation SSL/TLS** des transferts.

### Choix à DÉCIDER : les variables architecturales

| Composant | Options considérées | Critères de choix |
|-----------|-------------------|------------------|
| **Stockage d'objets** | AWS S3 vs MinIO vs alternatives | Scalabilité, coûts, intégration AWS, sécurité |
| **Data warehouse** | Redshift vs Snowflake vs BigQuery vs Athena | Compatibilité SQL Server, coûts, performances, capacité |
| **Extension AD** | AWS Directory Service vs Azure AD vs alternatives | Coût, intégration AD existant, gestion des permissions |
| **Connectivité réseau** | VPC + S2S VPN vs AWS Direct Connect vs BGP | Latence, sécurité, débit, coûts (Direct Connect = plus cher) |
| **Ingestion des données** | AWS Glue vs DMS (Database Migration Service) vs scripts custom | Effort de mise en œuvre, automatisation, coûts |
| **Surveillance des coûts** | AWS Cost Explorer vs CloudWatch vs Budget Alerts | Granularité du suivi, alertes |

### Structure du schéma visuel attendu

Ton schéma doit montrer :

**Côté on-premise (datacenter InduTechData)** :
- Cluster SQL Server (40 To)
- Baie SAN (10 To)
- Serveur Active Directory
- ERP et CRM
- Indicateurs des données générées (flux IoT 50 Go/mois, logs, fichiers)

**Côté cloud AWS** :
- VPC avec subnets publics/privés
- S3 bucket(s) pour données brutes/non structurées
- Data warehouse (Redshift ou Snowflake)
- Redpanda (cluster pour streaming)
- AWS Directory Service (extension AD)

**Connexions et flux** :
- Lien sécurisé on-premise → cloud (VPN ou Direct Connect)
- Flux temps réel : IoT → Redpanda → transformation → S3 / Data warehouse
- Flux batch : SQL Server → (AWS DMS ou Glue) → Data warehouse
- Synchronisation AD : AD on-premise ↔ AWS Directory Service (bidirectionnel)
- Protocoles à indiquer : HTTPS/SSL-TLS, JDBC, ODBC, etc.

***

## Étape 3 – Évaluation de la compatibilité (document structuré)

C'est le **document argumenté** qui justifie les choix d'architecture. L'exercice demande environ **400 à 1200 mots** couvrant trois axes.

### Axe 1 – Sécurité et conformité

**Questions clés à adresser** :

- **Chiffrage en transit** : Comment garantir que les données sensibles (SQL Server, données métier) sont protégées lors du transfert on-premise → cloud ?
  - *Réponse attendue* : SSL/TLS pour tous les transferts, VPN site-to-site chiffré, option Direct Connect si besoin accru.
- **Chiffrage au repos** : Comment sécuriser les données dans S3 et la data warehouse ?
  - *Réponse attendue* : Chiffrage S3 (AES-256), chiffrage Redshift natif, audit CloudTrail.
- **Gestion des identités unifiée** : Comment étendre AD on-premise au cloud ?
  - *Réponse attendue* : AWS Directory Service (Managed Microsoft AD ou Connector), permettant authentification SSO, rôles et permissions cohérents.
- **Conformité réglementaire** : Données critiques (ERP, CRM) doivent-elles rester on-premise ou peuvent-elles résider dans le cloud ?
  - *Réponse attendue* : Dépend du secteur industriel et des régulations (RGPD, ISO 27001, etc.), à évaluer case-by-case.

**À évaluer dans le document** :
- Forces : chiffrage natif AWS, audit CloudTrail, isolation des données par VPC.
- Limitations : coûts additionnels de chiffrage, complexité de gestion des certificats.
- Points d'attention : audits de sécurité réguliers, rotation des clés, révision des permissions AD.

### Axe 2 – Interopérabilité

**Questions clés à adresser** :

- **Synchronisation SQL Server ↔ Cloud** : Comment réamorcer les données historiques (40 To) et maintenir la synchronisation ongoing ?
  - *Options* :
    - **AWS DMS (Database Migration Service)** : migrer une fois + réplication continue. Coût : faible à modéré.
    - **AWS Glue** : ETL managed, peut extraire et charger. Coût : selon volume/temps de calcul.
    - **JDBC/ODBC + scripts Python/Spark** : solution plus légère si peu de transformations.
  - *Recommandation prudente* : DMS pour migration initiale, puis Glue ou Spark pour MAJ continues.

- **Intégration Redpanda avec SQL Server et SAN** :
  - Les données IoT et logs arrivent-elles d'abord dans Redpanda, puis sont traitées et écrites dans S3 et la data warehouse ?
  - Ou faut-il que Redpanda consomme aussi depuis des topics générés par SQL Server ou SAN ?
  - *Réponse* : Généralement, flux nouveaux → Redpanda, flux historiques → DMS/Glue.

- **Automatisation des flux** : Comment assurer que les pipelines s'exécutent sans intervention manuelle ?
  - *Options* :
    - **AWS Glue Workflows** : orchestration native, déclencheurs programmés.
    - **Apache Airflow** (sur on-premise ou auto-hébergé en cloud) : plus flexible.
    - **Redpanda Connect** : connecteurs Redpanda pour intégration avec bases externes.
  - *Recommandation* : Glue Workflows pour simplicité AWS, Airflow si besoin flexibilité.

**À évaluer dans le document** :
- Forces : AWS DMS éprouvé, Redpanda compatible Kafka, Glue serverless réduit ops.
- Limitations : DMS nécessite compute temporaire (coûts), Glue non idéal pour micro-batches hautes fréquences.
- Points d'attention : tester la latence de synchronisation (RTO/RPO), documenter les transformations.

### Axe 3 – Scalabilité et gestion des coûts

**Questions clés à adresser** :

- **Scalabilité du stockage** :
  - S3 : illimité, scalabilité automatique → ✅ Excellent.
  - Data warehouse : capacité initiale à dimensionner. Redshift vs Snowflake vs Athena ?
    - **Redshift** : scaling manuel, moins coûteux mais nécessite planification.
    - **Snowflake** : scaling automatique, coûts à l'usage, API conviviale.
    - **Athena** : requêtes ad-hoc sur S3, pay-per-query, scalable infiniment.
  - **Recommandation** : Athena pour analytics exploratoire, Redshift pour workloads OLAP intensifs et réguliers.

- **Scalabilité du flux temps réel** :
  - Redpanda : peut-il absorber 50 Go/mois + croissance future ?
  - 50 Go/mois ≈ 20 Mo/jour (faible), Redpanda peut en gérer aisément 1000x plus.
  - Dimensionner le cluster Redpanda (nombre de brokers, CPU, RAM) en fonction de la rétention et de la throughput.

- **Estimation des coûts** (à faire avec AWS Pricing Calculator) :
  - **S3** : $0.023/Go/mois (Standard), ~$2.30/To/mois. Pour 50 Go/mois nouveaux, ~$1.15/mois (croissance).
  - **Redshift** : instance 2-nœud `dc2.large` ≈ $3,000/mois (indicatif), ou Spectrum (requêtes sur S3) moins cher.
  - **AWS Directory Service Managed AD** : ~$28/nœud/mois.
  - **DMS** : frais de réplication continue, $0.5/dms unit/heure, instance min $0.5/heure.
  - **Glue** : $1.50/DPU-heure, jobrun moyen 2–10 min/jour ≈ $10–100/mois.
  - **Connectivité** : VPN site-to-site gratuit (mais limité bande), Direct Connect 1 Gbps ≈ $0.30/heure ≈ $2,200/mois.
  
  **Total estimé (ordre de grandeur)** : $3,500–5,500/mois (Redshift), ou $1,500–2,500/mois (Athena + DMS + Glue).

- **Surveillance et optimisation** :
  - **CloudWatch** : métriques natives AWS.
  - **AWS Cost Explorer** : granularité par service, par tag.
  - **Budget Alerts** : alertes si dépassement.
  - **Reserved Instances / Savings Plans** : rabais 25–40% sur compute.

**À évaluer dans le document** :
- Forces : S3 scalable et pas cher, Redpanda léger pour 50 Go/mois, AWS pricing transparent.
- Limitations : Redshift fixe-coûts initiaux, DMS récurrent, Direct Connect très coûteux.
- Points d'attention : dimensionner conservativement d'abord, monitorer utilisation hebdo, ajuster ressources trimestriellement.

***

## Résumé des choix clés à documenter dans Étape 3

Voici une **matrice des décisions** à prendre et justifier :

| Décision | Choix recommandé | Justification brève | Coûts estimés |
|----------|-----------------|------------------|---------------|
| **Stockage objet** | AWS S3 | Scalabilité, intégration AWS, faible coûts | $1–10/To/an |
| **Data warehouse** | Athena (analytique) + Redshift (OLAP lourd) | Flexibilité, séparation charges | $1,500–3,000/mois |
| **Extension AD** | AWS Managed Microsoft AD | SSO, gestion unifiée, support natif | $300–500/an |
| **Sync SQL Server** | AWS DMS initial + Glue continu | Éprouvé, migration rapide, maintenance légère | $500–1,500/mois |
| **Ingestion flux IoT** | Redpanda sur EC2 ou auto-hébergé | Léger, compatible Kafka, ops simple | $500–2,000/mois |
| **Connectivité** | VPN site-to-site + option Direct Connect | VPN pour démarrage, DX si hautes performances exigées | $0 (VPN) → $2,200/mois (DX) |
| **Orchestration** | AWS Glue Workflows (ou Airflow si besoin) | Serverless, intégration Glue, peu d'ops | $50–500/mois |
| **Surveillance coûts** | AWS Cost Explorer + Budget Alerts | Natif, temps réel, alertes | Inclus gratuit |

***

## Points clés à retenir pour la rédaction de l'Étape 3

1. **Structure recommandée du document** (400–1200 mots) :
   - **Introduction** : résumé des besoins (50 Go/mois, compatibilité SI).
   - **Sécurité** : chiffrage, AD, conformité (2–3 paragraphes).
   - **Interopérabilité** : sync SQL Server, Redpanda, automation (2–3 paragraphes).
   - **Scalabilité & coûts** : croissance future, estimation chiffrée (2–3 paragraphes).
   - **Conclusion** : avantages nets et points de vigilance (1 paragraphe).

2. **Ton et rigueur scientifique** : référencer les documentations officielles (AWS docs, Redpanda docs, OWASP si sécurité), pas de spéculation.

3. **Éviter les pièges** :
   - Ne pas oublier les coûts de personnel et de formation.
   - Ne pas ignorer la question de la **résilience** : RTO/RPO, sauvegardes, DRP.
   - Clarifier qui héberge quoi (on-premise vs cloud) et pourquoi.

