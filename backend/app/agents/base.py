"""
Base agent class and shared agent functionality
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    id: str
    sender: str
    recipient: str
    content: Any
    message_type: str
    timestamp: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResult:
    """Result structure for agent operations"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    execution_time: float = 0.0
    tokens_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, model_wrapper=None):
        self.name = name
        self.model_wrapper = model_wrapper
        self.status = AgentStatus.IDLE
        self.message_history: List[AgentMessage] = []
        self.execution_stats = {
            "total_executions": 0,
            "total_time": 0.0,
            "total_tokens": 0,
            "success_count": 0,
            "error_count": 0
        }
        self.logger = structlog.get_logger(f"agent.{name}")
    
    @abstractmethod
    async def process(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResult:
        """Process input and return result"""
        pass
    
    async def execute(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResult:
        """Execute agent with error handling and stats tracking"""
        self.status = AgentStatus.PROCESSING
        start_time = time.time()
        
        try:
            self.logger.info("Starting agent execution", input_type=type(input_data).__name__)
            
            result = await self.process(input_data, context or {})
            
            # Update stats
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            self.execution_stats["total_executions"] += 1
            self.execution_stats["total_time"] += execution_time
            self.execution_stats["total_tokens"] += result.tokens_used
            
            if result.success:
                self.status = AgentStatus.COMPLETED
                self.execution_stats["success_count"] += 1
                self.logger.info(
                    "Agent execution completed successfully",
                    execution_time=f"{execution_time:.2f}s",
                    tokens_used=result.tokens_used
                )
            else:
                self.status = AgentStatus.ERROR
                self.execution_stats["error_count"] += 1
                self.logger.error(
                    "Agent execution failed",
                    error=result.error,
                    execution_time=f"{execution_time:.2f}s"
                )
            
            return result
            
        except asyncio.TimeoutError:
            self.status = AgentStatus.TIMEOUT
            self.execution_stats["error_count"] += 1
            self.logger.error("Agent execution timed out")
            return AgentResult(
                success=False,
                error="Execution timed out",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.execution_stats["error_count"] += 1
            self.logger.error("Agent execution failed", error=str(e))
            return AgentResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def add_message(self, message: AgentMessage):
        """Add message to history"""
        self.message_history.append(message)
        
        # Keep history size manageable
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-50:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        stats = self.execution_stats.copy()
        stats.update({
            "name": self.name,
            "status": self.status.value,
            "message_count": len(self.message_history),
            "average_execution_time": (
                stats["total_time"] / stats["total_executions"]
                if stats["total_executions"] > 0 else 0.0
            ),
            "success_rate": (
                stats["success_count"] / stats["total_executions"]
                if stats["total_executions"] > 0 else 0.0
            )
        })
        return stats
    
    def reset_stats(self):
        """Reset execution statistics"""
        self.execution_stats = {
            "total_executions": 0,
            "total_time": 0.0,
            "total_tokens": 0,
            "success_count": 0,
            "error_count": 0
        }
        self.message_history.clear()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health"""
        return {
            "name": self.name,
            "status": self.status.value,
            "healthy": self.status != AgentStatus.ERROR,
            "model_available": self.model_wrapper is not None
        }


class AgentCommunicator:
    """Handles communication between agents"""
    
    def __init__(self):
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.subscribers: Dict[str, List[BaseAgent]] = {}
    
    def subscribe(self, topic: str, agent: BaseAgent):
        """Subscribe agent to topic"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(agent)
    
    async def publish(self, topic: str, message: AgentMessage):
        """Publish message to topic subscribers"""
        if topic in self.subscribers:
            for agent in self.subscribers[topic]:
                agent.add_message(message)
    
    async def send_direct(self, message: AgentMessage, recipient: BaseAgent):
        """Send direct message to agent"""
        recipient.add_message(message)