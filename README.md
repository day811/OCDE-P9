# OCDE-P9
Project #9 in OpenClassrooms DataEngineer Cursus 
# Exercice 2 : Gestion de Tickets Clients avec Redpanda et PySpark

## Vue d'ensemble

POC (Proof of Concept) d'un pipeline ETL temps réel pour la gestion de tickets clients.

**Architecture:**
- **Producteur** : Génère des tickets clients aléatoires
- **Broker** : Redpanda (Kafka-compatible) pour le streaming
- **Processeur** : PySpark pour transformation et analyse
- **Sortie** : Fichiers Parquet/JSON avec insights

## Flux de données

\`\`\`mermaid
graph LR
    A["Ticket Generator<br/>(Python)"] -->|JSON| B["Redpanda<br/>Topic: client_tickets"]
    B -->|Streaming| C["PySpark<br/>Processor"]
    C -->|Transform| D["Add Support Team<br/>Calculate Metrics"]
    D -->|Export| E["Parquet/JSON<br/>data/output/"]
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#fce4ec
\`\`\`

## Démarrage rapide

### Prérequis
- Docker & Docker Compose
- Linux Debian (VSCode)
- Port 9092 disponible (Redpanda)

### Installation

\`\`\`bash
# Cloner et naviguer au répertoire
cd projet_exercice2

# Construire et lancer les conteneurs
docker-compose up --build

# En arrière-plan
docker-compose up -d --build
\`\`\`

### Vérifier le statut

\`\`\`bash
# Lister les conteneurs
docker-compose ps

# Logs producteur
docker-compose logs -f producer

# Logs processeur
docker-compose logs -f processor

# Logs Redpanda
docker-compose logs -f redpanda
\`\`\`

## Utilisation

### Configuration (.env)

Paramètres clés dans \`.env\`:

\`\`\`env
REDPANDA_BROKER_LOCAL=localhost:9092  # Adresse broker
TOPIC_NAME=client_tickets             # Topic Kafka
PRODUCER_RATE=10                      # Tickets/sec
SPARK_MEMORY=2g                       # Mémoire Spark
OUTPUT_FORMAT=parquet                 # Format export
\`\`\`

### Surcharge par argument CLI

**Producteur:**
\`\`\`bash
python producer/ticket_producer.py --broker localhost:9092 --rate 20
\`\`\`

**Processeur:**
\`\`\`bash
python processor/spark_processor.py --memory 4g --output-format json
\`\`\`

## Structure des données

### Ticket (Input)

\`\`\`json
{
  "ticket_id": "uuid",
  "client_id": "CLIENT_1234",
  "created_at": "2025-12-18T14:30:00Z",
  "request": "Unable to reset password",
  "request_type": "account|billing|technical|general",
  "priority": "low|medium|high|critical"
}
\`\`\`

### Ticket enrichi (Output)

\`\`\`json
{
  "ticket_id": "uuid",
  "client_id": "CLIENT_1234",
  "created_at": "2025-12-18T14:30:00Z",
  "request": "Unable to reset password",
  "request_type": "account",
  "priority": "high",
  "assigned_team": "Account Management"
}
\`\`\`

## Résultats d'analyse

Fichiers générés dans \`data/output/\`:

- **tickets_with_assignment/** : Tous les tickets avec équipe assignée
- **metrics/** : Métriques globales (total, par type, par priorité, clients uniques)
- **tickets_by_type/** : Comptage par type de demande
- **tickets_by_priority/** : Comptage par priorité
- **high_priority_tickets/** : Tickets haute priorité/critiques

## Architecture du code

\`\`\`
producer/
  ├── ticket_producer.py      # Point d'entrée
  ├── config.py               # Gestion .env + CLI
  ├── producer.py             # Classe ProductionManager
  ├── ticket.py               # Classe Ticket + validation
  └── requirements.txt

processor/
  ├── spark_processor.py      # Point d'entrée
  ├── config.py               # Gestion .env + CLI
  ├── processor.py            # Classe SparkProcessor
  ├── transformations.py      # Classe Transformations
  └── requirements.txt

data/output/                  # Résultats export
\`\`\`

## Arrêt et nettoyage

\`\`\`bash
# Arrêter les conteneurs
docker-compose down

# Arrêter et supprimer volumes
docker-compose down -v
\`\`\`

## Points clés

| Composant | Description |
|-----------|-------------|
| **Producteur** | Génère tickets aléatoires, publie via Kafka/Redpanda |
| **Redpanda** | Broker Kafka-compatible, persiste données streaming |
| **Processeur** | Lit Redpanda avec Spark, transforme, agrège, exporte |
| **Configuration** | .env + surcharge CLI pour flexibilité |
| **Sortie** | Parquet/JSON pour visualisation/BI ultérieure |

## Troubleshooting

### Redpanda ne démarre pas
\`\`\`bash
docker-compose logs redpanda
# Vérifier ports disponibles, espace disque
\`\`\`

### Producteur ne se connecte pas
\`\`\`bash
# Tester connectivité
docker exec redpanda_exercice2 rpk cluster info
# Ou vérifier broker dans .env
\`\`\`

### Processeur pas de données
\`\`\`bash
# Attendre quelques secondes, vérifier logs producteur
docker-compose logs producer
# Vérifier topic existe
docker exec redpanda_exercice2 rpk topic list
\`\`\`

## Notes

- Pipeline conçu pour démonstration/POC
- Données de test générées aléatoirement
- Résultats exportés en Parquet (format columnar optimisé)
- Extensible pour données réelles (MySQL, API, etc.)
