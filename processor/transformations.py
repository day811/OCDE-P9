"""
Data transformations and business logic.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, when, count, countDistinct, 
    avg, max, min, struct, to_json
)


class Transformations:
    """
    Encapsulates all data transformation logic for ticket processing.
    """
    
    # Support team assignment mapping
    SUPPORT_TEAMS = {
        'billing': 'Billing Team',
        'technical': 'Technical Support',
        'account': 'Account Management',
        'general': 'General Support'
    }
    
    @staticmethod
    def add_support_team(df: DataFrame) -> DataFrame:
        """
        Assign support team based on request type.
        
        Args:
            df: Input DataFrame with 'request_type' column
        
        Returns:
            DataFrame with new 'assigned_team' column
        """
        return df.withColumn(
            'assigned_team',
            when(col('request_type') == 'billing', 'Billing Team')
            .when(col('request_type') == 'technical', 'Technical Support')
            .when(col('request_type') == 'account', 'Account Management')
            .otherwise('General Support')
        )
    
    @staticmethod
    def calculate_ticket_metrics(df: DataFrame) -> DataFrame:
        """
        Calculate aggregate metrics for all tickets.
        
        Metrics:
            - Total ticket count
            - Count by type
            - Count by priority
            - Average per type
        
        Args:
            df: Input DataFrame with tickets
        
        Returns:
            DataFrame with computed metrics
        """
        metrics = df.select(
            count('*').alias('total_tickets'),
            count(
                when(col('request_type') == 'billing', 1)
            ).alias('billing_count'),
            count(
                when(col('request_type') == 'technical', 1)
            ).alias('technical_count'),
            count(
                when(col('request_type') == 'account', 1)
            ).alias('account_count'),
            count(
                when(col('request_type') == 'general', 1)
            ).alias('general_count'),
            count(
                when(col('priority') == 'critical', 1)
            ).alias('critical_priority_count'),
            countDistinct('client_id').alias('unique_clients')
        )
        
        return metrics
    
    @staticmethod
    def group_by_type(df: DataFrame) -> DataFrame:
        """
        Group tickets by request type with counts.
        
        Args:
            df: Input DataFrame
        
        Returns:
            DataFrame grouped by type with counts
        """
        return df.groupBy('request_type').agg(
            count('*').alias('count')
        ).orderBy(col('count').desc())
    
    @staticmethod
    def group_by_priority(df: DataFrame) -> DataFrame:
        """
        Group tickets by priority with counts.
        
        Args:
            df: Input DataFrame
        
        Returns:
            DataFrame grouped by priority with counts
        """
        return df.groupBy('priority').agg(
            count('*').alias('count')
        ).orderBy(col('count').desc())
    
    @staticmethod
    def high_priority_tickets(df: DataFrame) -> DataFrame:
        """
        Filter high priority and critical tickets.
        
        Args:
            df: Input DataFrame
        
        Returns:
            DataFrame with only high/critical tickets
        """
        return df.filter(
            (col('priority') == 'critical') | (col('priority') == 'high')
        )
