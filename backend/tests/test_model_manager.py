"""
Tests for the ModelManager class with Ollama integration
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.models.manager import ModelManager
from app.core.config import settings


class TestModelManager:
    """Test cases for ModelManager class"""
    
    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of ModelManager"""
        with patch('app.models.manager.ollama.Client') as mock_client:
            # Mock successful connection
            mock_client_instance = MagicMock()
            mock_client_instance.list.return_value = {
                'models': [{'name': 'mistral:7b-instruct'}]
            }
            mock_client.return_value = mock_client_instance
            
            manager = ModelManager()
            await manager.initialize()
            
            assert manager.is_connected is True
            assert manager.model_name == "mistral:7b-instruct"
    
    @pytest.mark.asyncio
    async def test_initialization_ollama_not_running(self):
        """Test initialization when Ollama is not running"""
        with patch('app.models.manager.ollama.Client') as mock_client:
            # Mock connection failure
            mock_client.side_effect = Exception("Connection refused")
            
            manager = ModelManager()
            
            with pytest.raises(RuntimeError, match="Ollama service is not accessible"):
                await manager.initialize()
    
    @pytest.mark.asyncio
    async def test_initialization_model_not_available(self):
        """Test initialization when model is not available"""
        with patch('app.models.manager.ollama.Client') as mock_client:
            # Mock successful connection but model not found
            mock_client_instance = MagicMock()
            mock_client_instance.list.return_value = {
                'models': [{'name': 'other-model'}]
            }
            mock_client_instance.pull.return_value = None
            mock_client.return_value = mock_client_instance
            
            manager = ModelManager()
            await manager.initialize()
            
            # Should pull the model and continue
            assert manager.is_connected is True
            mock_client_instance.pull.assert_called_once_with("mistral:7b-instruct")
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self):
        """Test successful text generation"""
        with patch('app.models.manager.ollama.Client') as mock_client:
            # Mock successful generation
            mock_client_instance = MagicMock()
            mock_client_instance.generate.return_value = {
                'response': 'Generated text response',
                'done': True
            }
            mock_client.return_value = mock_client_instance
            
            manager = ModelManager()
            manager.is_connected = True
            manager.model_name = "mistral:7b-instruct"
            
            result = await manager.generate("Test prompt", max_tokens=100)
            
            assert result["text"] == "Generated text response"
            assert result["finish_reason"] == "stop"
            assert manager.stats["total_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_text_not_initialized(self):
        """Test text generation when not initialized"""
        manager = ModelManager()
        manager.is_connected = False
        
        with pytest.raises(RuntimeError, match="Ollama model manager not initialized"):
            await manager.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_text_with_stop_sequences(self):
        """Test text generation with stop sequences"""
        with patch('app.models.manager.ollama.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.generate.return_value = {
                'response': 'Generated text',
                'done': True
            }
            mock_client.return_value = mock_client_instance
            
            manager = ModelManager()
            manager.is_connected = True
            manager.model_name = "mistral:7b-instruct"
            
            stop_sequences = ["[INST]", "</s>"]
            await manager.generate("Test prompt", stop_sequences=stop_sequences)
            
            # Verify stop sequences were passed to Ollama
            call_args = mock_client_instance.generate.call_args
            assert call_args[1]['options']['stop'] == stop_sequences
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check when system is healthy"""
        with patch('app.models.manager.ollama.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.generate.return_value = {
                'response': 'Test',
                'done': True
            }
            mock_client.return_value = mock_client_instance
            
            manager = ModelManager()
            manager.is_connected = True
            manager.model_name = "mistral:7b-instruct"
            
            health_status = await manager.health_check()
            assert health_status == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_not_connected(self):
        """Test health check when not connected"""
        manager = ModelManager()
        manager.is_connected = False
        
        health_status = await manager.health_check()
        assert health_status == "not_connected"
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check when generation fails"""
        with patch('app.models.manager.ollama.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.generate.side_effect = Exception("Generation failed")
            mock_client.return_value = mock_client_instance
            
            manager = ModelManager()
            manager.is_connected = True
            manager.model_name = "mistral:7b-instruct"
            
            health_status = await manager.health_check()
            assert health_status == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting model statistics"""
        manager = ModelManager()
        manager.is_connected = True
        manager.model_name = "mistral:7b-instruct"
        manager.stats["total_requests"] = 5
        manager.stats["total_tokens"] = 100
        
        stats = manager.get_stats()
        
        assert stats["model_name"] == "mistral:7b-instruct"
        assert stats["is_connected"] is True
        assert stats["model_type"] == "ollama"
        assert stats["ollama_url"] == settings.OLLAMA_BASE_URL
        assert stats["total_requests"] == 5
        assert stats["total_tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test model manager shutdown"""
        manager = ModelManager()
        manager.is_connected = True
        
        await manager.shutdown()
        
        assert manager.is_connected is False
    
    @pytest.mark.asyncio
    async def test_generate_with_custom_parameters(self):
        """Test text generation with custom temperature and top_p"""
        with patch('app.models.manager.ollama.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.generate.return_value = {
                'response': 'Custom response',
                'done': True
            }
            mock_client.return_value = mock_client_instance
            
            manager = ModelManager()
            manager.is_connected = True
            manager.model_name = "mistral:7b-instruct"
            
            await manager.generate(
                "Test prompt",
                max_tokens=200,
                temperature=0.5,
                top_p=0.8
            )
            
            # Verify custom parameters were passed
            call_args = mock_client_instance.generate.call_args
            assert call_args[1]['options']['temperature'] == 0.5
            assert call_args[1]['options']['top_p'] == 0.8
            assert call_args[1]['options']['num_predict'] == 200
