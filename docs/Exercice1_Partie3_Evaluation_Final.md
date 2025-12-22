# Évaluation de la compatibilité de l'architecture hybride cloud
## Exercice 1 – Modélisation infrastructure InduTechData (Révisée)

---

## Introduction

InduTechData fait face à une saturation critique de son infrastructure on-premise avec 50 Go/mois de flux IoT temps réel. Cette évaluation propose une architecture hybride AWS optimisée, consolidant les données brutes dans S3 comme source unique immuable, utilisant Redshift pour l'analytique en deux flux distincts (SQL nightly + IoT real-time), Redpanda pour l'ingestion streaming, et Directory Service pour l'identité unifiée. L'architecture déploie un Gateway Kafka on-premise essentiel et adopte les bonnes pratiques OLAP en maintenant des fact tables séparées par fréquence d'update, éliminant les faux décalages analytiques.

---

## 1. Justification des composants cloud sélectionnés

### Amazon S3 (Stockage d'objets – Source de vérité unique immuable)

**Rôle critique** : S3 héberge l'ensemble des données brutes (IoT Parquet, SQL Server Parquet), constituant la source unique de vérité immuable, protégée par WORM Object Lock contre suppression accidentelle ou malveillante.

**Scalabilité** : Capacité illimitée, architecture distribuée multi-AZ. Supporte croissance 10x (50 Go → 500 Go/mois) sans refonte architecturale ni coûts supplémentaires.

**Immuabilité et audit** : S3 Object Lock (WORM) garantit que données, une fois écrites, sont immuables 30 jours minimum. Versionning automatique permet audit trail complet (7 ans rétention). Si Redshift crash, données recalculables depuis S3 en 2-4 heures.

**Tiering économique** : Auto-archivage Glacier après 90 jours réduit coûts long-terme (compliance 7 ans pour ~$500/an vs $13k standard).

**Coûts** : $13,050/an (50 Go IoT/mois + 6 To SQL delta/mois + Glacier tiering)

---

### Amazon Redshift (Data Warehouse analytique OLAP)

**Positionnement** : Moteur analytique OLAP dénormalisé pour requêtes complexes. Rôle = **consumption layer dérivé**, NON source de données persistante. Si Redshift crash, recalculable depuis S3 via Glue en 2-4h.

**Architecture OLAP robuste** : Deux fact tables distinctes (fact_sales nightly + fact_iot_metrics real-time) respectent bonnes pratiques OLAP en séparant données par fréquence d'update. Métadonnées explicites (data_loaded_at, data_is_fresh_as_of) permettent aux analystes de distinguer données 24h-old (SQL) des données < 1min (IoT), évitant fausses corrélations.

**Interopérabilité SQL Server** : Migration initiale 40 To via Snowball ($300 one-time, local copy très rapide, pas ISP egress). Sync nightly : Glue ETL (2 DPU, 30-60 min) transforme delta 200 GB SQL depuis S3 et dénormalise Redshift. Redshift reçoit données transformées, analytique-optimisées (compression columnar 8 To physique vs 40 To logique).

**Latence analytique acceptable** : Nightly updates (02:00-03:00 UTC) suffisent pour reporting/BI batch. IoT real-time streams direct via Spark (< 60 sec latency) vers deuxième fact table. Séparation explicite = analysts conscients des SLAs différents.

**Coûts** : $18,888/an (2 nœuds dc2.large, 1-year Reserved Instances -30%)

---

### Redpanda (Streaming IoT kafka-compatible)

**Rôle** : Broker Kafka-compatible pour ingestion IoT 50 Go/mois continu, destinations multiples sans duplication. Redpanda publie topics Kafka. PySpark Streaming consomme topics une seule fois, écrit simultanément S3 (Parquet backup brut) ET Redshift (agrégations real-time). Zéro duplication data ou network.

**Hébergement AWS** : 3 brokers EC2 t3.xlarge multi-AZ. Latence 10-50 ms on-prem → AWS acceptable pour 50 Go/mois (charge extrêmement légère : 20 MB/jour = 15 KB/sec). Elasticité cloud : scalable 5 min vs 6 mois hardware on-prem.

**Résilience** : Multi-AZ failover automatique (RTO < 5 min si AZ down). Data buffered in topics pendant outage cloud (Redpanda continue accepter PUSH depuis Gateway on-prem même si Redshift down).

**Coûts** : $3,800/an (3 × EC2 t3.xlarge + EBS, 1-year RI -30%)

---

### Kafka Gateway VM on-premise (Infrastructure REQUISE)

**Composant essentiel non-optionnel** : Capteurs IoT poussent données vers Gateway Kafka on-prem (Docker container, 2 vCPU, 4 GB RAM). Gateway transforme données capteurs (Modbus, CAN, MQTT) en événements JSON Kafka. Gateway PUSH vers Redpanda AWS via VPN sécurisé (Kafka API SSL/TLS port 9093).

**Résilience local** : 50 GB local SSD buffer permet buffering si connexion AWS fail. En cas outage AWS Redpanda, Gateway accumule données localement 24-48h. Données jamais perdues (Redpanda topics reprennent lors reconnexion).

**Infrastructure** : Allocation incremental sur hypervisor existant. Opex estimé ~$400-800/an (patching, monitoring, 4 h/year IT admin).

---

### AWS Directory Service (Gestion identités unifiée)

**Rôle** : Managed Microsoft AD synchronisée bidirectionnelle AD on-prem ↔ AWS. SSO unifié : utilisateur authentifie une fois → accès partout (on-prem + AWS services).

**Sync temps réel** : LDAP SSL/TLS port 636, bidirectionnel < 5 sec. Permission changement on-prem propagée cloud immédiatement (sécurité critique).

**Résilience** : AWS inclut snapshots quotidiens 30 jours + multi-AZ replication (RTO 5-10 min AZ failure). Additionnel : export S3 quotidien avec Object Lock WORM ($4/an) protège contre ransomware AD.

**Coûts** : $676/an (2 nœuds $56/mois + S3 backup $4/an)

---

## 2. Sécurité et conformité

**Chiffrage transit** : Tous flux via TLS 1.2+ (Kafka SSL port 9093, JDBC 5439, LDAP 636, HTTPS S3/DataSync/CloudWatch). VPN Site-to-Site IPSec v2 pour Gateway ↔ Redpanda, SQL DataSync, AD LDAP.

**Chiffrage repos** : AES-256 server-side S3/Redshift/Directory Service. KMS gère clés (rotation annuelle, audit CloudTrail).

**Identités unifiées** : AD on-prem ↔ Directory Service syncs. Permissions granulaires : S3 (bucket policies, IAM), Redshift (row-level security), EC2 (security groups).

**Audit complet** : CloudTrail centralise API calls (S3, Redshift, IAM) en CloudWatch Logs. S3 versioning fournit historique immuable 7 ans. VPC Flow Logs capture trafic réseau. Monitoring → CloudWatch (dotted lines, non-critical Tier 3).

**Conformité** : WORM Object Lock GDPR-ready (7 ans retention). No ransomware risk (S3 immutable, Directory Service WORM backup).

---

## 3. Interopérabilité : Flux consolidés (5 flux critiques)

### Flux 1 : SAN IoT → Redpanda (⚡ Temps réel - Tier 1)
Capteurs industriels (Modbus, CAN, MQTT) envoient 50 Go/mois continu via Gateway Kafka on-prem (Docker, SDK Kafka). Gateway PUSH → Redpanda AWS (Kafka API SSL/TLS port 9093, < 1 sec latency, via VPN).

### Flux 2a : Redpanda → S3 (📦 IoT Data Lake)
PySpark Streaming reads Redpanda topics (une seule fois, consumer group unique). Spark écrit Parquet micro-batches toutes 5-10 min vers S3 datalake. **Purpose : Immutable IoT backup (source de vérité)**.

### Flux 2b : Redpanda → Redshift (⚡ IoT Analytics real-time)
Same PySpark Streaming job (reads Redpanda une fois), écrit SIMULTANÉMENT vers Redshift fact_iot_metrics. Agrégations temps réel (SUM, COUNT, avg) via JDBC SSL/TLS, < 60 sec latency. **Purpose : Real-time analytics (recalculable from Flux 2a)**. Distinct fact table de Flux 3c (SQL nightly).

### Flux 3a/b : SQL Server → S3 (📦 SQL Métier Backup)
Initial : Snowball device ($300 one-time, 40 To, local copy instant). Daily : DataSync 200 GB/day delta (HTTPS via VPN). Destination : S3 Parquet brut, WORM-protected. **Purpose : Immutable métier backup (source de vérité SQL)**.

### Flux 3c : S3 → Glue → Redshift (🔄 SQL Analytics nightly)
Glue ETL job (2 DPU, scheduled 02:30 UTC) reads S3 Parquet (intra-AWS free). Transforms : JOIN tables, dénormalize, aggregate. Writes Redshift fact_sales (JDBC COPY). Nightly latency 24h acceptable pour BI batch. **Purpose : Analytics derived from SQL (recalculable from S3)**.

### Flux 4 : AD ↔ Directory Service (🔄 Identités - Tier 1)
Bidirectional LDAP SSL/TLS sync < 5 sec. Users authenticate once → access everywhere. Daily S3 backup with Object Lock WORM.

### Monitoring (Tier 3 - non-critical)
CloudWatch receives metrics/logs from Redpanda, Redshift, Glue, CloudTrail (dotted lines, implicit, no data loss if down).

---

## 4. OLAP Architecture : Bonnes pratiques

**Fact tables séparées par fréquence** : fact_sales (nightly SQL, 24h latency) vs fact_iot_metrics (real-time IoT, < 1min latency). Métadonnées explicites (data_loaded_at, data_is_fresh_as_of) permettent aux analystes de voir freshness différente, évitant fausses corrélations.

**Joins explicites** : Queries joignent tables uniquement sur dates identiques (ex: "yesterday's orders with yesterday's factory metrics"). Documentation stricte prevent anti-patterns.

**Dashboards séparés** : Sales dashboard (nightly static) vs Factory KPIs (real-time dynamic) vs Correlation analysis (manual, same-date comparison). Pattern standard dans industry (manufacturing, e-commerce, healthcare).

**Conforme OLAP** : Séparation fact tables par grain + fréquence = bonnes pratiques. Non-conforme serait single fact table mixing 24h-old orders avec IoT real-time (false correlation risk).

---

## 5. Scalabilité et coûts optimisés

### Croissance 10x (50 Go → 500 Go/mois)
- S3 : Automatique illimité
- Redpanda : Ajouter 2-3 brokers (15 min, no downtime)
- Redshift : Resize 4-6 nœuds (linear perf increase)
- Glue : Auto-scale DPUs (minutes)

### Coûts finalisés (Architecture optimisée)

| Composant | Year 1 | Year 2+ |
|-----------|--------|---------|
| **S3 + Glacier** | $13,050 | $13,050 |
| **Redshift (2 nœuds)** | $18,888 | $18,888 |
| **Redpanda EC2** | $3,800 | $3,800 |
| **Glue ETL** | $1,596 | $1,596 |
| **Directory Service** | $676 | $676 |
| **DataSync (delta only)** | $729 | $729 |
| **Snowball (init)** | $300 | - |
| **VPN Site-to-Site** | $1,878 | $1,878 |
| **CloudWatch/Trail/KMS** | $3,696 | $3,696 |
| **ISP egress (200 GB/day SQL + backup)** | $2,000 | $2,000 |
| **On-prem Gateway ops** | $400-800 | $400-800 |
| | | |
| **TOTAL** | **$47,013-47,413** | **$46,313-46,713** |

**Comparaison** : vs full on-prem ($85-145k/an, Kafka expert hiring $60k) → Hybrid saves $40-100k/an. vs full cloud ($45,696/an, requires sensor capability) → Hybrid +$1,300/an for on-prem flexibility.

---

## 6. Avantages et limitations

### Avantages
✅ Modernisation cloud atteinte (S3 + Redshift AWS) sans surcharge on-prem  
✅ Data intégrité maximale (S3 WORM source of truth, recalculabilité totale)  
✅ OLAP bien-structuré (separate fact tables, explicit joins, metadata)  
✅ Scalabilité cloud-native (elasticity 10x growth)  
✅ Sécurité multicouches (chiffrage, audit CloudTrail, WORM backup)  
✅ Coûts raisonnables (~$47k/an vs $85k+ on-prem ou $120k+ real-time)  
✅ Ops burden minimal (AWS managed Redpanda, Glue, Directory Service)

### Limitations et points d'attention

**Latence** : On-prem → AWS 10-50 ms acceptable (50 Go/mois très faible). Non pour ultra-low-latency < 5ms (alternative : on-prem Redpanda).

**Dépendance VPN** : Single point of failure (3 flux via VPN). Mitigation : Dual VPN, Gateway local buffering.

**Expertise requise** : Kafka Gateway ops (Linux/Docker), Glue ETL (PySpark), OLAP design (fact table separation). PME peut apprendre 1-2 weeks.

**OLAP discipline** : Must separate fact tables + metadata + explicit joins. Common source of BI errors if not enforced.

---

## Conclusion

L'architecture hybride cloud optimisée répond objectifs InduTechData (saturation on-prem, modernisation cloud, analytique scalable). S3 source de vérité immuable (WORM), Redshift analytics OLAP bien-structuré (separate fact tables nightly SQL + real-time IoT), Redpanda streaming Kafka-compatible, Directory Service identités unifiées créent infrastructure scalable, sécurisée, rentable (~$47k/an). Gateway Kafka on-premise essentiel + discipline OLAP (explicit joins, metadata freshness) éliminent risques false correlation et ensure data intégrité.

**Phases implémentation** : Phase 1 (month 1) audit SI, tester Snowball clone, Glue ETL dev, failover tests. Phase 2 (week 1-2) Snowball migration, DataSync nightly, Redshift provisioning, training ops. Phase 3 (month 1-3 post-go-live) monitor replication lag, optimize Glue job, calibrate CloudWatch, validate fact table separation OLAP.

**Points succès critiques** : S3 backup immuable (RTO < 1h), VPN monitored 24/7, coûts AWS < $50k/mois, ops team AWS-ready, OLAP separation enforced (fact tables validated), Gateway on-prem stable (local buffer functional).

