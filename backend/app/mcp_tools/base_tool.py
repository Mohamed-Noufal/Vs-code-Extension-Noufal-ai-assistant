"""
Base MCP tool interface and common functionality
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class ToolResult:
    """Result structure for tool operations"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseMCPTool(ABC):
    """Base class for MCP tools"""
    
    def __init__(self, name: str):
        self.name = name
        self.workspace_dir = Path(settings.WORKSPACE_DIR)
        self.logger = structlog.get_logger(f"mcp_tool.{name}")
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }
    
    @abstractmethod
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute tool operation"""
        pass
    
    async def safe_execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute with error handling and stats tracking"""
        start_time = time.time()
        
        try:
            self.logger.debug("Executing tool operation", operation=operation)
            
            result = await self.execute(operation, **kwargs)
            
            # Update stats
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            self.execution_stats["total_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            
            if result.success:
                self.execution_stats["successful_executions"] += 1
                self.logger.debug(
                    "Tool operation completed successfully",
                    operation=operation,
                    execution_time=f"{execution_time:.3f}s"
                )
            else:
                self.execution_stats["failed_executions"] += 1
                self.logger.warning(
                    "Tool operation failed",
                    operation=operation,
                    error=result.error,
                    execution_time=f"{execution_time:.3f}s"
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            
            self.logger.error(
                "Tool operation failed with exception",
                operation=operation,
                error=str(e),
                execution_time=f"{execution_time:.3f}s"
            )
            
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def validate_path(self, path: str) -> bool:
        """Validate that path is within workspace"""
        try:
            full_path = (self.workspace_dir / path).resolve()
            workspace_path = self.workspace_dir.resolve()
            
            # Check if path is within workspace
            return str(full_path).startswith(str(workspace_path))
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics"""
        stats = self.execution_stats.copy()
        stats.update({
            "name": self.name,
            "success_rate": (
                stats["successful_executions"] / stats["total_executions"]
                if stats["total_executions"] > 0 else 0.0
            ),
            "average_execution_time": (
                stats["total_execution_time"] / stats["total_executions"]
                if stats["total_executions"] > 0 else 0.0
            )
        })
        return stats
    
    def is_allowed_file_type(self, file_path: str) -> bool:
        """Check if file type is allowed"""
        path = Path(file_path)
        return path.suffix.lower() in settings.ALLOWED_EXTENSIONS
    
    def is_within_size_limit(self, content: str) -> bool:
        """Check if content is within size limit"""
        return len(content.encode('utf-8')) <= settings.MAX_FILE_SIZE