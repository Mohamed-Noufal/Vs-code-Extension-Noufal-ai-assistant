"""
Tests for the MistralPromptTemplate class
"""
import pytest
import json
from app.models.mistral import MistralPromptTemplate


class TestMistralPromptTemplate:
    """Test cases for MistralPromptTemplate class"""
    
    def test_instruction_template_format(self):
        """Test instruction template formatting"""
        instruction = "Write a Python function"
        formatted = MistralPromptTemplate.INSTRUCTION_TEMPLATE.format(instruction=instruction)
        
        expected = "<s>[INST] Write a Python function [/INST]"
        assert formatted == expected
    
    def test_qa_agent_prompt_formatting(self):
        """Test Q&A agent prompt formatting"""
        user_request = "I want to build a web app"
        prompt = MistralPromptTemplate.format_qa_prompt(user_request)
        
        assert "[INST]" in prompt
        assert "[/INST]" in prompt
        assert "Q&A Intake Agent" in prompt
        assert user_request in prompt
        assert "development system" in prompt
    
    def test_manager_agent_prompt_formatting(self):
        """Test Manager agent prompt formatting"""
        requirements = "Build a login system"
        prompt = MistralPromptTemplate.format_manager_prompt(requirements)
        
        assert "[INST]" in prompt
        assert "[/INST]" in prompt
        assert "Manager/Planner Agent" in prompt
        assert requirements in prompt
        assert "JSON plan" in prompt
    
    def test_code_agent_prompt_formatting(self):
        """Test Code agent prompt formatting"""
        task_details = "Implement login form"
        project_context = "React application"
        prompt = MistralPromptTemplate.format_code_prompt(task_details, project_context)
        
        assert "[INST]" in prompt
        assert "[/INST]" in prompt
        assert "Code Agent" in prompt
        assert task_details in prompt
        assert project_context in prompt
        assert "production-ready code" in prompt
    
    def test_extract_json_from_response_valid(self):
        """Test JSON extraction from valid response"""
        response = """
        Here is the plan:
        {
            "project": "Web App",
            "tasks": ["login", "dashboard"]
        }
        End of response.
        """
        
        result = MistralPromptTemplate.extract_json_from_response(response)
        
        assert result is not None
        assert result["project"] == "Web App"
        assert result["tasks"] == ["login", "dashboard"]
    
    def test_extract_json_from_response_no_json(self):
        """Test JSON extraction when no JSON is present"""
        response = "This is a plain text response without JSON"
        
        result = MistralPromptTemplate.extract_json_from_response(response)
        
        assert result is None
    
    def test_extract_json_from_response_invalid_json(self):
        """Test JSON extraction with invalid JSON"""
        response = """
        Here is the plan:
        {
            "project": "Web App",
            "tasks": ["login", "dashboard"
        }
        """
        
        result = MistralPromptTemplate.extract_json_from_response(response)
        
        assert result is None
    
    def test_extract_code_from_response_single_block(self):
        """Test code extraction from single code block"""
        response = """Here's the implementation:
```python
def hello():
    print("Hello World")
```
That's the code."""
        
        result = MistralPromptTemplate.extract_code_from_response(response)
        
        assert len(result) == 1
        assert result[0]["language"] == "python"
        assert "def hello():" in result[0]["code"]
    
    def test_extract_code_from_response_multiple_blocks(self):
        """Test code extraction from multiple code blocks"""
        response = """Here are the files:
```javascript
function greet() {
    return "Hello";
}
```

```css
.greeting {
    color: blue;
}
```"""
        
        result = MistralPromptTemplate.extract_code_from_response(response)
        
        assert len(result) == 2
        assert result[0]["language"] == "javascript"
        assert result[1]["language"] == "css"
        assert "function greet" in result[0]["code"]
        assert ".greeting" in result[1]["code"]
    
    def test_extract_code_from_response_no_language(self):
        """Test code extraction from code block without language"""
        response = """Here's the code:
```
echo "Hello World"
```"""
        
        result = MistralPromptTemplate.extract_code_from_response(response)
        
        assert len(result) == 1
        assert result[0]["language"] == "text"
        assert "echo" in result[0]["code"]
    
    def test_extract_code_from_response_no_code_blocks(self):
        """Test code extraction when no code blocks are present"""
        response = "This is a plain text response without any code blocks"
        
        result = MistralPromptTemplate.extract_code_from_response(response)
        
        assert len(result) == 0
    
    def test_system_prompt_content(self):
        """Test system prompt content"""
        system_prompt = MistralPromptTemplate.SYSTEM_PROMPT
        
        assert "professional software engineer" in system_prompt
        assert "software development" in system_prompt
        assert "coding practices" in system_prompt
        assert "technical solutions" in system_prompt
