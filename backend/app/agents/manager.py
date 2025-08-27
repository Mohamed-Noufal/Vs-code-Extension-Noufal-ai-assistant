"""
Manager/Planner Agent - Converts requirements into detailed implementation plans
"""
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import structlog

from app.agents.base import BaseAgent, AgentResult
from app.models.mistral import MistralModelWrapper

logger = structlog.get_logger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class Task:
    """Individual task in the implementation plan"""
    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    estimated_hours: float
    dependencies: List[str] = None
    acceptance_criteria: List[str] = None
    technical_notes: str = ""
    assigned_agent: str = "CodeAgent"
    created_at: float = None
    updated_at: float = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert enums to strings
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        return data


@dataclass
class ImplementationPlan:
    """Complete implementation plan structure"""
    id: str
    project_overview: Dict[str, Any]
    technical_specifications: Dict[str, Any]
    tasks: List[Task]
    timeline_estimate: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    created_at: float = None
    updated_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert tasks to dict format
        data["tasks"] = [task.to_dict() if isinstance(task, Task) else task for task in self.tasks]
        return data


class ManagerPlannerAgent(BaseAgent):
    """Manager/Planner Agent for creating detailed implementation plans"""
    
    def __init__(self, model_wrapper: MistralModelWrapper):
        super().__init__("ManagerPlannerAgent", model_wrapper)
        self.project_templates = self._load_project_templates()
        self.max_tasks_per_plan = 20
    
    def _load_project_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load project templates for different types"""
        return {
            "web_application": {
                "default_tasks": [
                    "Setup project structure and dependencies",
                    "Implement frontend components",
                    "Create backend API endpoints",
                    "Setup database schema and models",
                    "Implement authentication system",
                    "Add error handling and validation",
                    "Create tests and documentation",
                    "Setup deployment configuration"
                ],
                "tech_specs": {
                    "architecture": "Client-Server",
                    "patterns": ["MVC", "REST API"],
                    "considerations": ["Responsive design", "Security", "Performance"]
                }
            },
            "api": {
                "default_tasks": [
                    "Design API schema and endpoints",
                    "Setup project structure",
                    "Implement core API logic",
                    "Add authentication and authorization",
                    "Implement data validation",
                    "Add error handling and logging",
                    "Create API documentation",
                    "Setup testing framework"
                ],
                "tech_specs": {
                    "architecture": "REST/GraphQL API",
                    "patterns": ["Repository Pattern", "Dependency Injection"],
                    "considerations": ["Rate limiting", "Caching", "Monitoring"]
                }
            },
            "cli_tool": {
                "default_tasks": [
                    "Setup project structure",
                    "Implement command parsing",
                    "Create core functionality",
                    "Add configuration support",
                    "Implement error handling",
                    "Create help and documentation",
                    "Add testing framework",
                    "Setup packaging and distribution"
                ],
                "tech_specs": {
                    "architecture": "Command Pattern",
                    "patterns": ["Factory Pattern", "Strategy Pattern"],
                    "considerations": ["Cross-platform compatibility", "Performance"]
                }
            }
        }
    
    async def process(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResult:
        """Process requirements and create implementation plan"""
        try:
            if isinstance(input_data, dict) and "requirements_summary" in input_data:
                return await self._create_implementation_plan(input_data["requirements_summary"], context)
            elif isinstance(input_data, dict) and "plan_review" in input_data:
                return await self._review_and_update_plan(input_data, context)
            else:
                return AgentResult(
                    success=False,
                    error=f"Unsupported input format. Expected requirements_summary or plan_review."
                )
        
        except Exception as e:
            logger.error("Error processing requirements", error=str(e))
            return AgentResult(
                success=False,
                error=str(e)
            )
    
    async def _create_implementation_plan(self, requirements: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """Create detailed implementation plan from requirements"""
        self.logger.info("Creating implementation plan", project_type=requirements.get("project_overview", {}).get("type"))
        
        project_overview = requirements.get("project_overview", {})
        project_type = project_overview.get("type", "general")
        
        # Generate AI-enhanced plan
        ai_plan_result = await self._generate_ai_enhanced_plan(requirements)
        
        if not ai_plan_result["success"]:
            # Fallback to template-based plan
            self.logger.warning("AI plan generation failed, using template fallback")
            plan = self._create_template_based_plan(requirements)
        else:
            plan = ai_plan_result["plan"]
        
        # Validate and enhance the plan
        validated_plan = self._validate_and_enhance_plan(plan, requirements)
        
        return AgentResult(
            success=True,
            data={
                "implementation_plan": validated_plan.to_dict(),
                "next_action": "begin_implementation",
                "status": "plan_ready"
            },
            tokens_used=ai_plan_result.get("tokens_used", 0)
        )
    
    async def _generate_ai_enhanced_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate implementation plan using AI"""
        try:
            # Format requirements for AI
            requirements_text = json.dumps(requirements, indent=2)
            
            # Generate plan using AI
            ai_response = await self.model_wrapper.generate_manager_plan(requirements_text)
            
            # Parse AI response into structured plan
            structured_plan = self._parse_ai_plan_response(ai_response, requirements)
            
            return {
                "success": True,
                "plan": structured_plan,
                "ai_response": ai_response,
                "tokens_used": 150  # Estimate
            }
        
        except Exception as e:
            logger.error("AI plan generation failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_ai_plan_response(self, ai_response: Dict[str, Any], requirements: Dict[str, Any]) -> ImplementationPlan:
        """Parse AI response into structured plan"""
        project_overview = requirements.get("project_overview", {})
        
        # Extract plan data from AI response
        plan_data = ai_response if isinstance(ai_response, dict) else {}
        
        # Create tasks from AI response
        tasks = []
        ai_tasks = plan_data.get("tasks", [])
        
        for i, task_data in enumerate(ai_tasks[:self.max_tasks_per_plan]):
            if isinstance(task_data, dict):
                task = Task(
                    id=task_data.get("id", f"task_{i+1}"),
                    title=task_data.get("title", f"Task {i+1}"),
                    description=task_data.get("description", ""),
                    priority=TaskPriority(task_data.get("priority", "medium")),
                    status=TaskStatus.PENDING,
                    estimated_hours=float(task_data.get("estimated_hours", 4.0)),
                    dependencies=task_data.get("dependencies", []),
                    acceptance_criteria=task_data.get("acceptance_criteria", []),
                    technical_notes=task_data.get("technical_notes", "")
                )
            else:
                # Handle string tasks
                task = Task(
                    id=f"task_{i+1}",
                    title=str(task_data)[:100],
                    description=str(task_data),
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.PENDING,
                    estimated_hours=4.0
                )
            tasks.append(task)
        
        # Calculate timeline
        total_hours = sum(task.estimated_hours for task in tasks)
        timeline_estimate = {
            "total_estimated_hours": total_hours,
            "estimated_days": max(1, int(total_hours / 8)),
            "complexity_level": self._assess_complexity(total_hours, len(tasks))
        }
        
        return ImplementationPlan(
            id=str(uuid.uuid4()),
            project_overview=project_overview,
            technical_specifications=plan_data.get("technical_specifications", {}),
            tasks=tasks,
            timeline_estimate=timeline_estimate,
            risk_assessment=plan_data.get("risk_assessment", {})
        )
    
    def _create_template_based_plan(self, requirements: Dict[str, Any]) -> ImplementationPlan:
        """Create plan using templates as fallback"""
        project_overview = requirements.get("project_overview", {})
        project_type = project_overview.get("type", "general")
        
        template = self.project_templates.get(project_type, self.project_templates["web_application"])
        
        # Create tasks from template
        tasks = []
        for i, task_title in enumerate(template["default_tasks"]):
            task = Task(
                id=f"task_{i+1}",
                title=task_title,
                description=f"Implement {task_title.lower()}",
                priority=TaskPriority.HIGH if i < 3 else TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                estimated_hours=6.0,
                acceptance_criteria=[f"Complete {task_title.lower()} implementation"]
            )
            tasks.append(task)
        
        # Add dependencies
        for i in range(1, len(tasks)):
            if i < 4:  # First few tasks depend on previous
                tasks[i].dependencies = [tasks[i-1].id]
        
        total_hours = sum(task.estimated_hours for task in tasks)
        
        return ImplementationPlan(
            id=str(uuid.uuid4()),
            project_overview=project_overview,
            technical_specifications=template["tech_specs"],
            tasks=tasks,
            timeline_estimate={
                "total_estimated_hours": total_hours,
                "estimated_days": max(1, int(total_hours / 8)),
                "complexity_level": self._assess_complexity(total_hours, len(tasks))
            },
            risk_assessment={
                "technical_risks": ["Integration complexity", "Performance requirements"],
                "timeline_risks": ["Scope creep", "Technical debt"],
                "mitigation_strategies": ["Regular testing", "Iterative development"]
            }
        )
    
    def _validate_and_enhance_plan(self, plan: ImplementationPlan, requirements: Dict[str, Any]) -> ImplementationPlan:
        """Validate and enhance the implementation plan"""
        
        # Ensure all tasks have proper IDs
        for i, task in enumerate(plan.tasks):
            if not task.id:
                task.id = f"task_{i+1}"
        
        # Add missing acceptance criteria
        for task in plan.tasks:
            if not task.acceptance_criteria:
                task.acceptance_criteria = [
                    f"Implementation of {task.title} is complete",
                    f"Code passes quality checks",
                    f"Basic testing is completed"
                ]
        
        # Update technical specifications based on requirements
        tech_reqs = requirements.get("technical_requirements", {})
        if tech_reqs.get("technology_preferences"):
            plan.technical_specifications["preferred_technologies"] = tech_reqs["technology_preferences"]
        if tech_reqs.get("constraints"):
            plan.technical_specifications["constraints"] = tech_reqs["constraints"]
        
        plan.updated_at = time.time()
        return plan
    
    def _assess_complexity(self, total_hours: float, task_count: int) -> str:
        """Assess project complexity"""
        if total_hours > 80 or task_count > 15:
            return "high"
        elif total_hours > 40 or task_count > 8:
            return "medium"
        else:
            return "low"
    
    async def _review_and_update_plan(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """Review and update existing plan based on feedback"""
        plan_review = input_data["plan_review"]
        current_plan = input_data.get("current_plan")
        
        if not current_plan:
            return AgentResult(
                success=False,
                error="No current plan provided for review"
            )
        
        # Update plan based on review
        # This could involve AI analysis of what needs to be changed
        
        return AgentResult(
            success=True,
            data={
                "updated_plan": current_plan,
                "review_applied": True,
                "next_action": "continue_implementation"
            }
        )
    
    def get_plan_summary(self, plan: ImplementationPlan) -> Dict[str, Any]:
        """Get a summary of the implementation plan"""
        return {
            "plan_id": plan.id,
            "project_type": plan.project_overview.get("type"),
            "total_tasks": len(plan.tasks),
            "estimated_hours": plan.timeline_estimate.get("total_estimated_hours"),
            "estimated_days": plan.timeline_estimate.get("estimated_days"),
            "complexity": plan.timeline_estimate.get("complexity_level"),
            "high_priority_tasks": len([t for t in plan.tasks if t.priority == TaskPriority.HIGH]),
            "critical_tasks": len([t for t in plan.tasks if t.priority == TaskPriority.CRITICAL])
        }