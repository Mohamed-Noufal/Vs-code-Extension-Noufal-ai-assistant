"""
File System MCP Tool - Safe file system operations
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

import aiofiles
import structlog

from app.mcp_tools.base_tool import BaseMCPTool, ToolResult
from app.core.config import settings

logger = structlog.get_logger(__name__)


class FileSystemTool(BaseMCPTool):
    """Safe file system operations tool"""
    
    def __init__(self):
        super().__init__("filesystem")
        self.supported_operations = {
            "read_file", "write_file", "create_file", "delete_file",
            "list_directory", "create_directory", "delete_directory",
            "copy_file", "move_file", "get_file_info"
        }
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute file system operation"""
        
        if operation not in self.supported_operations:
            return ToolResult(
                success=False,
                error=f"Unsupported operation: {operation}"
            )
        
        # Route to specific operation
        method = getattr(self, f"_{operation}", None)
        if not method:
            return ToolResult(
                success=False,
                error=f"Operation method not found: {operation}"
            )
        
        return await method(**kwargs)
    
    async def _read_file(self, file_path: str) -> ToolResult:
        """Read file content"""
        if not self.validate_path(file_path):
            return ToolResult(
                success=False,
                error=f"Invalid file path: {file_path}"
            )
        
        full_path = self.workspace_dir / file_path
        
        if not full_path.exists():
            return ToolResult(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        if not full_path.is_file():
            return ToolResult(
                success=False,
                error=f"Path is not a file: {file_path}"
            )
        
        try:
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            return ToolResult(
                success=True,
                data={
                    "content": content,
                    "file_path": file_path,
                    "size_bytes": len(content.encode('utf-8'))
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to read file: {str(e)}"
            )
    
    async def _write_file(self, file_path: str, content: str, overwrite: bool = False) -> ToolResult:
        """Write content to file"""
        if not self.validate_path(file_path):
            return ToolResult(
                success=False,
                error=f"Invalid file path: {file_path}"
            )
        
        if not self.is_allowed_file_type(file_path):
            return ToolResult(
                success=False,
                error=f"File type not allowed: {Path(file_path).suffix}"
            )
        
        if not self.is_within_size_limit(content):
            return ToolResult(
                success=False,
                error=f"Content exceeds size limit ({settings.MAX_FILE_SIZE} bytes)"
            )
        
        full_path = self.workspace_dir / file_path
        
        if full_path.exists() and not overwrite:
            return ToolResult(
                success=False,
                error=f"File already exists: {file_path}. Use overwrite=True to replace."
            )
        
        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return ToolResult(
                success=True,
                data={
                    "file_path": file_path,
                    "bytes_written": len(content.encode('utf-8')),
                    "created": not overwrite
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to write file: {str(e)}"
            )
    
    async def _create_file(self, file_path: str, content: str = "") -> ToolResult:
        """Create new file"""
        return await self._write_file(file_path, content, overwrite=False)
    
    async def _delete_file(self, file_path: str) -> ToolResult:
        """Delete file"""
        if not self.validate_path(file_path):
            return ToolResult(
                success=False,
                error=f"Invalid file path: {file_path}"
            )
        
        full_path = self.workspace_dir / file_path
        
        if not full_path.exists():
            return ToolResult(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        if not full_path.is_file():
            return ToolResult(
                success=False,
                error=f"Path is not a file: {file_path}"
            )
        
        try:
            full_path.unlink()
            return ToolResult(
                success=True,
                data={"deleted_file": file_path}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to delete file: {str(e)}"
            )
    
    async def _list_directory(self, dir_path: str = "", include_hidden: bool = False) -> ToolResult:
        """List directory contents"""
        if not self.validate_path(dir_path):
            return ToolResult(
                success=False,
                error=f"Invalid directory path: {dir_path}"
            )
        
        full_path = self.workspace_dir / dir_path if dir_path else self.workspace_dir
        
        if not full_path.exists():
            return ToolResult(
                success=False,
                error=f"Directory not found: {dir_path}"
            )
        
        if not full_path.is_dir():
            return ToolResult(
                success=False,
                error=f"Path is not a directory: {dir_path}"
            )
        
        try:
            items = []
            for item in full_path.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                item_info = {
                    "name": item.name,
                    "path": str(item.relative_to(self.workspace_dir)),
                    "type": "file" if item.is_file() else "directory",
                    "size": item.stat().st_size if item.is_file() else None
                }
                items.append(item_info)
            
            return ToolResult(
                success=True,
                data={
                    "directory": dir_path or ".",
                    "items": sorted(items, key=lambda x: (x["type"], x["name"])),
                    "total_items": len(items)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list directory: {str(e)}"
            )
    
    async def _create_directory(self, dir_path: str) -> ToolResult:
        """Create directory"""
        if not self.validate_path(dir_path):
            return ToolResult(
                success=False,
                error=f"Invalid directory path: {dir_path}"
            )
        
        full_path = self.workspace_dir / dir_path
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            return ToolResult(
                success=True,
                data={"created_directory": dir_path}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to create directory: {str(e)}"
            )
    
    async def _delete_directory(self, dir_path: str, recursive: bool = False) -> ToolResult:
        """Delete directory"""
        if not self.validate_path(dir_path):
            return ToolResult(
                success=False,
                error=f"Invalid directory path: {dir_path}"
            )
        
        full_path = self.workspace_dir / dir_path
        
        if not full_path.exists():
            return ToolResult(
                success=False,
                error=f"Directory not found: {dir_path}"
            )
        
        if not full_path.is_dir():
            return ToolResult(
                success=False,
                error=f"Path is not a directory: {dir_path}"
            )
        
        try:
            if recursive:
                shutil.rmtree(full_path)
            else:
                full_path.rmdir()  # Only works if empty
            
            return ToolResult(
                success=True,
                data={"deleted_directory": dir_path}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to delete directory: {str(e)}"
            )
    
    async def _copy_file(self, source_path: str, dest_path: str) -> ToolResult:
        """Copy file"""
        if not self.validate_path(source_path) or not self.validate_path(dest_path):
            return ToolResult(
                success=False,
                error="Invalid file paths"
            )
        
        source_full = self.workspace_dir / source_path
        dest_full = self.workspace_dir / dest_path
        
        if not source_full.exists():
            return ToolResult(
                success=False,
                error=f"Source file not found: {source_path}"
            )
        
        try:
            # Create destination directory if needed
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_full, dest_full)
            
            return ToolResult(
                success=True,
                data={
                    "source": source_path,
                    "destination": dest_path,
                    "size_bytes": dest_full.stat().st_size
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to copy file: {str(e)}"
            )
    
    async def _move_file(self, source_path: str, dest_path: str) -> ToolResult:
        """Move file"""
        if not self.validate_path(source_path) or not self.validate_path(dest_path):
            return ToolResult(
                success=False,
                error="Invalid file paths"
            )
        
        source_full = self.workspace_dir / source_path
        dest_full = self.workspace_dir / dest_path
        
        if not source_full.exists():
            return ToolResult(
                success=False,
                error=f"Source file not found: {source_path}"
            )
        
        try:
            # Create destination directory if needed
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source_full), str(dest_full))
            
            return ToolResult(
                success=True,
                data={
                    "source": source_path,
                    "destination": dest_path
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to move file: {str(e)}"
            )
    
    async def _get_file_info(self, file_path: str) -> ToolResult:
        """Get file information"""
        if not self.validate_path(file_path):
            return ToolResult(
                success=False,
                error=f"Invalid file path: {file_path}"
            )
        
        full_path = self.workspace_dir / file_path
        
        if not full_path.exists():
            return ToolResult(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        try:
            stat = full_path.stat()
            
            info = {
                "path": file_path,
                "name": full_path.name,
                "type": "file" if full_path.is_file() else "directory",
                "size_bytes": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "is_readable": os.access(full_path, os.R_OK),
                "is_writable": os.access(full_path, os.W_OK)
            }
            
            if full_path.is_file():
                info["extension"] = full_path.suffix
                info["is_allowed_type"] = self.is_allowed_file_type(file_path)
            
            return ToolResult(
                success=True,
                data=info
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get file info: {str(e)}"
            )