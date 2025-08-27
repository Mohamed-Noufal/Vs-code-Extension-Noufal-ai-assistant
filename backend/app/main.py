"""
Multi-Agent Development System - Main FastAPI Application
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import structlog

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import api_router
from app.api.websocket import websocket_router
from app.models.manager import ModelManager
from app.orchestrator.workflow import WorkflowManager

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Global instances
model_manager: ModelManager = None
workflow_manager: WorkflowManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    global model_manager, workflow_manager
    
    logger.info("Starting Multi-Agent Development System")
    
    try:
        # Initialize model manager
        logger.info("Initializing AI model manager")
        model_manager = ModelManager()
        await model_manager.initialize()
        
        # Initialize workflow manager
        logger.info("Initializing workflow manager")
        workflow_manager = WorkflowManager(model_manager)
        await workflow_manager.initialize()
        
        # Store in app state
        app.state.model_manager = model_manager
        app.state.workflow_manager = workflow_manager
        
        logger.info("System initialization complete")
        yield
        
    except Exception as e:
        logger.error("Failed to initialize system", error=str(e))
        raise
    finally:
        # Cleanup
        logger.info("Shutting down system")
        if workflow_manager:
            await workflow_manager.shutdown()
        if model_manager:
            await model_manager.shutdown()


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-Agent Development System with Local AI Models",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router)

# Serve static files
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Multi-Agent Development System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "api": f"{settings.API_V1_STR}",
            "docs": "/docs",
            "websocket": "/ws"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check model manager
        model_status = "unknown"
        if hasattr(app.state, 'model_manager') and app.state.model_manager:
            model_status = await app.state.model_manager.health_check()
        
        # Check workflow manager
        workflow_status = "unknown"
        if hasattr(app.state, 'workflow_manager') and app.state.workflow_manager:
            workflow_status = app.state.workflow_manager.health_check()
        
        return {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {
                "model_manager": model_status,
                "workflow_manager": workflow_status
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/system/info")
async def system_info():
    """System information endpoint"""
    try:
        info = {
            "system": "Multi-Agent Development System",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "agents": []
        }
        
        if hasattr(app.state, 'workflow_manager') and app.state.workflow_manager:
            info["agents"] = app.state.workflow_manager.get_agent_info()
        
        return info
    except Exception as e:
        logger.error("Failed to get system info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system info")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )