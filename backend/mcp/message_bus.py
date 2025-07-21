import asyncio
from typing import Dict, List, Callable, Any
from .message_types import MCPMessage, MessageType
import logging

logger = logging.getLogger(__name__)

class MCPMessageBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[MCPMessage] = []
        self._lock = asyncio.Lock()
    
    async def subscribe(self, agent_name: str, callback: Callable[[MCPMessage], Any]):
        """Subscribe an agent to receive messages"""
        async with self._lock:
            if agent_name not in self.subscribers:
                self.subscribers[agent_name] = []
            self.subscribers[agent_name].append(callback)
    
    async def publish(self, message: MCPMessage):
        """Publish a message to the bus"""
        async with self._lock:
            self.message_history.append(message)
            logger.info(f"Message published: {message.sender} -> {message.receiver} ({message.type.value})")
            
            # Deliver to specific receiver
            if message.receiver in self.subscribers:
                for callback in self.subscribers[message.receiver]:
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"Error delivering message to {message.receiver}: {e}")
    
    def get_message_history(self, trace_id: str) -> List[MCPMessage]:
        """Get message history for a specific trace"""
        return [msg for msg in self.message_history if msg.trace_id == trace_id]

# Global message bus instance
message_bus = MCPMessageBus()