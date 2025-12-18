"""
Processor configuration management.
Loads environment variables from .env and allows CLI argument overrides.
"""

import os
import argparse
from dotenv import load_dotenv

# Load .env from parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


class ProcessorConfig:
    """Processor configuration container."""
    
    def __init__(self):
        self.redpanda_broker = os.getenv('REDPANDA_BROKER_LOCAL', 'localhost:9092')
        self.topic_name = os.getenv('TOPIC_NAME', 'client_tickets')
        self.spark_memory = os.getenv('SPARK_MEMORY', '2g')
        self.spark_executor_cores = int(os.getenv('SPARK_EXECUTOR_CORES', '2'))
        self.output_format = os.getenv('OUTPUT_FORMAT', 'parquet')
        self.output_path = os.getenv('OUTPUT_PATH', './data/output')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    def __repr__(self):
        return (
            f"ProcessorConfig(broker={self.redpanda_broker}, "
            f"topic={self.topic_name}, output_format={self.output_format})"
        )


def parse_processor_args():
    """Parse command-line arguments and merge with environment variables."""
    parser = argparse.ArgumentParser(
        description='Ticket processor with PySpark'
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
        '--memory',
        type=str,
        help='Spark driver memory (override .env)'
    )
    parser.add_argument(
        '--output-format',
        type=str,
        help='Output format: json or parquet (override .env)'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        help='Output path (override .env)'
    )
    
    args = parser.parse_args()
    
    # Create config from .env
    config = ProcessorConfig()
    
    # Apply CLI overrides
    if args.broker:
        config.redpanda_broker = args.broker
    if args.topic:
        config.topic_name = args.topic
    if args.memory:
        config.spark_memory = args.memory
    if args.output_format:
        config.output_format = args.output_format
    if args.output_path:
        config.output_path = args.output_path
    
    return config
