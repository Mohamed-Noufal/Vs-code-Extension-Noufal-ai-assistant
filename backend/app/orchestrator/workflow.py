"""
LangGraph Workflow Manager - Orchestrates multi-agent workflows
"""
import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import structlog
from langgraph.graph import StateGraph, END

from app.models.manager import ModelManager
from app.models.mistral import MistralModelWrapper
from app.agents.intake import QAIntakeAgent
from app.agents.manager import ManagerPlannerAgent
from app.agents.code import CodeAgent
from app.core.config import settings

logger = structlog.get_logger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class WorkflowState:
    """Shared state for workflow execution"""
    workflow_id: str
    user_request: str
    current_step: str
    status: WorkflowStatus
    
    # Agent data
    requirements_data: Dict[str, Any] = None
    plan_data: Dict[str, Any] = None
    implementation_data: Dict[str, Any] = None
    
    # Execution metadata
    started_at: float = None
    completed_at: float = None
    total_tokens_used: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.requirements_data is None:
            self.requirements_data = {}
        if self.plan_data is None:
            self.plan_data = {}
        if self.implementation_data is None:
            self.implementation_data = {}
        if self.errors is None:
            self.errors = []
        if self.started_at is None:
            self.started_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class WorkflowManager:
    """Manages LangGraph workflow execution for multi-agent system"""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.model_wrapper = None
        self.agents = {}
        self.workflow_graph = None
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.max_concurrent_workflows = settings.MAX_CONCURRENT_WORKFLOWS
    
    async def initialize(self):
        """Initialize workflow manager and agents"""
        logger.info("Initializing workflow manager")
        
        # Create model wrapper
        self.model_wrapper = MistralModelWrapper(self.model_manager)
        
        # Initialize agents
        self.agents = {
            "qa_intake": QAIntakeAgent(self.model_wrapper),
            "manager": ManagerPlannerAgent(self.model_wrapper),
            "code": CodeAgent(self.model_wrapper)
        }
        
        # Build workflow graph
        self._build_workflow_graph()
        
        logger.info("Workflow manager initialized successfully")
    
    def _build_workflow_graph(self):
        """Build LangGraph workflow"""
        
        # Create state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (agents)
        workflow.add_node("qa_intake", self._qa_intake_node)
        workflow.add_node("manager", self._manager_node)
        workflow.add_node("code", self._code_node)
        workflow.add_node("review", self._review_node)
        
        # Add edges (workflow flow)
        workflow.set_entry_point("qa_intake")
        
        workflow.add_conditional_edges(
            "qa_intake",
            self._qa_routing_condition,
            {
                "continue_qa": "qa_intake",
                "proceed_to_planning": "manager",
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "manager",
            self._manager_routing_condition,
            {
                "proceed_to_code": "code",
                "revise_plan": "manager",
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "code",
            self._code_routing_condition,
            {
                "proceed_to_review": "review",
                "revise_code": "code",
                "complete": END,
                "error": END
            }
        )
        
        workflow.add_conditional_edges(
            "review",
            self._review_routing_condition,
            {
                "approve": END,
                "request_revision": "code",
                "back_to_planning": "manager"
            }
        )
        
        self.workflow_graph = workflow.compile()
    
    async def _qa_intake_node(self, state: WorkflowState) -> WorkflowState:
        """Q&A Intake Agent node"""
        logger.info("Executing Q&A Intake node", workflow_id=state.workflow_id)
        
        state.current_step = "qa_intake"
        
        try:
            # Determine input for QA agent
            if not state.requirements_data:
                # Initial request
                input_data = state.user_request
            else:
                # Follow-up with responses
                input_data = {
                    "requirements_state": state.requirements_data.get("requirements_state"),
                    "responses": state.requirements_data.get("user_responses", {})
                }
            
            # Execute QA agent
            result = await self.agents["qa_intake"].execute(input_data)
            
            if result.success:
                state.requirements_data = result.data
                state.total_tokens_used += result.tokens_used
            else:
                state.errors.append(f"QA Intake failed: {result.error}")
                state.status = WorkflowStatus.FAILED
            
        except Exception as e:
            logger.error("QA Intake node failed", error=str(e))
            state.errors.append(f"QA Intake error: {str(e)}")
            state.status = WorkflowStatus.FAILED
        
        return state
    
    async def _manager_node(self, state: WorkflowState) -> WorkflowState:
        """Manager/Planner Agent node"""
        logger.info("Executing Manager node", workflow_id=state.workflow_id)
        
        state.current_step = "manager"
        
        try:
            # Execute Manager agent
            result = await self.agents["manager"].execute(state.requirements_data)
            
            if result.success:
                state.plan_data = result.data
                state.total_tokens_used += result.tokens_used
            else:
                state.errors.append(f"Manager failed: {result.error}")
                state.status = WorkflowStatus.FAILED
            
        except Exception as e:
            logger.error("Manager node failed", error=str(e))
            state.errors.append(f"Manager error: {str(e)}")
            state.status = WorkflowStatus.FAILED
        
        return state
    
    async def _code_node(self, state: WorkflowState) -> WorkflowState:
        """Code Agent node"""
        logger.info("Executing Code node", workflow_id=state.workflow_id)
        
        state.current_step = "code"
        
        try:
            # Get first pending task from plan
            plan = state.plan_data.get("implementation_plan", {})
            tasks = plan.get("tasks", [])
            
            # Find first pending task
            pending_task = None
            for task in tasks:
                if task.get("status") == "pending":
                    pending_task = task
                    break
            
            if not pending_task:
                # No more tasks to implement
                state.implementation_data["all_tasks_complete"] = True
                return state
            
            # Execute Code agent for this task
            input_data = {
                "task": pending_task,
                "project_context": {
                    "project_overview": plan.get("project_overview", {}),
                    "technical_specifications": plan.get("technical_specifications", {}),
                    "completed_tasks": [t for t in tasks if t.get("status") == "completed"]
                }
            }
            
            result = await self.agents["code"].execute(input_data)
            
            if result.success:
                # Update implementation data
                if "implementations" not in state.implementation_data:
                    state.implementation_data["implementations"] = []
                
                state.implementation_data["implementations"].append(result.data)
                state.total_tokens_used += result.tokens_used
                
                # Mark task as completed
                pending_task["status"] = "completed"
                
            else:
                state.errors.append(f"Code generation failed: {result.error}")
                if result.data and result.data.get("revision_required"):
                    # Quality issues - keep in revision loop
                    state.implementation_data["revision_required"] = True
                    state.implementation_data["quality_issues"] = result.data.get("quality_issues", [])
                else:
                    state.status = WorkflowStatus.FAILED
            
        except Exception as e:
            logger.error("Code node failed", error=str(e))
            state.errors.append(f"Code error: {str(e)}")
            state.status = WorkflowStatus.FAILED
        
        return state
    
    async def _review_node(self, state: WorkflowState) -> WorkflowState:
        """Review node for Manager oversight"""
        logger.info("Executing Review node", workflow_id=state.workflow_id)
        
        state.current_step = "review"
        
        try:
            # Simple review logic - check if all tasks are completed
            plan = state.plan_data.get("implementation_plan", {})
            tasks = plan.get("tasks", [])
            
            completed_tasks = [t for t in tasks if t.get("status") == "completed"]
            total_tasks = len(tasks)
            
            if len(completed_tasks) == total_tasks and total_tasks > 0:
                # All tasks completed
                state.implementation_data["review_status"] = "approved"
                state.status = WorkflowStatus.COMPLETED
                state.completed_at = time.time()
            else:
                # More tasks to complete
                state.implementation_data["review_status"] = "continue_implementation"
            
        except Exception as e:
            logger.error("Review node failed", error=str(e))
            state.errors.append(f"Review error: {str(e)}")
            state.status = WorkflowStatus.FAILED
        
        return state
    
    def _qa_routing_condition(self, state: WorkflowState) -> str:
        """Routing condition for QA node"""
        if state.status == WorkflowStatus.FAILED:
            return "error"
        
        qa_data = state.requirements_data
        if qa_data and qa_data.get("next_action") == "proceed_to_planning":
            return "proceed_to_planning"
        elif qa_data and qa_data.get("next_action") == "await_user_responses":
            return "continue_qa"
        else:
            return "error"
    
    def _manager_routing_condition(self, state: WorkflowState) -> str:
        """Routing condition for Manager node"""
        if state.status == WorkflowStatus.FAILED:
            return "error"
        
        plan_data = state.plan_data
        if plan_data and plan_data.get("next_action") == "begin_implementation":
            return "proceed_to_code"
        else:
            return "error"
    
    def _code_routing_condition(self, state: WorkflowState) -> str:
        """Routing condition for Code node"""
        if state.status == WorkflowStatus.FAILED:
            return "error"
        
        impl_data = state.implementation_data
        
        if impl_data.get("revision_required"):
            return "revise_code"
        elif impl_data.get("all_tasks_complete"):
            return "complete"
        else:
            return "proceed_to_review"
    
    def _review_routing_condition(self, state: WorkflowState) -> str:
        """Routing condition for Review node"""
        impl_data = state.implementation_data
        review_status = impl_data.get("review_status")
        
        if review_status == "approved":
            return "approve"
        elif review_status == "continue_implementation":
            return "request_revision"
        else:
            return "back_to_planning"
    
    async def start_workflow(self, user_request: str, user_id: str = None) -> str:
        """Start a new workflow"""
        
        # Check concurrent workflow limit
        if len(self.active_workflows) >= self.max_concurrent_workflows:
            raise RuntimeError(f"Maximum concurrent workflows ({self.max_concurrent_workflows}) reached")
        
        # Create workflow state
        workflow_id = str(uuid.uuid4())
        state = WorkflowState(
            workflow_id=workflow_id,
            user_request=user_request,
            current_step="pending",
            status=WorkflowStatus.PENDING
        )
        
        self.active_workflows[workflow_id] = state
        
        logger.info("Started new workflow", workflow_id=workflow_id, user_id=user_id)
        
        # Start workflow execution in background
        asyncio.create_task(self._execute_workflow(workflow_id))
        
        return workflow_id
    
    async def _execute_workflow(self, workflow_id: str):
        """Execute workflow in background"""
        try:
            state = self.active_workflows[workflow_id]
            state.status = WorkflowStatus.RUNNING
            
            logger.info("Executing workflow", workflow_id=workflow_id)
            
            # Execute workflow graph
            final_state = await self.workflow_graph.ainvoke(state)
            
            # Update final state
            self.active_workflows[workflow_id] = final_state
            
            if final_state.status != WorkflowStatus.FAILED:
                final_state.status = WorkflowStatus.COMPLETED
                final_state.completed_at = time.time()
            
            logger.info("Workflow completed", workflow_id=workflow_id, status=final_state.status.value)
            
        except Exception as e:
            logger.error("Workflow execution failed", workflow_id=workflow_id, error=str(e))
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id].status = WorkflowStatus.FAILED
                self.active_workflows[workflow_id].errors.append(f"Execution error: {str(e)}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        if workflow_id not in self.active_workflows:
            return None
        
        state = self.active_workflows[workflow_id]
        return state.to_dict()
    
    def get_agent_info(self) -> List[Dict[str, Any]]:
        """Get information about all agents"""
        return [
            agent.get_stats() for agent in self.agents.values()
        ]
    
    def health_check(self) -> str:
        """Check workflow manager health"""
        if not self.workflow_graph:
            return "not_initialized"
        if not self.model_wrapper:
            return "model_not_available"
        return "healthy"
    
    async def shutdown(self):
        """Shutdown workflow manager"""
        logger.info("Shutting down workflow manager")
        
        # Wait for active workflows to complete (with timeout)
        if self.active_workflows:
            logger.info(f"Waiting for {len(self.active_workflows)} active workflows to complete")
            await asyncio.sleep(2)  # Grace period
        
        # Clear active workflows
        self.active_workflows.clear()