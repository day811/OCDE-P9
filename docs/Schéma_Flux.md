# Tableau récapitulatif complet des flux - Exercice 1 InduTechData

## Architecture finale CORRIGÉE (7 flux critiques)

| # | Source | Destination | Type | Criticité | **Données transférées** | **Volume** | **Fréquence** | **Protocole/Outil** | **Sécurité** | **Raison / Justification** |
|---|--------|-------------|------|-----------|---|---|---|---|---|---|
| **1** | SAN | Redpanda | ⚡ Temps réel | Critique | **Flux IoT brut** (capteurs industriels, 50 Go/mois) | ~20 MB/jour | Continu (temps réel) | Kafka API + connecteur | SSL/TLS 1.3 (port 9093) | Ingestion données temps réel IoT (besoin nouveau 50 Go/mois mentionné exercice) |
| **2** | Redpanda | S3 | ⚡ Temps réel | **Critique** | **Données IoT transformées** (Parquet, compressées) | ~50 GB/mois | Micro-batches (toutes les 5-10 min) | S3 API HTTPS + PySpark Streaming | HTTPS + AES-256 S3 server-side encryption | **BACKUP IoT brut** = data lake source de vérité pour données temps réel |
| **3** | Redpanda | Redshift | ⚡ Temps réel | Non-critique | **Agrégations temps réel** (SUM revenue, COUNT tickets, avg latency) | Variable (~100 MB/min) | Continu (streaming writes) | Direct Redshift API (JDBC) | SSL/TLS over JDBC + IAM auth | Analytical queries temps réel (optionnel, Redshift moteur calcul, pas stockage) |
| **4** | SQL Server | S3 | 📦 Batch | **Critique** | **Données métier BRUTES** (40 To ERP/CRM : orders, customers, products, invoices) | 40 TB initial + delta daily (~200 GB/day) | Initial migration (1 × 3-7 jours) + nightly delta sync | AWS DataSync ou AWS DMS export | SSL/TLS + AES-256 S3 encryption | **BACKUP métier brut** = source de vérité données critiques métier (on-premise) |
| **5** | SQL Server | Redshift | 📦 Batch | Non-critique | **Données métier transformées** (40 To dénormalisées pour analytics) | 40 TB initial + delta daily (~200 GB/day) | Initial load (1 × 3-7 jours) + nightly incremental (via DMS CDC) | AWS DMS (Database Migration Service) + COPY command | JDBC over SSL/TLS + AES-256 Redshift encryption | Analytical data warehouse (Redshift = moteur analytique, pas backup primaire) |
| **6** | Active Directory | AWS Directory Service | 🔄 Temps réel | Critique | **Métadonnées identité** (users, groups, permissions, DN entries) | ~50 MB (métadonnées uniquement) | Bi-directionnel, temps réel (sync continu) | LDAP over SSL/TLS (port 636) + AWS AD Replication | SSL/TLS + Kerberos auth | SSO unifié on-prem ↔ cloud (identités critiques = même permissions partout) |
| **7** | Services (Redpanda, Redshift, S3, Directory Service) | CloudWatch | 👁️ Temps réel | Non-critique | **Métriques & Logs monitoring** (CPU %, memory, queries/sec, errors, latency) | ~5-10 GB/mois (logs agrégés) | Continu (1min intervals pour métriques) | HTTPS CloudWatch API + CloudTrail | HTTPS + IAM IAM roles | Observabilité infrastructure (non-critique = ne pas compris alertes de sauvegarde) |

---

## Détails complémentaires par flux

### FLUX 1 : SAN → Redpanda (⚡ Temps réel - Critique)

| Aspect | Description |
|--------|-------------|
| **Source** | SAN Storage (10 To) = données non-structurées |
| **Données** | Flux IoT brut (capteurs industriels temps réel) |
| **Volume** | 50 Go/mois = ~20 MB/jour = ~15 KB/sec (très faible) |
| **Fréquence** | Continu (événementiel, pas batch) |
| **Protocole** | Kafka API (Redpanda Kafka-compatible) |
| **Port** | 9093 (SSL/TLS) ou 9092 (plaintext) |
| **Chiffrage** | SSL/TLS 1.3, certificats mutuels |
| **Authentification** | SASL/SCRAM ou IAM (si AWS MSK) |
| **Outil** | Kafka Connect source ou collecteur custom (Filebeat, Fluentd) |
| **Latence acceptable** | < 1 seconde (IoT critique) |
| **RTO/RPO** | RPO < 1 sec, RTO < 5 min (données IoT peuvent être perdues court-terme) |

---

### FLUX 2 : Redpanda → S3 (⚡ Temps réel - Critique)

| Aspect | Description |
|--------|-------------|
| **Source** | Redpanda Topics (client_tickets, sensor_data, etc.) |
| **Destination** | S3 Buckets (Raw Data partition) |
| **Données** | IoT transformé/agrégé en Parquet (même données que Flux 1, format optimisé) |
| **Volume** | ~50 GB/mois (légèrement compressé vs JSON brut) |
| **Fréquence** | Micro-batches : écrire un fichier Parquet toutes les 5-10 minutes |
| **Format** | Parquet (colonaire, compressé ~3x vs JSON) |
| **Partitioning** | S3 path : `s3://indutech-datalake/iot/year=2025/month=01/day=17/hour=16/` |
| **Protocole** | S3 API HTTPS (boto3, Spark S3A) |
| **Chiffrage** | AES-256 server-side encryption (S3 managed or KMS) |
| **Authentification** | IAM roles EC2 (Redpanda runs on EC2) |
| **Outil** | PySpark Streaming WRITE ou custom Kafka → S3 connector |
| **Latence acceptable** | < 15 minutes (batch acceptable, data lake) |
| **RTO/RPO** | RPO = 5-10 min (time between writes), RTO = 1h (restore from latest partition) |
| **Justification criticité** | C'est le BACKUP de données IoT brutes → source de vérité long-terme |

---

### FLUX 3 : Redpanda → Redshift (⚡ Temps réel - Non-critique)

| Aspect | Description |
|--------|-------------|
| **Source** | Redpanda Topics (client_tickets, sensor_data, etc.) |
| **Destination** | Redshift Cluster (tables analytiques) |
| **Données** | Agrégations temps réel (SUM revenue, COUNT tickets, avg latency, group by customer/region) |
| **Volume** | Variable, ~100 MB/min (depends on aggregations & downsampling) |
| **Fréquence** | Continu streaming writes via Spark Streaming or Kinesis Firehose |
| **Transformation** | PySpark Streaming : GROUP BY, window functions, enrichments |
| **Protocole** | JDBC (Redshift native driver) |
| **Port** | 5439 (Redshift default) |
| **Chiffrage** | SSL/TLS over JDBC |
| **Authentification** | Redshift IAM credentials + database user/password |
| **Outil** | PySpark Streaming WRITE mode="append" to Redshift |
| **Latence acceptable** | 10-60 seconds (near real-time analytics OK) |
| **RTO/RPO** | RPO N/A (recalculate from S3), RTO = rebuild from Flux 2 data |
| **Justification non-criticité** | Redshift = moteur analytique optionnel. Si crash, données peuvent être recalculées depuis S3 (Flux 2) |

---

### FLUX 4 : SQL Server → S3 (📦 Batch - Critique)

| Aspect | Description |
|--------|-------------|
| **Source** | SQL Server Cluster (40 To) = ERP/CRM métier |
| **Destination** | S3 Buckets (Backup partition) |
| **Données** | Dump complet données métier BRUTES (tables : orders, customers, products, invoices, GL) |
| **Volume** | 40 TB initial migration + ~200 GB delta/day |
| **Fréquence** | Initial : 1× migration (3-7 jours débit réseau) + Nightly incremental (02:00 UTC) |
| **Format** | CSV, Parquet, or Backup files (.bak format convertis en S3) |
| **Partitioning** | S3 path : `s3://indutech-backup/sql-server/year=2025/month=01/day=17/` |
| **Protocole** | HTTPS (S3 API via AWS DataSync or custom scripts) |
| **Chiffrage** | AES-256 server-side encryption + client-side encryption (KMS optional) |
| **Authentification** | IAM role (on AWS migration instance) |
| **Outil** | AWS DataSync (managed service) OR AWS Snowball (for initial 40 TB, then sync) |
| **Latency acceptable** | < 24 hours acceptable (batch daily) |
| **RTO/RPO** | RPO = 24h (daily backup), RTO = 2-4h (restore from latest daily) |
| **Justification criticité** | **SOURCE DE VÉRITÉ = données métier brutes** (on-prem). MUST backup for DR/compliance. Non-negotiable. |

---

### FLUX 5 : SQL Server → Redshift (📦 Batch - Non-critique)

| Aspect | Description |
|--------|-------------|
| **Source** | SQL Server Cluster (40 To) = ERP/CRM métier |
| **Destination** | Redshift Cluster (tables dénormalisées analytiques) |
| **Données** | Mêmes données SQL Server MAIS transformées (dénormalisées, agrégées pour OLAP) |
| **Volume** | 40 TB initial + ~200 GB delta/day |
| **Fréquence** | Initial load (1×, 3-7 jours) + Nightly incremental sync (02:00 UTC) |
| **Transformation** | ETL dénormalisation (jointures, aggregations, slowly changing dims) |
| **Protocole** | JDBC (AWS DMS Database Migration Service) |
| **Chiffrage** | SSL/TLS over JDBC + AES-256 Redshift cluster encryption |
| **Authentification** | DMS IAM role + Redshift master user |
| **Outil** | AWS DMS (full load + CDC mode) OR AWS Glue (Spark ETL script) |
| **Latency acceptable** | 12-24 hours (nightly OK, not real-time) |
| **RTO/RPO** | RPO = 24h (nightly sync), RTO = rebuild from Flux 4 (S3 backup) + re-transform |
| **Justification non-criticité** | Redshift = analytical engine, NOT primary storage. Data can be recalculated from Flux 4 (S3 backup). If Redshift crashes, use S3 + re-run DMS/Glue. |

---

### FLUX 6 : AD ↔ Directory Service (🔄 Temps réel - Critique)

| Aspect | Description |
|--------|-------------|
| **Source/Dest** | Active Directory on-premise ↔ AWS Managed Microsoft AD |
| **Données** | Métadonnées identité (usernames, groups, DN entries, SIDs, permissions) |
| **Volume** | ~50 MB (très petit : metadata only) |
| **Fréquence** | Bi-directionnel, temps réel (sync change notifications) |
| **Protocol** | LDAP over SSL/TLS (port 636) + AD replication protocol |
| **Chiffrage** | SSL/TLS 1.2+ + Kerberos authentication |
| **Authentication** | Kerberos ticket (AD native auth) |
| **Outil** | AWS Managed AD Connector (lightweight proxy) OR Managed AD (replication) |
| **Latency acceptable** | < 5 seconds (identities must sync quickly) |
| **RTO/RPO** | RPO < 5 sec (real-time SSO), RTO < 1 min (failover to AD Connector) |
| **Justification criticité** | SSO = **user authentication on-prem AND cloud must be identical**. If identity sync fails, users cannot authenticate anywhere. CRITICAL. |

---

### FLUX 7 : Services → CloudWatch (👁️ Temps réel - Non-critique)

| Aspect | Description |
|--------|-------------|
| **Sources** | Redpanda (broker metrics), Redshift (query logs), S3 (request logs), Directory Service (audit) |
| **Destination** | AWS CloudWatch (centralized monitoring) |
| **Données** | Métriques de monitoring (CPU %, memory %, disk I/O, network throughput, query count, errors, latency) + CloudTrail audit logs |
| **Volume** | ~5-10 GB/month (aggregated metrics) |
| **Fréquence** | Continuous (metrics pushed every 1-5 minutes, logs streamed real-time) |
| **Protocol** | HTTPS CloudWatch API (PutMetricData, PutLogEvents) |
| **Chiffrage** | HTTPS + TLS 1.2+ |
| **Authentication** | IAM roles (service-to-service auth) |
| **Outil** | CloudWatch Agent + CloudTrail (native AWS monitoring) |
| **Latency acceptable** | 1-5 minutes (alerting can tolerate some delay) |
| **RTO/RPO** | RPO = 5 min (metric aggregation window), RTO N/A (monitoring only) |
| **Justification non-criticité** | Monitoring = observability only. If CloudWatch fails, infrastructure continues running (no data loss, just no alerts). Important but NOT critical for data integrity. |

---

## Résumé par type de flux

### Flux CRITIQUES (backups + identités)
- **Flux 2** : Redpanda → S3 (IoT backup brut)
- **Flux 4** : SQL Server → S3 (métier backup brut)
- **Flux 6** : AD ↔ Directory Service (identités SSO)

**➜ Ces flux DOIVENT réussir, sinon perte données ou perte accès utilisateurs**

### Flux NON-CRITIQUES (analytique + monitoring)
- **Flux 3** : Redpanda → Redshift (aggregations, recalculable)
- **Flux 5** : SQL Server → Redshift (analytics, recalculable)
- **Flux 7** : Services → CloudWatch (observability, facultatif)

**➜ Ces flux peuvent échouer court-terme sans perte données (recalculables depuis Flux 2, 4, 6)**

---

## Matrice : Dépendances entre flux

| Flux | Dépend de | Peut être remplacé par | En cas de failure |
|------|-----------|----------------------|------------------|
| **Flux 2** (Redpanda → S3) | Flux 1 (SAN → Redpanda) | Aucun | Perte données IoT temps réel |
| **Flux 3** (Redpanda → Redshift) | Flux 1 (SAN → Redpanda) | Recalcul depuis Flux 2 | Requêtes analytics indisponibles |
| **Flux 4** (SQL → S3) | SQL Server on-prem | Aucun | Perte données métier |
| **Flux 5** (SQL → Redshift) | Flux 4 (SQL → S3) | Recalcul depuis Flux 4 + ré-ETL | Requêtes analytics indisponibles |
| **Flux 6** (AD ↔ Dir.Svc) | AD on-prem | AD Connector fallback | Utilisateurs ne peuvent pas se logger cloud |
| **Flux 7** (Services → CloudWatch) | Tous les autres | Logs locaux (insuffisant) | Monitoring indisponible (données safe) |

---

## Recommandations de monitoring & alertes

| Flux | Métrique à monitorer | Seuil d'alerte | Action corrective |
|------|-------------------|---------------|----|
| **Flux 1** (SAN → Redpanda) | Redpanda lag (partition offset) | > 5 min | Vérifier réseau VPN, Redpanda brokers CPU |
| **Flux 2** (Redpanda → S3) | S3 write latency, file count/day | > 10 min, < 100 files | Vérifier EC2 Spark cluster, S3 rate limits |
| **Flux 3** (Redpanda → Redshift) | Redshift ingestion lag, query queue | > 1 hour, > 100 queued | Vérifier Redshift WLM config, add nodes |
| **Flux 4** (SQL → S3) | DataSync task duration, errors | > 2h, any errors | Check SQL Server locks, network bandwidth |
| **Flux 5** (SQL → Redshift) | DMS task replication lag, errors | > 30 min, > 0 errors | Check CDC logs, DMS instance CPU/RAM |
| **Flux 6** (AD ↔ Dir.Svc) | AD replication lag, sync errors | > 1 min, > 0 errors | Check LDAP connectivity, Directory Service health |
| **Flux 7** (Services → CloudWatch) | Log delivery latency, ingestion errors | > 5 min, > 0 errors | Check CloudWatch agent, IAM permissions |

---

**Fin du tableau récapitulatif complet.**
