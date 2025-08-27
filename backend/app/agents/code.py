"""
Code Agent - Implements tasks from the development plan
"""
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import structlog

from app.agents.base import BaseAgent, AgentResult
from app.models.mistral import MistralModelWrapper
from app.agents.manager import Task, TaskStatus

logger = structlog.get_logger(__name__)


@dataclass
class CodeFile:
    """Represents a generated code file"""
    path: str
    content: str
    language: str
    description: str
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class CodeImplementation:
    """Complete code implementation for a task"""
    task_id: str
    files: List[CodeFile]
    setup_instructions: List[str]
    test_instructions: List[str]
    documentation: str
    quality_score: float = 0.0
    review_notes: List[str] = None
    
    def __post_init__(self):
        if self.review_notes is None:
            self.review_notes = []


class CodeAgent(BaseAgent):
    """Code Agent for implementing development tasks"""
    
    def __init__(self, model_wrapper: MistralModelWrapper):
        super().__init__("CodeAgent", model_wrapper)
        self.code_templates = self._load_code_templates()
        self.quality_threshold = 7.0  # Minimum quality score
    
    def _load_code_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load code templates for different project types"""
        return {
            "web_application": {
                "react": {
                    "structure": [
                        "src/components",
                        "src/pages", 
                        "src/hooks",
                        "src/utils",
                        "src/styles",
                        "public"
                    ],
                    "key_files": [
                        "package.json",
                        "src/App.jsx",
                        "src/index.js",
                        "src/components/Layout.jsx"
                    ]
                },
                "fastapi": {
                    "structure": [
                        "app/api",
                        "app/core",
                        "app/models",
                        "app/schemas",
                        "tests"
                    ],
                    "key_files": [
                        "main.py",
                        "requirements.txt",
                        "app/api/routes.py",
                        "app/core/config.py"
                    ]
                }
            },
            "api": {
                "fastapi": {
                    "structure": [
                        "app/api/v1",
                        "app/core",
                        "app/models",
                        "app/schemas",
                        "app/crud",
                        "tests"
                    ],
                    "key_files": [
                        "main.py",
                        "requirements.txt",
                        "app/api/v1/endpoints.py"
                    ]
                }
            },
            "cli_tool": {
                "python": {
                    "structure": [
                        "src",
                        "tests",
                        "docs"
                    ],
                    "key_files": [
                        "setup.py",
                        "src/main.py",
                        "src/cli.py",
                        "requirements.txt"
                    ]
                }
            }
        }
    
    async def process(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResult:
        """Process task and generate code implementation"""
        try:
            if isinstance(input_data, dict) and "task" in input_data:
                return await self._implement_task(input_data["task"], input_data.get("project_context", {}), context)
            elif isinstance(input_data, dict) and "review_feedback" in input_data:
                return await self._handle_review_feedback(input_data, context)
            else:
                return AgentResult(
                    success=False,
                    error="Invalid input format. Expected task or review_feedback."
                )
        
        except Exception as e:
            logger.error("Error implementing task", error=str(e))
            return AgentResult(
                success=False,
                error=str(e)
            )
    
    async def _implement_task(self, task: Dict[str, Any], project_context: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """Implement a specific development task"""
        self.logger.info("Implementing task", task_id=task.get("id"), title=task.get("title"))
        
        # Generate code using AI
        code_result = await self._generate_code_implementation(task, project_context)
        
        if not code_result["success"]:
            return AgentResult(
                success=False,
                error=code_result["error"]
            )
        
        implementation = code_result["implementation"]
        
        # Review code quality
        quality_result = await self._review_code_quality(implementation)
        implementation.quality_score = quality_result["score"]
        implementation.review_notes = quality_result["notes"]
        
        # Check if quality meets threshold
        if implementation.quality_score < self.quality_threshold:
            return await self._request_code_revision(implementation, quality_result)
        
        return AgentResult(
            success=True,
            data={
                "implementation": implementation,
                "next_action": "deploy_code",
                "status": "implementation_complete",
                "quality_score": implementation.quality_score
            },
            tokens_used=code_result.get("tokens_used", 0) + quality_result.get("tokens_used", 0)
        )
    
    async def _generate_code_implementation(self, task: Dict[str, Any], project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code implementation using AI"""
        try:
            # Prepare context for AI
            task_details = json.dumps(task, indent=2)
            context_details = json.dumps(project_context, indent=2)
            
            # Generate code using AI model
            ai_result = await self.model_wrapper.generate_code_implementation(task_details, context_details)
            
            # Parse AI response into structured implementation
            implementation = self._parse_code_response(ai_result, task)
            
            return {
                "success": True,
                "implementation": implementation,
                "ai_response": ai_result,
                "tokens_used": ai_result.get("usage", {}).get("total_tokens", 0)
            }
        
        except Exception as e:
            logger.error("Code generation failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_code_response(self, ai_result: Dict[str, Any], task: Dict[str, Any]) -> CodeImplementation:
        """Parse AI response into structured code implementation"""
        
        code_blocks = ai_result.get("code_blocks", [])
        response_text = ai_result.get("response", "")
        
        # Create code files from AI response
        files = []
        for i, block in enumerate(code_blocks):
            language = block.get("language", "text")
            code = block.get("code", "")
            
            # Determine file path based on language and content
            file_path = self._determine_file_path(code, language, i)
            
            files.append(CodeFile(
                path=file_path,
                content=code,
                language=language,
                description=f"Generated {language} code for {task.get('title', 'task')}"
            ))
        
        # If no code blocks found, create a single file from response
        if not files and response_text:
            files.append(CodeFile(
                path="main.py",  # Default
                content=response_text,
                language="python",
                description=f"Implementation for {task.get('title', 'task')}"
            ))
        
        # Extract setup and test instructions from response
        setup_instructions = self._extract_instructions(response_text, "setup")
        test_instructions = self._extract_instructions(response_text, "test")
        
        return CodeImplementation(
            task_id=task.get("id", "unknown"),
            files=files,
            setup_instructions=setup_instructions,
            test_instructions=test_instructions,
            documentation=self._generate_documentation(task, files, response_text)
        )
    
    def _determine_file_path(self, code: str, language: str, index: int) -> str:
        """Determine appropriate file path for code"""
        
        # Look for file path hints in code comments
        lines = code.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            if '# File:' in line or '// File:' in line or '<!-- File:' in line:
                path = line.split(':', 1)[-1].strip()
                return path
        
        # Determine based on language and content
        if language == "python":
            if "from fastapi" in code or "FastAPI" in code:
                return "main.py"
            elif "import pytest" in code or "def test_" in code:
                return f"test_{index}.py"
            else:
                return f"module_{index}.py"
        
        elif language in ["javascript", "js"]:
            if "import React" in code or "function App" in code:
                return "src/App.js"
            elif "describe(" in code or "test(" in code:
                return f"tests/test_{index}.js"
            else:
                return f"script_{index}.js"
        
        elif language in ["typescript", "ts"]:
            return f"src/component_{index}.ts"
        
        elif language == "html":
            return "index.html"
        
        elif language == "css":
            return "styles.css"
        
        elif language == "json":
            if "package.json" in code or '"name"' in code[:100]:
                return "package.json"
            else:
                return f"config_{index}.json"
        
        else:
            return f"file_{index}.{language}"
    
    def _extract_instructions(self, text: str, instruction_type: str) -> List[str]:
        """Extract setup or test instructions from text"""
        instructions = []
        lines = text.split('\n')
        
        # Look for instruction sections
        in_section = False
        section_markers = {
            "setup": ["# Setup", "## Setup", "Installation:", "To install:", "Setup:"],
            "test": ["# Testing", "## Testing", "To test:", "Run tests:", "Testing:"]
        }
        
        for line in lines:
            line = line.strip()
            
            # Check if we're entering the section
            if any(marker in line for marker in section_markers.get(instruction_type, [])):
                in_section = True
                continue
            
            # Check if we're leaving the section
            if in_section and line.startswith('#') and instruction_type not in line.lower():
                break
            
            # Collect instructions
            if in_section and line:
                if line.startswith('-') or line.startswith('*') or line.startswith('1.'):
                    instructions.append(line.lstrip('- *1234567890. '))
                elif line.startswith('```') or line.startswith('$'):
                    instructions.append(line.lstrip('$ `'))
        
        # Default instructions if none found
        if not instructions:
            if instruction_type == "setup":
                instructions = ["Install dependencies", "Configure environment", "Run setup script"]
            elif instruction_type == "test":
                instructions = ["Run test suite", "Check code quality", "Verify functionality"]
        
        return instructions[:5]  # Limit to 5 instructions
    
    def _generate_documentation(self, task: Dict[str, Any], files: List[CodeFile], response: str) -> str:
        """Generate documentation for the implementation"""
        
        doc_sections = [
            f"# Implementation: {task.get('title', 'Task')}",
            "",
            f"## Description",
            task.get('description', 'No description available'),
            "",
            "## Files Generated",
        ]
        
        for file in files:
            doc_sections.extend([
                f"### {file.path}",
                f"- Language: {file.language}",
                f"- Description: {file.description}",
                ""
            ])
        
        doc_sections.extend([
            "## Implementation Notes",
            response[:500] + "..." if len(response) > 500 else response
        ])
        
        return '\n'.join(doc_sections)
    
    async def _review_code_quality(self, implementation: CodeImplementation) -> Dict[str, Any]:
        """Review code quality using AI"""
        try:
            quality_scores = []
            all_notes = []
            tokens_used = 0
            
            # Review each file
            for file in implementation.files:
                if file.language in ["python", "javascript", "typescript", "java", "go"]:
                    review_result = await self.model_wrapper.validate_code_quality(
                        file.content, file.language
                    )
                    
                    quality_scores.append(review_result.get("quality_score", 7))
                    if "raw_feedback" in review_result:
                        all_notes.append(f"{file.path}: {review_result['raw_feedback'][:200]}")
                    
                    tokens_used += 50  # Estimate
            
            # Calculate average quality score
            avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 7.0
            
            return {
                "score": avg_score,
                "notes": all_notes,
                "tokens_used": tokens_used
            }
        
        except Exception as e:
            logger.error("Code quality review failed", error=str(e))
            return {
                "score": 6.0,  # Default moderate score
                "notes": [f"Quality review failed: {str(e)}"],
                "tokens_used": 0
            }
    
    async def _request_code_revision(self, implementation: CodeImplementation, quality_result: Dict[str, Any]) -> AgentResult:
        """Request code revision due to quality issues"""
        return AgentResult(
            success=False,
            data={
                "implementation": implementation,
                "revision_required": True,
                "quality_issues": quality_result["notes"],
                "quality_score": quality_result["score"],
                "next_action": "revise_code"
            },
            error=f"Code quality below threshold ({implementation.quality_score} < {self.quality_threshold})"
        )
    
    async def _handle_review_feedback(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """Handle feedback from Manager agent and revise code"""
        
        review_feedback = input_data["review_feedback"]
        current_implementation = input_data.get("current_implementation")
        
        if not current_implementation:
            return AgentResult(
                success=False,
                error="No current implementation provided for revision"
            )
        
        # This would involve re-generating code based on feedback
        # For now, return the current implementation with feedback noted
        
        return AgentResult(
            success=True,
            data={
                "revised_implementation": current_implementation,
                "feedback_addressed": True,
                "next_action": "continue_implementation"
            }
        )
    
    def get_implementation_summary(self, implementation: CodeImplementation) -> Dict[str, Any]:
        """Get summary of the code implementation"""
        return {
            "task_id": implementation.task_id,
            "files_count": len(implementation.files),
            "languages": list(set(f.language for f in implementation.files)),
            "quality_score": implementation.quality_score,
            "has_tests": any("test" in f.path.lower() for f in implementation.files),
            "setup_steps": len(implementation.setup_instructions),
            "documentation_length": len(implementation.documentation)
        }