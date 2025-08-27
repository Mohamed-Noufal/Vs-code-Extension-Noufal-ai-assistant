"""
Command Execution MCP Tool - Safe command execution with timeouts
"""
import asyncio
import shlex
import signal
from typing import Dict, Any, List, Optional

import structlog

from app.mcp_tools.base_tool import BaseMCPTool, ToolResult
from app.core.config import settings

logger = structlog.get_logger(__name__)


class CommandExecutionTool(BaseMCPTool):
    """Safe command execution tool with sandboxing"""
    
    def __init__(self):
        super().__init__("command_execution")
        self.supported_operations = {
            "run_command", "run_shell", "check_command_exists"
        }
        self.allowed_commands = {
            # Package managers
            "npm", "yarn", "pip", "poetry", "composer",
            # Build tools
            "make", "cmake", "gradle", "mvn",
            # Version control
            "git",
            # Node.js/JavaScript
            "node", "npx",
            # Python
            "python", "python3", "pytest",
            # General utilities
            "ls", "cat", "echo", "mkdir", "rm", "cp", "mv",
            "grep", "find", "which", "chmod"
        }
        self.forbidden_commands = {
            "sudo", "su", "passwd", "chmod +x", "rm -rf /",
            "dd", "fdisk", "mkfs", "mount", "umount",
            "iptables", "ufw", "systemctl", "service"
        }
        self.default_timeout = 30  # seconds
        self.max_timeout = 300  # 5 minutes
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute command operation"""
        
        if operation not in self.supported_operations:
            return ToolResult(
                success=False,
                error=f"Unsupported operation: {operation}"
            )
        
        method = getattr(self, f"_{operation}", None)
        if not method:
            return ToolResult(
                success=False,
                error=f"Operation method not found: {operation}"
            )
        
        return await method(**kwargs)
    
    async def _run_command(
        self, 
        command: str, 
        args: List[str] = None, 
        timeout: int = None,
        cwd: str = None
    ) -> ToolResult:
        """Run a single command with arguments"""
        
        if not self._is_command_allowed(command):
            return ToolResult(
                success=False,
                error=f"Command not allowed: {command}"
            )
        
        # Prepare command with arguments
        cmd_parts = [command]
        if args:
            cmd_parts.extend(args)
        
        return await self._execute_command(cmd_parts, timeout, cwd)
    
    async def _run_shell(
        self, 
        command_line: str, 
        timeout: int = None,
        cwd: str = None
    ) -> ToolResult:
        """Run a shell command line"""
        
        # Parse command line
        try:
            cmd_parts = shlex.split(command_line)
        except ValueError as e:
            return ToolResult(
                success=False,
                error=f"Invalid command line: {str(e)}"
            )
        
        if not cmd_parts:
            return ToolResult(
                success=False,
                error="Empty command"
            )
        
        # Check if base command is allowed
        base_command = cmd_parts[0]
        if not self._is_command_allowed(base_command):
            return ToolResult(
                success=False,
                error=f"Command not allowed: {base_command}"
            )
        
        # Check for forbidden patterns
        if any(forbidden in command_line for forbidden in self.forbidden_commands):
            return ToolResult(
                success=False,
                error="Command contains forbidden patterns"
            )
        
        return await self._execute_command(cmd_parts, timeout, cwd)
    
    async def _check_command_exists(self, command: str) -> ToolResult:
        """Check if command exists in system"""
        try:
            process = await asyncio.create_subprocess_exec(
                "which", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            exists = process.returncode == 0
            path = stdout.decode().strip() if exists else None
            
            return ToolResult(
                success=True,
                data={
                    "command": command,
                    "exists": exists,
                    "path": path,
                    "is_allowed": self._is_command_allowed(command)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to check command: {str(e)}"
            )
    
    async def _execute_command(
        self, 
        cmd_parts: List[str], 
        timeout: int = None,
        cwd: str = None
    ) -> ToolResult:
        """Execute command with proper sandboxing"""
        
        # Set timeout
        exec_timeout = min(timeout or self.default_timeout, self.max_timeout)
        
        # Set working directory
        work_dir = self.workspace_dir
        if cwd:
            if not self.validate_path(cwd):
                return ToolResult(
                    success=False,
                    error=f"Invalid working directory: {cwd}"
                )
            work_dir = self.workspace_dir / cwd
            if not work_dir.exists():
                return ToolResult(
                    success=False,
                    error=f"Working directory does not exist: {cwd}"
                )
        
        try:
            self.logger.info(
                "Executing command",
                command=cmd_parts[0],
                args=cmd_parts[1:],
                timeout=exec_timeout,
                cwd=str(work_dir)
            )
            
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=exec_timeout
                )
            except asyncio.TimeoutError:
                # Kill process group
                try:
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()
                    await process.wait()
                except:
                    pass
                
                return ToolResult(
                    success=False,
                    error=f"Command timed out after {exec_timeout} seconds"
                )
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    "command": " ".join(cmd_parts),
                    "return_code": process.returncode,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "working_directory": str(work_dir),
                    "timeout_seconds": exec_timeout
                },
                error=f"Command failed with return code {process.returncode}" if process.returncode != 0 else None
            )
        
        except Exception as e:
            self.logger.error("Command execution failed", error=str(e))
            return ToolResult(
                success=False,
                error=f"Command execution failed: {str(e)}"
            )
    
    def _is_command_allowed(self, command: str) -> bool:
        """Check if command is allowed"""
        
        # Extract base command (remove path)
        base_command = command.split('/')[-1]
        
        # Check allowed list
        if base_command in self.allowed_commands:
            return True
        
        # Check forbidden list
        if base_command in self.forbidden_commands:
            return False
        
        # Check for common safe patterns
        safe_patterns = [
            base_command.startswith('python'),
            base_command.startswith('node'),
            base_command.startswith('npm'),
            base_command.endswith('.py'),
            base_command.endswith('.js'),
            base_command.endswith('.sh')
        ]
        
        return any(safe_patterns)
    
    def get_allowed_commands(self) -> List[str]:
        """Get list of allowed commands"""
        return sorted(list(self.allowed_commands))
    
    def get_forbidden_commands(self) -> List[str]:
        """Get list of forbidden commands"""
        return sorted(list(self.forbidden_commands))