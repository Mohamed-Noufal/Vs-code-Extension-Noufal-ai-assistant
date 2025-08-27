"""
AI Model Manager - Handles Ollama AI model management and inference
"""
import asyncio
from typing import Dict, Any, Optional, List
import time

import structlog
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ModelManager:
    """Manages Ollama AI model connections and inference"""
    
    def __init__(self):
        self.model_name: Optional[str] = None
        self.client: Optional[ollama.Client] = None
        self.is_connected = False
        self.lock = asyncio.Lock()
        self.stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "average_response_time": 0.0,
            "last_request_time": None
        }
    
    async def initialize(self):
        """Initialize the Ollama model manager"""
        logger.info("Initializing Ollama model manager")
        
        # Check if Ollama is running
        await self._check_ollama_connection()
        
        # Set model name
        self.model_name = settings.MODEL_NAME
        
        # Check if model is available
        await self._ensure_model_available()
        
        self.is_connected = True
        logger.info(f"Ollama model manager initialized with model: {self.model_name}")
    
    async def _check_ollama_connection(self):
        """Check if Ollama service is accessible"""
        try:
            # Test connection to Ollama
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._test_ollama_connection)
            
            # Initialize the client if connection is successful
            self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
            
            logger.info("Ollama service is accessible")
        except Exception as e:
            logger.error("Failed to connect to Ollama service", error=str(e))
            raise RuntimeError(
                "Ollama service is not accessible. Please ensure Ollama is running and accessible at "
                f"{settings.OLLAMA_BASE_URL}"
            )
    
    def _test_ollama_connection(self):
        """Test Ollama connection synchronously"""
        try:
            client = ollama.Client(host=settings.OLLAMA_BASE_URL)
            client.list()  # Test API call
        except Exception as e:
            raise RuntimeError(f"Ollama connection failed: {str(e)}")
    
    async def _ensure_model_available(self) -> None:
        """Ensure the specified model is available, download if necessary"""
        try:
            models = await self._list_models()
            logger.debug("Available models", models=models)
            
            # Check if our model is in the list
            model_names = []
            if 'models' in models:
                for model in models['models']:
                    if isinstance(model, dict) and 'name' in model:
                        model_names.append(model['name'])
                    elif isinstance(model, str):
                        model_names.append(model)
            
            if self.model_name in model_names:
                logger.info("Model is already available", model=self.model_name)
                return
            
            logger.info("Model not found, downloading", model=self.model_name)
            await self._pull_model()
            
        except Exception as e:
            logger.error("Failed to check model availability", error=str(e))
            raise
    
    async def _list_models(self) -> Dict[str, Any]:
        """List available models from Ollama"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.client.list)
            logger.debug("Ollama list models response", response=response)
            return response
        except Exception as e:
            logger.error("Failed to list models", error=str(e))
            raise
    
    async def _pull_model(self):
        """Pull the specified model from Ollama"""
        logger.info(f"Pulling model {self.model_name} from Ollama...")
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._pull_model_sync)
            logger.info(f"Model {self.model_name} pulled successfully")
        except Exception as e:
            logger.error(f"Failed to pull model {self.model_name}", error=str(e))
            raise RuntimeError(f"Failed to pull model {self.model_name}: {str(e)}")
    
    def _pull_model_sync(self):
        """Pull model synchronously"""
        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        client.pull(self.model_name)
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = None,
        top_p: float = None,
        stop_sequences: List[str] = None
    ) -> Dict[str, Any]:
        """Generate text using Ollama model"""
        
        if not self.is_connected:
            raise RuntimeError("Ollama model manager not initialized. Please check initialization.")
        
        # Use default values if not provided
        temperature = temperature or settings.MODEL_TEMPERATURE
        top_p = top_p or settings.MODEL_TOP_P
        
        start_time = time.time()
        
        try:
            logger.debug(
                "Generating text with Ollama",
                model=self.model_name,
                prompt_length=len(prompt),
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Generate using Ollama
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._generate_sync,
                prompt,
                max_tokens,
                temperature,
                top_p,
                stop_sequences
            )
            
            # Update stats
            response_time = time.time() - start_time
            self.stats["total_requests"] += 1
            # Ollama doesn't provide token usage, so we estimate
            estimated_tokens = len(result["text"].split()) * 1.3  # Rough estimate
            self.stats["total_tokens"] += int(estimated_tokens)
            self.stats["last_request_time"] = time.time()
            
            # Update rolling average
            prev_avg = self.stats["average_response_time"]
            total_requests = self.stats["total_requests"]
            self.stats["average_response_time"] = (
                (prev_avg * (total_requests - 1) + response_time) / total_requests
            )
            
            logger.debug(
                "Text generation complete",
                response_time=f"{response_time:.2f}s",
                estimated_tokens=int(estimated_tokens)
            )
            
            return result
            
        except Exception as e:
            logger.error("Text generation failed", error=str(e))
            raise
    
    def _generate_sync(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop_sequences: List[str]
    ) -> Dict[str, Any]:
        """Synchronous text generation using Ollama"""
        
        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        
        # Prepare generation options
        options = {
            "model": self.model_name,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens
            }
        }
        
        # Add stop sequences if provided
        if stop_sequences:
            options["options"]["stop"] = stop_sequences
        
        response = client.generate(**options)
        
        return {
            "text": response["response"],
            "usage": {
                "prompt_tokens": 0,  # Ollama doesn't provide this
                "completion_tokens": 0,  # Ollama doesn't provide this
                "total_tokens": 0  # Ollama doesn't provide this
            },
            "finish_reason": "stop" if response.get("done") else "length"
        }
    
    async def health_check(self) -> str:
        """Check Ollama model health status"""
        if not self.is_connected:
            return "not_connected"
        
        try:
            # Quick test generation
            test_result = await self.generate(
                "Test",
                max_tokens=1,
                temperature=0.1
            )
            return "healthy" if test_result else "unhealthy"
        except Exception:
            return "unhealthy"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model usage statistics"""
        return {
            **self.stats,
            "model_name": self.model_name,
            "is_connected": self.is_connected,
            "model_type": "ollama",
            "ollama_url": settings.OLLAMA_BASE_URL
        }
    
    async def shutdown(self):
        """Shutdown the Ollama model manager"""
        async with self.lock:
            logger.info("Shutting down Ollama model manager")
            self.is_connected = False
            # Ollama client doesn't need explicit cleanup