from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum

class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    BOUNCED = "bounced"

class NotificationResult:
    def __init__(
        self,
        success: bool,
        message_id: Optional[str] = None,
        status: NotificationStatus = NotificationStatus.PENDING,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.message_id = message_id
        self.status = status
        self.error = error
        self.metadata = metadata or {}

class BaseNotificationProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialize()
    
    @abstractmethod
    def initialize(self) -> None:
        pass
    
    @abstractmethod
    async def send(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        **kwargs
    ) -> NotificationResult:
        pass
    
    @abstractmethod
    async def send_template(
        self,
        to: str | List[str],
        template_id: str,
        template_data: Dict[str, Any],
        **kwargs
    ) -> NotificationResult:
        pass
    
    @abstractmethod
    async def get_status(self, message_id: str) -> NotificationStatus:
        pass