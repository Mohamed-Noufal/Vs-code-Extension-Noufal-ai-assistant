"""
Mistral-specific model implementation and utilities
"""
from typing import Dict, Any, List, Optional
import json
import re

import structlog

from app.models.manager import ModelManager

logger = structlog.get_logger(__name__)


class MistralPromptTemplate:
    """Mistral-specific prompt templates and formatting"""
    
    # Mistral instruction format
    INSTRUCTION_TEMPLATE = """<s>[INST] {instruction} [/INST]"""
    
    SYSTEM_PROMPT = """You are a professional software engineer assistant. You provide clear, accurate, and helpful responses about software development, coding practices, and technical solutions."""
    
    # Agent-specific templates
    QA_AGENT_TEMPLATE = """<s>[INST] You are a Q&A Intake Agent for a development system. Your role is to gather detailed requirements from users who want to build software projects.

Ask clarifying questions to understand:
1. What type of project they want to build
2. Target platform and technology preferences
3. Key features and functionality
4. Timeline and complexity expectations
5. Any specific constraints or requirements

User request: {user_request}

Respond with clarifying questions to gather complete requirements. Be conversational and helpful. [/INST]"""

    MANAGER_AGENT_TEMPLATE = """<s>[INST] You are a Manager/Planner Agent. Convert user requirements into a detailed implementation plan.

Requirements Summary:
{requirements}

Create a JSON plan with:
- Project overview
- Technical specifications
- Task breakdown with priorities
- Implementation order
- Acceptance criteria for each task

Respond with a well-structured PLAN.json format. [/INST]"""

    CODE_AGENT_TEMPLATE = """<s>[INST] You are a Code Agent. Implement the specified task from the development plan.

Task Details:
{task_details}

Project Context:
{project_context}

Generate working, production-ready code with:
- Proper error handling
- Clear documentation
- Best practices
- Test considerations

Provide the complete implementation. [/INST]"""

    @classmethod
    def format_qa_prompt(cls, user_request: str) -> str:
        """Format prompt for Q&A agent"""
        return cls.QA_AGENT_TEMPLATE.format(user_request=user_request)
    
    @classmethod
    def format_manager_prompt(cls, requirements: str) -> str:
        """Format prompt for Manager agent"""
        return cls.MANAGER_AGENT_TEMPLATE.format(requirements=requirements)
    
    @classmethod
    def format_code_prompt(cls, task_details: str, project_context: str) -> str:
        """Format prompt for Code agent"""
        return cls.CODE_AGENT_TEMPLATE.format(
            task_details=task_details,
            project_context=project_context
        )
    
    @classmethod
    def extract_json_from_response(cls, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from model response"""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except Exception as e:
            logger.warning("Failed to extract JSON from response", error=str(e))
        return None
    
    @classmethod
    def extract_code_from_response(cls, response: str) -> List[Dict[str, str]]:
        """Extract code blocks from model response"""
        code_blocks = []
        
        # Find code blocks with language specification
        # More robust regex to handle various code block formats
        pattern = r'```(\w+)?\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for language, code in matches:
            if code.strip():  # Only add non-empty code blocks
                code_blocks.append({
                    "language": language.strip() if language else "text",
                    "code": code.strip()
                })
        
        return code_blocks


class MistralModelWrapper:
    """Wrapper for Mistral model with specialized methods"""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
    
    async def generate_qa_response(self, user_request: str) -> str:
        """Generate Q&A agent response"""
        prompt = MistralPromptTemplate.format_qa_prompt(user_request)
        
        result = await self.model_manager.generate(
            prompt=prompt,
            max_tokens=512,
            temperature=0.7,
            stop_sequences=["[INST]", "</s>"]
        )
        
        return result["text"].strip()
    
    async def generate_manager_plan(self, requirements: str) -> Dict[str, Any]:
        """Generate Manager agent plan"""
        prompt = MistralPromptTemplate.format_manager_prompt(requirements)
        
        result = await self.model_manager.generate(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.3,
            stop_sequences=["[INST]", "</s>"]
        )
        
        response_text = result["text"].strip()
        
        # Try to extract JSON plan
        plan = MistralPromptTemplate.extract_json_from_response(response_text)
        
        if not plan:
            # Fallback: create structured plan from text
            plan = {
                "project_overview": "Generated from requirements",
                "tasks": [
                    {
                        "id": "task_1",
                        "title": "Implement based on requirements",
                        "description": response_text[:500],
                        "priority": "high",
                        "status": "pending"
                    }
                ],
                "raw_response": response_text
            }
        
        return plan
    
    async def generate_code_implementation(
        self, 
        task_details: str, 
        project_context: str
    ) -> Dict[str, Any]:
        """Generate Code agent implementation"""
        prompt = MistralPromptTemplate.format_code_prompt(task_details, project_context)
        
        result = await self.model_manager.generate(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.2,
            stop_sequences=["[INST]", "</s>"]
        )
        
        response_text = result["text"].strip()
        
        # Extract code blocks
        code_blocks = MistralPromptTemplate.extract_code_from_response(response_text)
        
        return {
            "response": response_text,
            "code_blocks": code_blocks,
            "usage": result["usage"]
        }
    
    async def validate_code_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Validate generated code quality"""
        validation_prompt = f"""<s>[INST] Review this {language} code for quality, best practices, and potential issues:

```{language}
{code}
```

Provide feedback on:
1. Code quality and structure
2. Best practices compliance
3. Potential bugs or issues
4. Suggestions for improvement

Respond with a JSON format assessment. [/INST]"""
        
        result = await self.model_manager.generate(
            prompt=validation_prompt,
            max_tokens=512,
            temperature=0.1
        )
        
        response_text = result["text"].strip()
        assessment = MistralPromptTemplate.extract_json_from_response(response_text)
        
        if not assessment:
            assessment = {
                "quality_score": 7,  # Default moderate score
                "issues": [],
                "suggestions": [],
                "raw_feedback": response_text
            }
        
        return assessment