"""
Q&A Intake Agent - Gathers detailed requirements from users
"""
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import structlog

from app.agents.base import BaseAgent, AgentResult
from app.models.mistral import MistralModelWrapper

logger = structlog.get_logger(__name__)


@dataclass
class RequirementsState:
    """Tracks requirements gathering state"""
    user_request: str = ""
    project_type: str = ""
    platform: str = ""
    features: List[str] = None
    technology_preferences: List[str] = None
    timeline: str = ""
    complexity: str = ""
    constraints: List[str] = None
    clarifications: List[Dict[str, str]] = None
    completeness_score: float = 0.0
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.technology_preferences is None:
            self.technology_preferences = []
        if self.constraints is None:
            self.constraints = []
        if self.clarifications is None:
            self.clarifications = []


class QAIntakeAgent(BaseAgent):
    """Q&A Intake Agent for gathering detailed user requirements"""
    
    def __init__(self, model_wrapper: MistralModelWrapper):
        super().__init__("QAIntakeAgent", model_wrapper)
        self.requirements_templates = self._load_question_templates()
        self.min_completeness_score = 0.7  # Threshold for completion
    
    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load question templates for different project types"""
        return {
            "web_application": [
                "What type of web application do you want to build? (e.g., blog, e-commerce, dashboard)",
                "Do you have preferences for frontend frameworks? (React, Vue, Angular, etc.)",
                "What backend technology would you prefer? (Node.js, Python, etc.)",
                "Do you need user authentication and authorization?",
                "What database requirements do you have?",
                "Do you need any third-party integrations?",
                "What are your hosting/deployment preferences?"
            ],
            "api": [
                "What type of API are you building? (REST, GraphQL, etc.)",
                "What data will your API handle?",
                "Do you need authentication/authorization?",
                "What are your performance requirements?",
                "Do you need documentation (OpenAPI/Swagger)?",
                "What database or data storage do you prefer?",
                "Any specific compliance requirements?"
            ],
            "cli_tool": [
                "What should your CLI tool accomplish?",
                "What commands or operations should it support?",
                "Do you need configuration file support?",
                "What input/output formats are required?",
                "Any specific libraries or frameworks preferred?",
                "Do you need package distribution (pip, npm, etc.)?"
            ],
            "data_analysis": [
                "What type of data will you be analyzing?",
                "What analysis or insights do you want to generate?",
                "Do you need visualization capabilities?",
                "What data sources will you connect to?",
                "Any specific analysis libraries preferred?",
                "Do you need automated reporting?"
            ],
            "general": [
                "Can you describe what you want to build in more detail?",
                "What problem are you trying to solve?",
                "Who are the intended users?",
                "What platforms should it support?",
                "Do you have any technology preferences?",
                "What are your main functional requirements?",
                "Are there any constraints or limitations to consider?"
            ]
        }
    
    async def process(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResult:
        """Process user input and gather requirements"""
        try:
            if isinstance(input_data, str):
                # Initial user request
                return await self._handle_initial_request(input_data, context)
            elif isinstance(input_data, dict):
                # Follow-up responses
                return await self._handle_followup_response(input_data, context)
            else:
                return AgentResult(
                    success=False,
                    error=f"Unsupported input type: {type(input_data)}"
                )
        
        except Exception as e:
            logger.error("Error processing input", error=str(e))
            return AgentResult(
                success=False,
                error=str(e)
            )
    
    async def _handle_initial_request(self, user_request: str, context: Dict[str, Any]) -> AgentResult:
        """Handle initial user request"""
        self.logger.info("Processing initial user request", request_length=len(user_request))
        
        # Initialize requirements state
        requirements_state = RequirementsState(user_request=user_request)
        
        # Determine project type from request
        project_type = self._classify_project_type(user_request)
        requirements_state.project_type = project_type
        
        # Generate clarifying questions using AI
        questions_result = await self._generate_clarifying_questions(
            user_request, project_type
        )
        
        if not questions_result["success"]:
            return AgentResult(
                success=False,
                error=questions_result["error"]
            )
        
        # Calculate initial completeness
        requirements_state.completeness_score = self._calculate_completeness(requirements_state)
        
        return AgentResult(
            success=True,
            data={
                "questions": questions_result["questions"],
                "project_type": project_type,
                "requirements_state": requirements_state,
                "next_action": "await_user_responses",
                "completeness_score": requirements_state.completeness_score
            },
            tokens_used=questions_result.get("tokens_used", 0)
        )
    
    async def _handle_followup_response(self, response_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """Handle user responses to clarifying questions"""
        self.logger.info("Processing follow-up responses")
        
        # Extract current state
        requirements_state = response_data.get("requirements_state", RequirementsState())
        user_responses = response_data.get("responses", {})
        
        # Update requirements state with responses
        self._update_requirements_from_responses(requirements_state, user_responses)
        
        # Calculate completeness
        completeness_score = self._calculate_completeness(requirements_state)
        requirements_state.completeness_score = completeness_score
        
        if completeness_score >= self.min_completeness_score:
            # Requirements are complete enough
            requirements_summary = self._generate_requirements_summary(requirements_state)
            
            return AgentResult(
                success=True,
                data={
                    "requirements_summary": requirements_summary,
                    "requirements_state": requirements_state,
                    "next_action": "proceed_to_planning",
                    "completeness_score": completeness_score,
                    "status": "requirements_complete"
                }
            )
        else:
            # Need more clarification
            additional_questions = await self._generate_additional_questions(
                requirements_state, user_responses
            )
            
            return AgentResult(
                success=True,
                data={
                    "questions": additional_questions["questions"],
                    "requirements_state": requirements_state,
                    "next_action": "await_user_responses",
                    "completeness_score": completeness_score,
                    "status": "needs_more_info"
                },
                tokens_used=additional_questions.get("tokens_used", 0)
            )
    
    def _classify_project_type(self, user_request: str) -> str:
        """Classify project type from user request"""
        request_lower = user_request.lower()
        
        # Simple keyword-based classification
        if any(word in request_lower for word in ["web", "website", "webapp", "frontend", "react", "vue"]):
            return "web_application"
        elif any(word in request_lower for word in ["api", "rest", "graphql", "backend", "service"]):
            return "api"
        elif any(word in request_lower for word in ["cli", "command", "terminal", "script"]):
            return "cli_tool"
        elif any(word in request_lower for word in ["data", "analysis", "analytics", "visualization"]):
            return "data_analysis"
        else:
            return "general"
    
    async def _generate_clarifying_questions(self, user_request: str, project_type: str) -> Dict[str, Any]:
        """Generate AI-powered clarifying questions"""
        try:
            # Get template questions
            template_questions = self.requirements_templates.get(project_type, self.requirements_templates["general"])
            
            # Use AI to generate personalized questions
            ai_response = await self.model_wrapper.generate_qa_response(user_request)
            
            # Parse AI response for questions
            ai_questions = self._extract_questions_from_response(ai_response)
            
            # Combine template and AI questions
            all_questions = template_questions[:3] + ai_questions[:2]  # Limit to 5 questions
            
            return {
                "success": True,
                "questions": all_questions,
                "ai_response": ai_response,
                "tokens_used": 100  # Estimate
            }
        
        except Exception as e:
            logger.error("Failed to generate questions", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "questions": self.requirements_templates.get(project_type, self.requirements_templates["general"])[:3]
            }
    
    def _extract_questions_from_response(self, response: str) -> List[str]:
        """Extract questions from AI response"""
        questions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.endswith('?') and len(line) > 10:
                # Clean up the question
                question = line.lstrip('- ').lstrip('* ').lstrip('1234567890. ')
                questions.append(question)
        
        return questions[:5]  # Limit to 5 questions
    
    def _update_requirements_from_responses(self, state: RequirementsState, responses: Dict[str, Any]):
        """Update requirements state from user responses"""
        for key, value in responses.items():
            if hasattr(state, key) and value:
                if isinstance(getattr(state, key), list):
                    # Handle list fields
                    if isinstance(value, list):
                        setattr(state, key, value)
                    else:
                        current_list = getattr(state, key)
                        current_list.append(str(value))
                else:
                    # Handle string fields
                    setattr(state, key, str(value))
        
        # Add responses to clarifications
        state.clarifications.append({
            "timestamp": time.time(),
            "responses": responses
        })
    
    def _calculate_completeness(self, state: RequirementsState) -> float:
        """Calculate requirements completeness score"""
        total_fields = 8  # Number of key fields
        completed_fields = 0
        
        if state.user_request:
            completed_fields += 1
        if state.project_type:
            completed_fields += 1
        if state.platform:
            completed_fields += 1
        if state.features:
            completed_fields += 1
        if state.technology_preferences:
            completed_fields += 1
        if state.timeline:
            completed_fields += 1
        if state.complexity:
            completed_fields += 1
        if state.constraints:
            completed_fields += 1
        
        return completed_fields / total_fields
    
    async def _generate_additional_questions(self, state: RequirementsState, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate additional clarifying questions based on current state"""
        missing_info = []
        
        if not state.platform:
            missing_info.append("target platform")
        if not state.features:
            missing_info.append("key features")
        if not state.technology_preferences:
            missing_info.append("technology preferences")
        if not state.timeline:
            missing_info.append("timeline expectations")
        
        # Generate targeted questions
        questions = []
        if "target platform" in missing_info:
            questions.append("What platform(s) should this run on? (Web, mobile, desktop, etc.)")
        if "key features" in missing_info:
            questions.append("What are the main features or capabilities you need?")
        if "technology preferences" in missing_info:
            questions.append("Do you have any preferred technologies or frameworks?")
        if "timeline expectations" in missing_info:
            questions.append("What's your expected timeline for this project?")
        
        return {
            "success": True,
            "questions": questions[:3],  # Limit to 3 additional questions
            "tokens_used": 50
        }
    
    def _generate_requirements_summary(self, state: RequirementsState) -> Dict[str, Any]:
        """Generate final requirements summary"""
        return {
            "project_overview": {
                "type": state.project_type,
                "description": state.user_request,
                "platform": state.platform,
                "complexity": state.complexity
            },
            "functional_requirements": {
                "features": state.features,
                "timeline": state.timeline
            },
            "technical_requirements": {
                "technology_preferences": state.technology_preferences,
                "constraints": state.constraints
            },
            "metadata": {
                "completeness_score": state.completeness_score,
                "clarification_rounds": len(state.clarifications),
                "generated_at": time.time()
            }
        }