"""
Main entry point for ticket producer.
Generates random tickets and publishes to Redpanda.
"""

import logging
import time
import random
import uuid
from config import parse_producer_args # pyright: ignore[reportAttributeAccessIssue]
from ticket import Ticket
from producer import ProductionManager # pyright: ignore[reportAttributeAccessIssue]


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample data for random generation
REQUEST_TYPES = ['billing', 'technical', 'account', 'general']
PRIORITIES = ['low', 'medium', 'high', 'critical']
SAMPLE_REQUESTS = [
    'Unable to reset password',
    'Invoice discrepancy',
    'Service not working',
    'Update account information',
    'Payment method issue',
    'Feature request',
    'Bug report',
    'Account locked'
]


def generate_random_ticket() -> Ticket:
    """Generate a random ticket for testing."""
    return Ticket(
        ticket_id=str(uuid.uuid4()),
        client_id=f"CLIENT_{random.randint(1000, 9999)}",
        request=random.choice(SAMPLE_REQUESTS),
        request_type=random.choice(REQUEST_TYPES),
        priority=random.choice(PRIORITIES)
    )


def main():
    """Main producer loop."""
    config = parse_producer_args()
    logger.info(f"Starting producer with config: {config}")
    
    manager = ProductionManager(
        broker=config.redpanda_broker,
        topic=config.topic_name,
        timeout=config.producer_timeout
    )
    
    # Connect to Redpanda
    if not manager.connect():
        logger.error("Failed to connect to Redpanda. Exiting.")
        return
    
    try:
        ticket_count = 0
        logger.info(f"Publishing tickets at rate {config.producer_rate}/sec")
        
        while True:
            # Generate and publish a ticket
            ticket = generate_random_ticket()
            ticket_json = ticket.to_json()
            
            if manager.publish_ticket(ticket_json):
                ticket_count += 1
                if ticket_count % 10 == 0:
                    logger.info(f"Published {ticket_count} tickets")
            else:
                logger.warning("Failed to publish ticket, continuing...")
            
            # Rate limiting
            time.sleep(1.0 / config.producer_rate)
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        manager.close()
        logger.info(f"Producer stopped. Total tickets published: {ticket_count}")


if __name__ == '__main__':
    main()
