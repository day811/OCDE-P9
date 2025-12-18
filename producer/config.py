"""
Producer configuration management.
Loads environment variables from .env and allows CLI argument overrides.
"""

import os
import argparse
from dotenv import load_dotenv

# Load .env from parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


class ProducerConfig:
    """Producer configuration container."""
    
    def __init__(self):
        self.redpanda_broker = os.getenv('REDPANDA_BROKER_LOCAL', 'localhost:9092')
        self.topic_name = os.getenv('TOPIC_NAME', 'client_tickets')
        self.producer_rate = int(os.getenv('PRODUCER_RATE', '10'))
        self.producer_timeout = int(os.getenv('PRODUCER_TIMEOUT', '30'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    def __repr__(self):
        return (
            f"ProducerConfig(broker={self.redpanda_broker}, "
            f"topic={self.topic_name}, rate={self.producer_rate})"
        )


def parse_producer_args():
    """Parse command-line arguments and merge with environment variables."""
    parser = argparse.ArgumentParser(
        description='Ticket producer with Redpanda'
    )
    parser.add_argument(
        '--broker',
        type=str,
        help='Redpanda broker address (override .env)'
    )
    parser.add_argument(
        '--topic',
        type=str,
        help='Topic name (override .env)'
    )
    parser.add_argument(
        '--rate',
        type=int,
        help='Tickets per second (override .env)'
    )
    
    args = parser.parse_args()
    
    # Create config from .env
    config = ProducerConfig()
    
    # Apply CLI overrides
    if args.broker:
        config.redpanda_broker = args.broker
    if args.topic:
        config.topic_name = args.topic
    if args.rate:
        config.producer_rate = args.rate
    
    return config
