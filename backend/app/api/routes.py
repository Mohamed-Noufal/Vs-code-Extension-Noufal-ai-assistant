"""
REST API Routes
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

import structlog

from app.core.config import settings
from app.orchestrator.workflow import WorkflowManager
from app.mcp_tools.fs_tool import FileSystemTool
from app.mcp_tools.run_tool import CommandExecutionTool

logger = structlog.get_logger(__name__)

# Create router
api_router = APIRouter()

# Pydantic models
class WorkflowStartRequest(BaseModel):
    user_request: str
    user_id: Optional[str] = None

class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    current_step: str
    progress: Dict[str, Any]

class FileOperationRequest(BaseModel):
    operation: str
    file_path: Optional[str] = None
    content: Optional[str] = None
    args: Optional[Dict[str, Any]] = None

class CommandRequest(BaseModel):
    command: str
    args: Optional[List[str]] = None
    timeout: Optional[int] = None
    cwd: Optional[str] = None


# Dependency injection
async def get_workflow_manager() -> WorkflowManager:
    """Get workflow manager from app state"""
    from fastapi import Request
    request: Request = Depends()
    return request.app.state.workflow_manager

async def get_fs_tool() -> FileSystemTool:
    """Get file system tool"""
    return FileSystemTool()

async def get_cmd_tool() -> CommandExecutionTool:
    """Get command execution tool"""
    return CommandExecutionTool()


# Workflow endpoints
@api_router.post("/workflows/start")
async def start_workflow(
    request: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Dict[str, str]:
    """Start a new multi-agent workflow"""
    try:
        workflow_id = await workflow_manager.start_workflow(
            user_request=request.user_request,
            user_id=request.user_id
        )
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": "Workflow started successfully"
        }
    
    except Exception as e:
        logger.error("Failed to start workflow", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start workflow: {str(e)}"
        )

@api_router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """Get workflow status"""
    try:
        status = workflow_manager.get_workflow_status(workflow_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow not found: {workflow_id}"
            )
        
        return {
            "workflow_id": workflow_id,
            **status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow status: {str(e)}"
        )

@api_router.get("/workflows")
async def list_workflows(
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """List all active workflows"""
    try:
        workflows = []
        for workflow_id, state in workflow_manager.active_workflows.items():
            workflows.append({
                "workflow_id": workflow_id,
                "status": state.status.value,
                "current_step": state.current_step,
                "started_at": state.started_at,
                "completed_at": state.completed_at
            })
        
        return {
            "workflows": workflows,
            "total_count": len(workflows)
        }
    
    except Exception as e:
        logger.error("Failed to list workflows", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list workflows: {str(e)}"
        )


# File system endpoints
@api_router.post("/fs/operation")
async def file_operation(
    request: FileOperationRequest,
    fs_tool: FileSystemTool = Depends(get_fs_tool)
) -> Dict[str, Any]:
    """Execute file system operation"""
    try:
        # Prepare arguments
        kwargs = request.args or {}
        if request.file_path:
            kwargs["file_path"] = request.file_path
        if request.content:
            kwargs["content"] = request.content
        
        # Execute operation
        result = await fs_tool.safe_execute(request.operation, **kwargs)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time
        }
    
    except Exception as e:
        logger.error("File operation failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"File operation failed: {str(e)}"
        )

@api_router.get("/fs/list")
async def list_directory(
    path: str = "",
    include_hidden: bool = False,
    fs_tool: FileSystemTool = Depends(get_fs_tool)
) -> Dict[str, Any]:
    """List directory contents"""
    try:
        result = await fs_tool.safe_execute(
            "list_directory",
            dir_path=path,
            include_hidden=include_hidden
        )
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error
            )
        
        return result.data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Directory listing failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Directory listing failed: {str(e)}"
        )

@api_router.get("/fs/read/{file_path:path}")
async def read_file(
    file_path: str,
    fs_tool: FileSystemTool = Depends(get_fs_tool)
) -> Dict[str, Any]:
    """Read file content"""
    try:
        result = await fs_tool.safe_execute("read_file", file_path=file_path)
        
        if not result.success:
            raise HTTPException(
                status_code=404 if "not found" in result.error.lower() else 400,
                detail=result.error
            )
        
        return result.data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("File read failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"File read failed: {str(e)}"
        )


# Command execution endpoints
@api_router.post("/cmd/run")
async def run_command(
    request: CommandRequest,
    cmd_tool: CommandExecutionTool = Depends(get_cmd_tool)
) -> Dict[str, Any]:
    """Execute command"""
    try:
        # Execute command
        result = await cmd_tool.safe_execute(
            "run_command",
            command=request.command,
            args=request.args,
            timeout=request.timeout,
            cwd=request.cwd
        )
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time
        }
    
    except Exception as e:
        logger.error("Command execution failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Command execution failed: {str(e)}"
        )

@api_router.post("/cmd/shell")
async def run_shell_command(
    command_line: str,
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
    cmd_tool: CommandExecutionTool = Depends(get_cmd_tool)
) -> Dict[str, Any]:
    """Execute shell command"""
    try:
        result = await cmd_tool.safe_execute(
            "run_shell",
            command_line=command_line,
            timeout=timeout,
            cwd=cwd
        )
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time
        }
    
    except Exception as e:
        logger.error("Shell command execution failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Shell command execution failed: {str(e)}"
        )

@api_router.get("/cmd/allowed")
async def get_allowed_commands(
    cmd_tool: CommandExecutionTool = Depends(get_cmd_tool)
) -> Dict[str, List[str]]:
    """Get allowed and forbidden commands"""
    return {
        "allowed_commands": cmd_tool.get_allowed_commands(),
        "forbidden_commands": cmd_tool.get_forbidden_commands()
    }


# Agent and system status endpoints
@api_router.get("/agents/status")
async def get_agents_status(
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """Get status of all agents"""
    try:
        agent_info = workflow_manager.get_agent_info()
        return {
            "agents": agent_info,
            "total_agents": len(agent_info)
        }
    
    except Exception as e:
        logger.error("Failed to get agent status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )

@api_router.get("/tools/status")
async def get_tools_status(
    fs_tool: FileSystemTool = Depends(get_fs_tool),
    cmd_tool: CommandExecutionTool = Depends(get_cmd_tool)
) -> Dict[str, Any]:
    """Get status of all MCP tools"""
    try:
        return {
            "tools": [
                fs_tool.get_stats(),
                cmd_tool.get_stats()
            ]
        }
    
    except Exception as e:
        logger.error("Failed to get tools status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tools status: {str(e)}"
        )