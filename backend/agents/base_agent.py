from abc import ABC, abstractmethod
from typing import List, Optional
from mcp.message_types import MCPMessage, MessageType
from mcp.message_bus import message_bus
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.subscribed_messages: List[MessageType] = []
    
    @abstractmethod
    async def process_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Process incoming message and return response if needed"""
        pass
    
    def subscribe_to_messages(self, message_types: List[MessageType]):
        """Subscribe to specific message types"""
        self.subscribed_messages = message_types
        message_bus.subscribe(self.name, message_types, self.process_message)
        logger.info(f"{self.name} subscribed to {[mt.value for mt in message_types]}")
    
    async def send_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Send message through the message bus"""
        return await message_bus.publish(message)
    
    async def request_response(self, message: MCPMessage, timeout: int = 30) -> MCPMessage:
        """Send message and wait for response"""
        return await message_bus.request_response(message, timeout)