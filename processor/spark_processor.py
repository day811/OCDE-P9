"""
Spark processor for ticket data.
Handles reading, processing, and exporting ticket data.
"""

import logging
import os
from typing import Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType
)
from transformations import Transformations

logger = logging.getLogger(__name__)


class SparkProcessor:
    """
    Manages Spark session and ticket processing pipeline.
    
    Handles:
        - Spark session initialization
        - Reading from Redpanda (Kafka)
        - Data transformation
        - Result export
    """
    
    def __init__(
        self,
        broker: str,
        topic: str,
        memory: str = '2g',
        executor_cores: int = 2
    ):
        """
        Initialize processor.
        
        Args:
            broker: Redpanda broker address
            topic: Topic to read from
            memory: Spark driver memory
            executor_cores: Number of executor cores
        """
        self.broker = broker
        self.topic = topic
        self.memory = memory
        self.executor_cores = executor_cores
        self.spark: Optional[SparkSession] = None
    
    def init_spark(self) -> bool:
        """
        Initialize Spark session.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.spark = SparkSession.builder \
                .appName("TicketProcessor") \
                .config("spark.driver.memory", self.memory) \
                .config("spark.executor.cores", self.executor_cores) \
                .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
                .getOrCreate() 
            
            # Set Spark log level
            self.spark.sparkContext.setLogLevel("WARN") # pyright: ignore[reportOptionalMemberAccess]
            
            logger.info("Spark session initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Spark: {e}")
            return False
    
    def read_tickets_batch(self, max_events: int = 10000) -> Optional[DataFrame]:
        """
        Read tickets from Redpanda in batch mode (for testing/demo).
        
        Args:
            max_events: Maximum events to read
        
        Returns:
            DataFrame with tickets or None if error
        """
        if not self.spark:
            logger.error("Spark session not initialized")
            return None
        
        try:
            df = self.spark.read \
                .format("kafka") \
                .option("kafka.bootstrap.servers", self.broker) \
                .option("subscribe", self.topic) \
                .option("startingOffsets", "earliest") \
                .option("maxOffsetsPerTrigger", max_events) \
                .load()
            
            # Parse JSON value
            from pyspark.sql.functions import from_json, col
            
            schema = StructType([
                StructField("ticket_id", StringType()),
                StructField("client_id", StringType()),
                StructField("created_at", StringType()),
                StructField("request", StringType()),
                StructField("request_type", StringType()),
                StructField("priority", StringType())
            ])
            
            df = df.select(
                from_json(col("value").cast("string"), schema).alias("ticket")
            ).select("ticket.*")
            
            logger.info(f"Read {df.count()} tickets from Redpanda")
            return df
        except Exception as e:
            logger.error(f"Failed to read tickets: {e}")
            return None
    
    def process(self, df: DataFrame) -> dict:
        """
        Apply transformations and generate insights.
        
        Args:
            df: Input DataFrame with tickets
        
        Returns:
            Dictionary with results (dataframes and metrics)
        """
        try:
            # Add support team assignment
            df_with_team = Transformations.add_support_team(df)
            
            # Generate metrics
            metrics = Transformations.calculate_ticket_metrics(df_with_team)
            
            # Group by type and priority
            by_type = Transformations.group_by_type(df_with_team)
            by_priority = Transformations.group_by_priority(df_with_team)
            
            # High priority tickets
            high_priority = Transformations.high_priority_tickets(df_with_team)
            
            logger.info("Processing completed successfully")
            
            return {
                'tickets': df_with_team,
                'metrics': metrics,
                'by_type': by_type,
                'by_priority': by_priority,
                'high_priority': high_priority
            }
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {}
    
    def export_results(self, results: dict, output_path: str, format: str = 'parquet'):
        """
        Export processing results to disk.
        
        Args:
            results: Dictionary of DataFrames to export
            output_path: Base output directory
            format: Output format ('parquet' or 'json')
        """
        if not results:
            logger.error("No results to export")
            return
        
        try:
            os.makedirs(output_path, exist_ok=True)
            
            # Export main tickets with assignments
            if 'tickets' in results:
                output_file = os.path.join(output_path, 'tickets_with_assignment')
                results['tickets'].coalesce(1).write \
                    .mode("overwrite") \
                    .format(format) \
                    .save(output_file)
                logger.info(f"Exported tickets to {output_file}")
            
            # Export metrics
            if 'metrics' in results:
                output_file = os.path.join(output_path, 'metrics')
                results['metrics'].coalesce(1).write \
                    .mode("overwrite") \
                    .format(format) \
                    .save(output_file)
                logger.info(f"Exported metrics to {output_file}")
            
            # Export by type
            if 'by_type' in results:
                output_file = os.path.join(output_path, 'tickets_by_type')
                results['by_type'].coalesce(1).write \
                    .mode("overwrite") \
                    .format(format) \
                    .save(output_file)
                logger.info(f"Exported by_type to {output_file}")
            
            # Export by priority
            if 'by_priority' in results:
                output_file = os.path.join(output_path, 'tickets_by_priority')
                results['by_priority'].coalesce(1).write \
                    .mode("overwrite") \
                    .format(format) \
                    .save(output_file)
                logger.info(f"Exported by_priority to {output_file}")
            
            # Export high priority
            if 'high_priority' in results:
                output_file = os.path.join(output_path, 'high_priority_tickets')
                results['high_priority'].coalesce(1).write \
                    .mode("overwrite") \
                    .format(format) \
                    .save(output_file)
                logger.info(f"Exported high_priority to {output_file}")
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
    
    def close(self):
        """Close Spark session."""
        if self.spark:
            try:
                self.spark.stop()
                logger.info("Spark session closed")
            except Exception as e:
                logger.error(f"Error closing Spark: {e}")
