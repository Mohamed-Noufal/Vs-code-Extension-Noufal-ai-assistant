"""
Pytest configuration and fixtures for Multi-Agent Development System tests
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Generator

from app.models.manager import ModelManager
from app.orchestrator.workflow import WorkflowManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_model_manager():
    """Create a mock model manager for testing"""
    manager = ModelManager()
    
    # Mock the Ollama client
    manager.client = MagicMock()
    manager.is_connected = True
    manager.model_name = "mistral:7b-instruct"
    
    # Mock the generate method
    manager.generate = AsyncMock()
    manager.generate.return_value = {
        "text": "Mock response from Ollama",
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        },
        "finish_reason": "stop"
    }
    
    return manager


@pytest.fixture
async def mock_workflow_manager(mock_model_manager):
    """Create a mock workflow manager for testing"""
    manager = WorkflowManager(mock_model_manager)
    await manager.initialize()
    return manager


@pytest.fixture
def sample_user_request():
    """Sample user request for testing"""
    return "I want to create a simple web application with a login form"


@pytest.fixture
def sample_requirements():
    """Sample requirements for testing"""
    return """
    Project: Simple Web Application
    Features:
    - User login form
    - Dashboard page
    - User authentication
    Technology: React + Node.js
    """


@pytest.fixture
def sample_task_details():
    """Sample task details for testing"""
    return """
    Task: Implement user login form
    Requirements:
    - Email and password fields
    - Form validation
    - Submit button
    - Error handling
    """


@pytest.fixture
def sample_project_context():
    """Sample project context for testing"""
    return """
    Project: React web application
    Current structure:
    - src/components/
    - src/pages/
    - src/utils/
    Dependencies: React, React Router, Axios
    """
