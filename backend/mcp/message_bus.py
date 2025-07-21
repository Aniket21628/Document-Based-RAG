import asyncio
from typing import Dict, List, Callable, Optional
from mcp.message_types import MCPMessage, MessageType
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MessageBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[MCPMessage] = []
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
    def subscribe(self, agent_name: str, message_types: List[MessageType], callback: Callable):
        """Subscribe an agent to specific message types"""
        key = f"{agent_name}:{','.join([mt.value for mt in message_types])}"
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(callback)
        logger.info(f"Agent {agent_name} subscribed to {message_types}")
    
    async def publish(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Publish a message to all subscribed agents"""
        self.message_history.append(message)
        logger.info(f"Publishing message: {message.type.value} from {message.sender} to {message.receiver}")
        
        # Find subscribers for this message type and receiver
        for key, callbacks in self.subscribers.items():
            agent_name, msg_types = key.split(':', 1)
            if (agent_name == message.receiver and 
                message.type.value in msg_types.split(',')):
                
                for callback in callbacks:
                    try:
                        response = await callback(message)
                        if response:
                            return response
                    except Exception as e:
                        logger.error(f"Error in callback for {agent_name}: {str(e)}")
        
        return None
    
    async def request_response(self, message: MCPMessage, timeout: int = 30) -> MCPMessage:
        """Send a message and wait for a response"""
        future = asyncio.Future()
        self.pending_responses[message.message_id] = future
        
        try:
            response = await self.publish(message)
            if response:
                return response
            else:
                # Wait for async response
                return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response to message {message.message_id}")
            raise
        finally:
            if message.message_id in self.pending_responses:
                del self.pending_responses[message.message_id]
    
    def get_message_history(self, trace_id: Optional[str] = None) -> List[MCPMessage]:
        """Get message history, optionally filtered by trace_id"""
        if trace_id:
            return [msg for msg in self.message_history if msg.trace_id == trace_id]
        return self.message_history[-50:]  # Return last 50 messages

# Global message bus instance
message_bus = MessageBus()