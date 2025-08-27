"""
WebSocket Handler for Real-time Communication
"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

import structlog

from app.orchestrator.workflow import WorkflowManager
from app.mcp_tools.fs_tool import FileSystemTool
from app.mcp_tools.run_tool import CommandExecutionTool

logger = structlog.get_logger(__name__)

# Create WebSocket router
websocket_router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.workflow_subscriptions: Dict[str, Set[str]] = {}  # workflow_id -> {connection_ids}
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info("WebSocket connected", connection_id=connection_id)
    
    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from workflow subscriptions
        for workflow_id, subscribers in self.workflow_subscriptions.items():
            subscribers.discard(connection_id)
        
        logger.info("WebSocket disconnected", connection_id=connection_id)
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error("Failed to send message", connection_id=connection_id, error=str(e))
                self.disconnect(connection_id)
    
    async def broadcast_to_workflow(self, message: Dict[str, Any], workflow_id: str):
        """Broadcast message to all subscribers of a workflow"""
        if workflow_id in self.workflow_subscriptions:
            subscribers = list(self.workflow_subscriptions[workflow_id])
            for connection_id in subscribers:
                await self.send_personal_message(message, connection_id)
    
    def subscribe_to_workflow(self, connection_id: str, workflow_id: str):
        """Subscribe connection to workflow updates"""
        if workflow_id not in self.workflow_subscriptions:
            self.workflow_subscriptions[workflow_id] = set()
        self.workflow_subscriptions[workflow_id].add(connection_id)
        logger.info("Subscribed to workflow", connection_id=connection_id, workflow_id=workflow_id)
    
    def unsubscribe_from_workflow(self, connection_id: str, workflow_id: str):
        """Unsubscribe connection from workflow updates"""
        if workflow_id in self.workflow_subscriptions:
            self.workflow_subscriptions[workflow_id].discard(connection_id)
            if not self.workflow_subscriptions[workflow_id]:
                del self.workflow_subscriptions[workflow_id]


# Global connection manager
manager = ConnectionManager()


@websocket_router.websocket("/ws/{connection_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    """Main WebSocket endpoint"""
    await manager.connect(websocket, connection_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": time.time(),
            "message": "Connected to Multi-Agent Development System"
        }, connection_id)
        
        # Message handling loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle message
                await handle_websocket_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected normally", connection_id=connection_id)
                break
            except json.JSONDecodeError as e:
                await manager.send_personal_message({
                    "type": "error",
                    "error": f"Invalid JSON: {str(e)}",
                    "timestamp": time.time()
                }, connection_id)
            except Exception as e:
                logger.error("WebSocket message handling error", connection_id=connection_id, error=str(e))
                await manager.send_personal_message({
                    "type": "error",
                    "error": f"Message handling failed: {str(e)}",
                    "timestamp": time.time()
                }, connection_id)
    
    except Exception as e:
        logger.error("WebSocket connection error", connection_id=connection_id, error=str(e))
    finally:
        manager.disconnect(connection_id)


async def handle_websocket_message(connection_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket message"""
    message_type = message.get("type")
    
    if message_type == "start_workflow":
        await handle_start_workflow(connection_id, message)
    elif message_type == "subscribe_workflow":
        await handle_subscribe_workflow(connection_id, message)
    elif message_type == "get_workflow_status":
        await handle_get_workflow_status(connection_id, message)
    elif message_type == "file_operation":
        await handle_file_operation(connection_id, message)
    elif message_type == "run_command":
        await handle_run_command(connection_id, message)
    elif message_type == "ping":
        await handle_ping(connection_id, message)
    else:
        await manager.send_personal_message({
            "type": "error",
            "error": f"Unknown message type: {message_type}",
            "timestamp": time.time()
        }, connection_id)


async def handle_start_workflow(connection_id: str, message: Dict[str, Any]):
    """Handle workflow start request"""
    try:
        # Get workflow manager (you'd need to pass this in production)
        from fastapi import Request
        # This is a simplified approach - in production, you'd inject dependencies properly
        
        user_request = message.get("user_request")
        if not user_request:
            await manager.send_personal_message({
                "type": "error",
                "error": "user_request is required",
                "timestamp": time.time()
            }, connection_id)
            return
        
        # Start workflow (mock response for now)
        workflow_id = f"workflow_{int(time.time())}"
        
        # Subscribe to workflow updates
        manager.subscribe_to_workflow(connection_id, workflow_id)
        
        # Send response
        await manager.send_personal_message({
            "type": "workflow_started",
            "workflow_id": workflow_id,
            "status": "started",
            "timestamp": time.time()
        }, connection_id)
        
        # Simulate workflow progress
        asyncio.create_task(simulate_workflow_progress(workflow_id))
        
    except Exception as e:
        await manager.send_personal_message({
            "type": "error",
            "error": f"Failed to start workflow: {str(e)}",
            "timestamp": time.time()
        }, connection_id)


async def handle_subscribe_workflow(connection_id: str, message: Dict[str, Any]):
    """Handle workflow subscription request"""
    workflow_id = message.get("workflow_id")
    if not workflow_id:
        await manager.send_personal_message({
            "type": "error",
            "error": "workflow_id is required",
            "timestamp": time.time()
        }, connection_id)
        return
    
    manager.subscribe_to_workflow(connection_id, workflow_id)
    
    await manager.send_personal_message({
        "type": "subscribed",
        "workflow_id": workflow_id,
        "timestamp": time.time()
    }, connection_id)


async def handle_get_workflow_status(connection_id: str, message: Dict[str, Any]):
    """Handle workflow status request"""
    workflow_id = message.get("workflow_id")
    if not workflow_id:
        await manager.send_personal_message({
            "type": "error",
            "error": "workflow_id is required",
            "timestamp": time.time()
        }, connection_id)
        return
    
    # Mock status response
    await manager.send_personal_message({
        "type": "workflow_status",
        "workflow_id": workflow_id,
        "status": "running",
        "current_step": "code_generation",
        "progress": {
            "completed_steps": 2,
            "total_steps": 4,
            "percentage": 50
        },
        "timestamp": time.time()
    }, connection_id)


async def handle_file_operation(connection_id: str, message: Dict[str, Any]):
    """Handle file operation request"""
    try:
        fs_tool = FileSystemTool()
        
        operation = message.get("operation")
        file_path = message.get("file_path")
        content = message.get("content")
        args = message.get("args", {})
        
        if not operation:
            await manager.send_personal_message({
                "type": "error",
                "error": "operation is required",
                "timestamp": time.time()
            }, connection_id)
            return
        
        # Prepare kwargs
        kwargs = args.copy()
        if file_path:
            kwargs["file_path"] = file_path
        if content:
            kwargs["content"] = content
        
        # Execute operation
        result = await fs_tool.safe_execute(operation, **kwargs)
        
        await manager.send_personal_message({
            "type": "file_operation_result",
            "operation": operation,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "timestamp": time.time()
        }, connection_id)
        
    except Exception as e:
        await manager.send_personal_message({
            "type": "error",
            "error": f"File operation failed: {str(e)}",
            "timestamp": time.time()
        }, connection_id)


async def handle_run_command(connection_id: str, message: Dict[str, Any]):
    """Handle command execution request"""
    try:
        cmd_tool = CommandExecutionTool()
        
        command = message.get("command")
        args = message.get("args", [])
        timeout = message.get("timeout")
        cwd = message.get("cwd")
        
        if not command:
            await manager.send_personal_message({
                "type": "error",
                "error": "command is required",
                "timestamp": time.time()
            }, connection_id)
            return
        
        # Execute command
        result = await cmd_tool.safe_execute(
            "run_command",
            command=command,
            args=args,
            timeout=timeout,
            cwd=cwd
        )
        
        await manager.send_personal_message({
            "type": "command_result",
            "command": command,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "timestamp": time.time()
        }, connection_id)
        
    except Exception as e:
        await manager.send_personal_message({
            "type": "error",
            "error": f"Command execution failed: {str(e)}",
            "timestamp": time.time()
        }, connection_id)


async def handle_ping(connection_id: str, message: Dict[str, Any]):
    """Handle ping request"""
    await manager.send_personal_message({
        "type": "pong",
        "timestamp": time.time(),
        "original_timestamp": message.get("timestamp")
    }, connection_id)


async def simulate_workflow_progress(workflow_id: str):
    """Simulate workflow progress for demo purposes"""
    steps = [
        {"step": "qa_intake", "message": "Gathering requirements..."},
        {"step": "manager", "message": "Creating implementation plan..."},
        {"step": "code", "message": "Generating code..."},
        {"step": "review", "message": "Reviewing implementation..."},
        {"step": "complete", "message": "Workflow completed successfully!"}
    ]
    
    for i, step_info in enumerate(steps):
        await asyncio.sleep(3)  # Simulate processing time
        
        await manager.broadcast_to_workflow({
            "type": "workflow_progress",
            "workflow_id": workflow_id,
            "current_step": step_info["step"],
            "message": step_info["message"],
            "progress": {
                "completed_steps": i + 1,
                "total_steps": len(steps),
                "percentage": ((i + 1) / len(steps)) * 100
            },
            "timestamp": time.time()
        }, workflow_id)
    
    # Mark as completed
    await manager.broadcast_to_workflow({
        "type": "workflow_completed",
        "workflow_id": workflow_id,
        "status": "completed",
        "result": {
            "files_generated": 5,
            "total_lines": 247,
            "execution_time": 15.3
        },
        "timestamp": time.time()
    }, workflow_id)