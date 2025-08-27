# Multi-Agent Development System - Makefile

.PHONY: dev-setup dev build test clean docker-build docker-up docker-down ollama-setup

# Variables
PYTHON_VERSION := 3.11
NODE_VERSION := 18
BACKEND_DIR := backend
EXTENSION_DIR := extension
DOCKER_DIR := docker

# Development setup - one command to rule them all
dev-setup: check-dependencies setup-python setup-node setup-docker ollama-setup
	@echo "🚀 Development environment setup complete!"
	@echo "Run 'make dev' to start the development servers"

# Check system dependencies
check-dependencies:
	@echo "🔍 Checking system dependencies..."
	@command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required"; exit 1; }
	@command -v ollama >/dev/null 2>&1 || { echo "❌ Ollama is required - see OLLAMA_SETUP.md"; exit 1; }
	@echo "✅ All system dependencies found"

# Python environment setup
setup-python:
	@echo "🐍 Setting up Python environment..."
	cd $(BACKEND_DIR) && python3 -m venv venv
	cd $(BACKEND_DIR) && . venv/bin/activate && pip install --upgrade pip
	cd $(BACKEND_DIR) && . venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Python environment ready"

# Node.js environment setup  
setup-node:
	@echo "📦 Setting up Node.js environment..."
	cd $(EXTENSION_DIR) && npm install
	@echo "✅ Node.js environment ready"

# Docker environment setup
setup-docker:
	@echo "🐳 Setting up Docker environment..."
	docker-compose -f docker-compose.dev.yml build
	@echo "✅ Docker environment ready"

# Ollama setup
ollama-setup:
	@echo "🤖 Setting up Ollama and Mistral model..."
	@echo "Checking if Ollama is running..."
	@ollama list >/dev/null 2>&1 || { echo "Starting Ollama service..."; ollama serve & sleep 5; }
	@echo "Pulling Mistral 7B Instruct model..."
	@ollama pull mistral:7b-instruct || { echo "❌ Failed to pull model. Check OLLAMA_SETUP.md"; exit 1; }
	@echo "✅ Ollama setup complete"

# Start development servers
dev:
	@echo "🚀 Starting development environment..."
	docker-compose -f docker-compose.dev.yml up --build

# Start backend only
dev-backend:
	@echo "🔧 Starting backend development server..."
	cd $(BACKEND_DIR) && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start extension development
dev-extension:
	@echo "🎨 Starting extension development..."
	cd $(EXTENSION_DIR) && npm run dev

# Build everything
build: build-backend build-extension
	@echo "✅ Build complete"

# Build backend
build-backend:
	@echo "🏗️ Building backend..."
	cd $(BACKEND_DIR) && . venv/bin/activate && python -m pytest tests/ -v

# Build extension
build-extension:
	@echo "📦 Building extension..."
	cd $(EXTENSION_DIR) && npm run build

# Run tests
test: test-backend test-extension
	@echo "✅ All tests passed"

# Test backend
test-backend:
	@echo "🧪 Testing backend..."
	cd $(BACKEND_DIR) && . venv/bin/activate && python -m pytest tests/ -v --cov=app

# Test extension
test-extension:
	@echo "🧪 Testing extension..."
	cd $(EXTENSION_DIR) && npm test

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	cd $(BACKEND_DIR) && rm -rf venv __pycache__ .pytest_cache .coverage
	cd $(EXTENSION_DIR) && rm -rf node_modules dist out
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f

# Docker commands
docker-build:
	docker-compose -f docker-compose.dev.yml build

docker-up:
	docker-compose -f docker-compose.dev.yml up -d

docker-down:
	docker-compose -f docker-compose.dev.yml down

# Ollama commands
ollama-status:
	@echo "🤖 Checking Ollama status..."
	@ollama list

ollama-pull-mistral:
	@echo "📥 Pulling Mistral 7B Instruct model..."
	@ollama pull mistral:7b-instruct

ollama-serve:
	@echo "🚀 Starting Ollama service..."
	@ollama serve

# Lint and format
lint:
	@echo "🔍 Linting code..."
	cd $(BACKEND_DIR) && . venv/bin/activate && black app/ && isort app/ && flake8 app/
	cd $(EXTENSION_DIR) && npm run lint

# Format code
format:
	@echo "✨ Formatting code..."
	cd $(BACKEND_DIR) && . venv/bin/activate && black app/ && isort app/
	cd $(EXTENSION_DIR) && npm run format

# Help
help:
	@echo "Multi-Agent Development System - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  dev-setup          - One-command development environment setup"
	@echo "  ollama-setup       - Setup Ollama and download Mistral model"
	@echo "  ollama-status      - Check Ollama models and status"
	@echo "  ollama-pull-mistral - Download/update Mistral model"
	@echo ""
	@echo "Development:"
	@echo "  dev               - Start full development environment"
	@echo "  dev-backend       - Start backend only"
	@echo "  dev-extension     - Start extension development"
	@echo ""
	@echo "Build & Test:"
	@echo "  build             - Build everything"
	@echo "  test              - Run all tests"
	@echo "  lint              - Lint and format code"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build      - Build Docker images"
	@echo "  docker-up         - Start Docker services"
	@echo "  docker-down       - Stop Docker services"
	@echo ""
	@echo "Ollama:"
	@echo "  ollama-serve      - Start Ollama service"
	@echo "  ollama-status     - List available models"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean             - Clean up all generated files"