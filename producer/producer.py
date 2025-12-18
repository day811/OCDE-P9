"""
Ticket producer for Redpanda.
Handles connection and message publishing.
"""

import logging
import time
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class ProductionManager:
    """
    Manages ticket production to Redpanda.
    
    Handles:
        - Connection to Redpanda broker
        - Message serialization
        - Error handling and reconnection
        - Resource cleanup
    """
    
    def __init__(self, broker: str, topic: str, timeout: int = 30):
        """
        Initialize production manager.
        
        Args:
            broker: Redpanda broker address (e.g., 'localhost:9092')
            topic: Topic name for publishing
            timeout: Connection timeout in seconds
        """
        self.broker = broker
        self.topic = topic
        self.timeout = timeout
        self.producer: Optional[KafkaProducer] = None
    
    def connect(self) -> bool:
        """
        Connect to Redpanda broker.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[self.broker],
                value_serializer=lambda v: v.encode('utf-8'),
                request_timeout_ms=self.timeout * 1000,
                retries=3
            )
            logger.info(f"Connected to Redpanda: {self.broker}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redpanda: {e}")
            return False
    
    def publish_ticket(self, ticket_json: str) -> bool:
        """
        Publish a ticket message to Redpanda.
        
        Args:
            ticket_json: JSON serialized ticket
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("Producer not connected")
            return False
        
        try:
            future = self.producer.send(self.topic, value=ticket_json)
            record_metadata = future.get(timeout=self.timeout)
            logger.debug(
                f"Published ticket to {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True
        except KafkaError as e:
            logger.error(f"Failed to publish ticket: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing ticket: {e}")
            return False
    
    def close(self):
        """Close producer connection and flush pending messages."""
        if self.producer:
            try:
                self.producer.flush(timeout=self.timeout)
                self.producer.close()
                logger.info("Producer closed")
            except Exception as e:
                logger.error(f"Error closing producer: {e}")
