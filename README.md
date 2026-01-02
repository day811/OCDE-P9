# Exercice 2 : Pipeline ETL Temps Réel avec Redpanda et PySpark

La vidéo de démonstration est disponible ici : [Projet9_part2_video.mp4](https://youtu.be/wuiCFop4TZc)

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
  - [Installation de Docker](#installation-de-docker)
  - [Configuration du projet](#configuration-du-projet)
- [Démarrage rapide](#démarrage-rapide)
- [Utilisation](#utilisation)
- [Structure des données](#structure-des-données)
- [Résultats et sorties](#résultats-et-sorties)
- [Troubleshooting](#troubleshooting)
- [Points clés du projet](#points-clés-du-projet)

---

## 🎯 Vue d'ensemble

Ce projet implémente un **pipeline ETL (Extract, Transform, Load) temps réel** pour la gestion de tickets clients. Il démontre comment :

- **Produire** des données en continu (tickets aléatoires)
- **Streamer** les données via un broker Kafka (Redpanda)
- **Traiter** les données à grande échelle avec Spark
- **Exporter** les résultats en formats optimisés (Parquet/JSON)

**Use case :** Imaginz une entreprise recevant 1000+ tickets par jour. Ce système capture, enrichit et analyse les tickets automatiquement, 24/7.

---

## 🏗️ Architecture

```mermaid
graph LR
    A["Producteur Python<br/>(Generator)"] -->|JSON| B["Redpanda<br/>(Kafka Broker)"]
    B -->|Messages| C["Processeur PySpark<br/>(ETL Engine)"]
    C -->|Transform| D["Enrichissement<br/>(Add Teams)"]
    D -->|Analyse| E["Exports<br/>(Parquet/JSON)"]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#fce4ec
```

### Composants

| Composant | Rôle | Technologies |
|-----------|------|--------------|
| **Producer** | Génère des tickets clients aléatoires en continu | Python, Kafka-Python |
| **Redpanda** | Broker Kafka-compatible, persiste les messages | Redpanda (Docker) |
| **Processor** | Lit, transforme et enrichit les données | PySpark, Spark SQL |
| **Output** | Exporte les résultats traités | Parquet, JSON |

---

## 📦 Prérequis

- **Système d'exploitation** : Linux Debian/Ubuntu (testé) ou macOS/Windows avec WSL
- **RAM** : Minimum 4 GB (6+ GB recommandé)
- **Espace disque** : 2 GB pour les conteneurs Docker
- **Port disponible** : 9092 (Redpanda)
- **Docker & Docker Compose** : Installés et en fonction

---

## 🔧 Installation

### Installation de Docker

#### Linux (Debian/Ubuntu)

```bash
# 1. Mettre à jour les packages
sudo apt-get update
sudo apt-get upgrade -y

# 2. Installer Docker
sudo apt-get install -y docker.io docker-compose

# 3. Ajouter l'utilisateur courant au groupe docker (optionnel, pour éviter sudo)
sudo usermod -aG docker $USER
newgrp docker

# 4. Vérifier l'installation
docker --version
docker-compose --version
```

#### macOS

```bash
# Avec Homebrew (recommandé)
brew install docker docker-compose

# Ou télécharger Docker Desktop depuis https://www.docker.com/products/docker-desktop
```

#### Windows

1. Installer **WSL2** (Windows Subsystem for Linux 2)
   ```powershell
   wsl --install
   ```

2. Télécharger et installer **Docker Desktop for Windows**
   - https://www.docker.com/products/docker-desktop
   - Activer WSL2 dans les paramètres Docker

3. Vérifier l'installation
   ```powershell
   docker --version
   docker-compose --version
   ```

---

### Configuration du projet

#### 1. Cloner/Créer le projet

```bash
# Créer le répertoire du projet
mkdir -p ~/projects
cd ~/projects

# Cloner le repository
git clone https://github.com/day811/OCDE-P9
cd OCDE-P9
```

#### 2. Structure du projet

Assurer que vous avez la structure suivante :

```
OCDE-P9/
├── README.md                    # Documentation (ce fichier)
├── docker-compose.yml           # Orchestration conteneurs
├── .env                         # Variables d'environnement
├── .gitignore                   # Exclusions Git
├── pyrightconfig.json           # Config type checking
├── producer/                    # Service producteur
│   ├── ticket_producer.py      # Point d'entrée
│   ├── producer.py             # Classe ProductionManager
│   ├── ticket.py               # Modèle Ticket
│   ├── config.py               # Configuration
│   ├── requirements.txt         # Dépendances Python
│   └── Dockerfile              # Image Docker
├── processor/                   # Service processeur
│   ├── spark_processor.py      # Point d'entrée
│   ├── processor.py            # Classe SparkProcessor
│   ├── transformations.py      # Logique métier
│   ├── config.py               # Configuration
│   ├── requirements.txt         # Dépendances Python
│   └── Dockerfile              # Image Docker
├── config/                      # Scripts utilitaires
│   └── redpanda_init.sh        # Initialisation Redpanda
└── data/                        # Répertoire données
    └── output/                 # Résultats export
```

#### 3. Créer les fichiers de configuration

Les fichiers sont fournis dans le `docker-compose.yml` et `.env`. Aucune configuration manuelle requise.

#### 4. Vérifier les ports disponibles

```bash
# Vérifier si le port 9092 est disponible
sudo lsof -i :9092  # Aucun résultat = port libre
```

---

## 🚀 Démarrage rapide

### Étape 1 : Lancer l'ensemble du pipeline

```bash
cd ~/projects/OCDE-P9

# Construire et démarrer tous les conteneurs
docker-compose up --build

# Ou en mode détaché (arrière-plan)
docker-compose up -d --build
```

**Attendez que tous les services démarrent** (environ 30-45 sec) :

```
redpanda_exercice2 | Waiting for Redpanda to start...
init_redpanda      | Topic 'client_tickets' created successfully
ticket_producer    | Starting producer with config: ProducerConfig(...)
ticket_processor   | Starting processor with config: ProcessorConfig(...)
```

### Étape 2 : Vérifier le statut

```bash
# Voir l'état des conteneurs
docker-compose ps

# Affichage attendu :
# NAME                     STATUS          PORTS
# redpanda_exercice2       Up 2 minutes    0.0.0.0:9092->9092/tcp
# init_redpanda            Exited          
# ticket_producer          Up 2 minutes    
# ticket_processor         Up 2 minutes
```

### Étape 3 : Monitorer les logs

```bash
# Logs du producteur (tickets publiés)
docker-compose logs -f producer

# Logs du processeur (tickets traités)
docker-compose logs -f processor

# Tous les logs en temps réel
docker-compose logs -f
```

### Étape 4 : Vérifier les résultats

```bash
# Les fichiers apparaîtront dans data/output/ après ~40 secondes
ls -la data/output/

# Exemple de sortie :
# total 128
# drwxr-xr-x 10 user group  4096 Dec 19 14:23 .
# drwxr-xr-x  3 user group  4096 Dec 19 14:20 ..
# drwxr-xr-x  2 user group  4096 Dec 19 14:23 tickets_with_assignment
# drwxr-xr-x  2 user group  4096 Dec 19 14:23 metrics
# drwxr-xr-x  2 user group  4096 Dec 19 14:23 tickets_by_type
# drwxr-xr-x  2 user group  4096 Dec 19 14:23 tickets_by_priority
# drwxr-xr-x  2 user group  4096 Dec 19 14:23 high_priority_tickets
```

### Étape 5 : Arrêter le pipeline

```bash
# Arrêter tous les conteneurs (conserve les données)
docker-compose down

# Arrêter et supprimer tous les volumes (données perdues)
docker-compose down -v
```

---

## 💻 Utilisation

### Configuration par variables d'environnement

Éditez `.env` pour personnaliser le comportement :

```bash
nano .env
```

**Paramètres clés :**

```env
# Redpanda / Kafka
REDPANDA_BROKER_LOCAL=redpanda:9092        # Adresse du broker
TOPIC_NAME=client_tickets                  # Nom du topic
TOPIC_PARTITIONS=3                         # Nombre de partitions
TOPIC_REPLICATION=1                        # Facteur de réplication

# Producteur
PRODUCER_RATE=10                           # Tickets par seconde
PRODUCER_TIMEOUT=30                        # Timeout de connexion (sec)

# Processeur Spark
SPARK_MEMORY=2g                            # Mémoire Spark
SPARK_EXECUTOR_CORES=2                     # Nombre de cores
OUTPUT_FORMAT=parquet                      # Format: parquet ou json
OUTPUT_PATH=/data/output                   # Chemin de sortie

# Logging
LOG_LEVEL=INFO                             # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT=docker                         # docker ou local
```

**Redémarrez après modification :**

```bash
docker-compose down
docker-compose up --build
```

### Surcharge par arguments CLI

**Producteur :**

```bash
docker-compose exec producer python ticket_producer.py --rate 20 --broker redpanda:9092
```

**Processeur :**

```bash
docker-compose exec processor python spark_processor.py --memory 4g --output-format json
```

---

## 📊 Structure des données

### Format d'entrée (Ticket brut)

```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "CLIENT_5234",
  "created_at": "2025-12-19T14:23:45.123456Z",
  "request": "Unable to reset password",
  "request_type": "account",
  "priority": "high"
}
```

**Champs disponibles :**

| Champ | Type | Exemple | Validations |
|-------|------|---------|-------------|
| `ticket_id` | UUID | `550e8400-...` | Unique, requis |
| `client_id` | String | `CLIENT_1234` | Format `CLIENT_XXXX` |
| `created_at` | ISO8601 | `2025-12-19T14:23:45Z` | Timestamp UTC |
| `request` | String | `"Service not working"` | Max 500 chars |
| `request_type` | Enum | `billing`, `technical`, `account`, `general` | 4 valeurs |
| `priority` | Enum | `low`, `medium`, `high`, `critical` | 4 valeurs |

### Format de sortie (Ticket enrichi)

```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "CLIENT_5234",
  "created_at": "2025-12-19T14:23:45.123456Z",
  "request": "Unable to reset password",
  "request_type": "account",
  "priority": "high",
  "assigned_team": "Account Management"
}
```

**Champ ajouté par enrichissement :**

| Champ | Source | Logique |
|-------|--------|--------|
| `assigned_team` | `request_type` | Mapping automatique pour routing |

---

## 📤 Résultats et sorties

### Emplacements des fichiers

Les résultats sont exportés dans `data/output/` avec la structure suivante :

```
data/output/
├── tickets_with_assignment/     # Tous les tickets enrichis
│   └── part-00000-c99...parquet
├── metrics/                      # Statistiques globales
│   └── part-00000-abc...parquet
├── tickets_by_type/              # Tickets groupés par type
│   └── part-00000-def...parquet
├── tickets_by_priority/          # Tickets groupés par priorité
│   └── part-00000-ghi...parquet
└── high_priority_tickets/        # Tickets critiques/hauts
    └── part-00000-jkl...parquet
```

### Exemple de métriques globales

```json
{
  "total_tickets": 1523,
  "billing_count": 391,
  "technical_count": 456,
  "account_count": 402,
  "general_count": 274,
  "critical_priority_count": 87,
  "unique_clients": 312
}
```

### Consulter les résultats

**Option 1 : Format JSON (lisible dans VSCode)**

```bash
# Modifier .env
OUTPUT_FORMAT=json

# Redémarrer
docker-compose down -v && docker-compose up --build

# Ouvrir directement dans VSCode
code data/output/metrics/part-00000-*.json
```

**Option 2 : Format Parquet (optimisé)**

```bash
# Avec Parquet Viewer (Extension VSCode)
# Clic droit → Preview Parquet File

# Ou convertir en CSV
python -c "
import pandas as pd
df = pd.read_parquet('data/output/metrics')
print(df)
"
```

**Option 3 : Nettoyer la sortie Spark**

```bash
python view_results.py  # Script fourni pour simplifier la structure
```

---

## 🐛 Troubleshooting

### Le port 9092 est déjà utilisé

```bash
# Identifier le processus
sudo lsof -i :9092

# Tuer le processus
sudo kill -9 <PID>

# Ou modifier le port dans docker-compose.yml et .env
```

### Les conteneurs ne démarrent pas

```bash
# Voir les erreurs
docker-compose logs redpanda

# Reconstruire from scratch
docker-compose down -v
docker system prune -a
docker-compose up --build
```

### Le processeur n'a pas de données

```bash
# Vérifier que le producteur publie
docker-compose logs producer | tail -20

# Vérifier le topic existe
docker exec redpanda_exercice2 rpk topic list

# Voir les messages dans le topic
docker exec redpanda_exercice2 rpk topic consume client_tickets
```

### Erreur : "Failed to find data source: kafka"

```bash
# Spark ne trouve pas le connecteur Kafka
# Solution : dans processor/processor.py, vérifier que init_spark() a :
#   .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
```

### Les fichiers Parquet ne se lisent pas directement

C'est normal ! Spark crée une structure multi-fichiers :

```
metrics/
├── _SUCCESS           # Marqueur de succès
├── ._SUCCESS.crc      # Checksum
├── .part-00000...     # Fichier temporaire
└── part-00000...      # ✅ LE VRAI FICHIER
```

**Solution :** Utiliser le script `view_results.py` ou convertir en JSON.

### Performance lente

```bash
# Augmenter les ressources dans .env
SPARK_MEMORY=4g          # au lieu de 2g
SPARK_EXECUTOR_CORES=4   # au lieu de 2

# Ou réduire le timeout producteur
PRODUCER_TIMEOUT=15
```

---

## 🎓 Points clés du projet

### 1. Producteur (Producer)

**Rôle :** Générer des tickets clients aléatoires.

**Code clé :**

```python
# producer/ticket_producer.py
def generate_random_ticket() -> Ticket:
    """Crée un ticket avec données aléatoires."""
    return Ticket(
        ticket_id=str(uuid.uuid4()),
        client_id=f"CLIENT_{random.randint(1000, 9999)}",
        request=random.choice(SAMPLE_REQUESTS),
        request_type=random.choice(REQUEST_TYPES),
        priority=random.choice(PRIORITIES)
    )
```

**Concepts :**
- **Rate limiting :** Publié N tickets/sec pour simuler une charge réaliste
- **Sérialisation JSON :** Conversion objet Python → texte Kafka
- **Reconnexion automatique :** Gestion des défaillances réseau

### 2. Broker Redpanda (Kafka)

**Rôle :** Persister les messages pour découplage producteur/consommateur.

**Concepts :**
- **Topics :** Canaux logiques (`client_tickets`)
- **Partitions :** Parallélisme (3 partitions = 3 workers)
- **Offset :** Position de lecture, permet reprendre après crash
- **Réplication :** Haute disponibilité (facteur = 1 en dev, 3+ en prod)

### 3. Processeur Spark

**Rôle :** Transformer et enrichir les données à l'échelle.

**Pipeline ETL :**

```python
# processor/transformations.py

# Extract
df = spark.read.kafka(...).select("ticket.*")

# Transform
df = Transformations.add_support_team(df)
metrics = Transformations.calculate_ticket_metrics(df)
by_priority = Transformations.group_by_priority(df)

# Load
df.write.parquet("data/output/tickets_with_assignment")
```

**Optimisations appliquées :**
- **Coalesce(1) :** Merge partitions pour 1 fichier (plus simple à lire)
- **Schema parsing :** Validation JSON avant traitement
- **Lazy evaluation :** Spark optimise la requête avant exécution

### 4. Architecture Batch vs Streaming

**Notre POC = BATCH (une seule exécution)**

```
Start → Read ALL data → Process → Export → Exit
```

**Production = STREAMING (continu)**

```
Start → Read MICRO-BATCH → Process → Export → Repeat every 30sec → ...
```

### 5. Concepts Data Engineering

| Concept | Application ici | Importance |
|---------|-----------------|-----------|
| **Schéma validation** | Type checking JSON | Qualité données |
| **Partitioning** | 3 partitions Redpanda | Parallélisme |
| **Checkpointing** | `startingOffsets` | Reprendre après crash |
| **Idempotence** | Même ID = même record | Pas de doublons |
| **Scalabilité** | Horizonal via partitions | Croître sans limite |

---

## 📚 Ressources complémentaires

- **Apache Spark :** https://spark.apache.org/docs/latest/
- **Redpanda :** https://redpanda.com/documentation
- **Kafka Concepts :** https://kafka.apache.org/documentation/#concepts
- **Docker :** https://docs.docker.com/

---

## 📝 Notes importantes

- **Données de test :** Générées aléatoirement, non persistées entre redémarrages
- **Format Parquet :** Format columnar compressé, optimal pour analyse
- **Checkpoint :** Spark peut reprendre depuis dernier offset en cas crash
- **Volume :** POC avec ~100-1000 tickets, production = millions/jour

---

## 🤝 Support et Questions

En cas de problème :

1. Consulter la section [Troubleshooting](#troubleshooting)
2. Vérifier les logs : `docker-compose logs <service>`
3. Valider la configuration `.env` et `docker-compose.yml`
4. S'assurer que Docker est opérationnel

---

**Dernière mise à jour :** Décembre 2025  
**Version :** 1.0.0  
**Auteur :** OpenClassroom - Data Engineer Track
