from abc import ABC, abstractmethod
from typing import Any, Dict
import asyncio
import logging
from mcp.message_bus import message_bus, MCPMessage

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.is_running = False
    
    async def start(self):
        """Start the agent"""
        self.is_running = True
        await message_bus.subscribe(self.name, self.handle_message)
        logger.info(f"Agent {self.name} started")
    
    async def stop(self):
        """Stop the agent"""
        self.is_running = False
        logger.info(f"Agent {self.name} stopped")
    
    @abstractmethod
    async def handle_message(self, message: MCPMessage):
        """Handle incoming MCP messages"""
        pass
    
    async def send_message(self, receiver: str, message_type, payload: Dict[str, Any], trace_id: str):
        """Send an MCP message"""
        message = MCPMessage.create(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            payload=payload,
            trace_id=trace_id
        )
        await message_bus.publish(message)