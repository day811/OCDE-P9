"""
Main entry point for ticket processor.
Reads, transforms, and exports ticket data from Redpanda.
"""

import logging
import time
from config import parse_processor_args # pyright: ignore[reportAttributeAccessIssue]
from spark_processor import SparkProcessor # pyright: ignore[reportAttributeAccessIssue]


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main processor loop."""
    config = parse_processor_args()
    logger.info(f"Starting processor with config: {config}")
    
    processor = SparkProcessor(
        broker=config.redpanda_broker,
        topic=config.topic_name,
        memory=config.spark_memory,
        executor_cores=config.spark_executor_cores
    )
    
    # Initialize Spark
    if not processor.init_spark():
        logger.error("Failed to initialize Spark. Exiting.")
        return
    
    try:
        # Give producer time to publish tickets
        logger.info("Waiting 10 seconds for tickets to accumulate...")
        time.sleep(10)
        
        # Read tickets from Redpanda
        logger.info("Reading tickets from Redpanda...")
        df = processor.read_tickets_batch(max_events=10000)
        
        if df is None or df.count() == 0:
            logger.warning("No tickets found. Nothing to process.")
            processor.close()
            return
        
        logger.info(f"Processing {df.count()} tickets...")
        
        # Process
        results = processor.process(df)
        
        if not results:
            logger.error("Processing failed. Exiting.")
            processor.close()
            return
        
        # Display some results
        logger.info("\n=== METRICS ===")
        results['metrics'].show(truncate=False)
        
        logger.info("\n=== TICKETS BY TYPE ===")
        results['by_type'].show(truncate=False)
        
        logger.info("\n=== TICKETS BY PRIORITY ===")
        results['by_priority'].show(truncate=False)
        
        # Export
        logger.info("Exporting results...")
        processor.export_results(
            results,
            output_path=config.output_path,
            format=config.output_format
        )
        
        logger.info("Processing completed successfully")
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        processor.close()


if __name__ == '__main__':
    main()
