"""
Ticket data model and validation.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class Ticket:
    """
    Represents a client support ticket.
    
    Fields:
        ticket_id: Unique ticket identifier
        client_id: Client identifier
        created_at: Ticket creation timestamp
        request: Description of the client request
        request_type: Category of request (billing, technical, account, general)
        priority: Priority level (low, medium, high, critical)
    """
    
    VALID_TYPES = {'billing', 'technical', 'account', 'general'}
    VALID_PRIORITIES = {'low', 'medium', 'high', 'critical'}
    
    def __init__(
        self,
        ticket_id: str,
        client_id: str,
        request: str,
        request_type: str,
        priority: str,
        created_at: Optional[str] = None
    ):
        """Initialize ticket with validation."""
        self.ticket_id = ticket_id
        self.client_id = client_id
        self.request = request
        self.request_type = request_type
        self.priority = priority
        self.created_at = created_at if created_at is not None else datetime.utcnow().isoformat()
        
        self._validate()
    
    def _validate(self):
        """Validate ticket fields."""
        if self.request_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid request_type: {self.request_type}. "
                f"Must be one of {self.VALID_TYPES}"
            )
        if self.priority not in self.VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority: {self.priority}. "
                f"Must be one of {self.VALID_PRIORITIES}"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ticket to dictionary."""
        return {
            'ticket_id': self.ticket_id,
            'client_id': self.client_id,
            'created_at': self.created_at,
            'request': self.request,
            'request_type': self.request_type,
            'priority': self.priority
        }
    
    def to_json(self) -> str:
        """Convert ticket to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ticket':
        """Create ticket from dictionary."""
        return cls(
            ticket_id=data['ticket_id'],
            client_id=data['client_id'],
            request=data['request'],
            request_type=data['request_type'],
            priority=data['priority'],
            created_at=data.get('created_at')
        )
    
    def __repr__(self):
        return (
            f"Ticket(id={self.ticket_id}, client={self.client_id}, "
            f"type={self.request_type}, priority={self.priority})"
        )
