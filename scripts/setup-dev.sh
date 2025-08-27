#!/bin/bash

# Multi-Agent Development System - Development Setup Script

set -e  # Exit on any error

echo "🚀 Setting up Multi-Agent Development System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "Makefile" ] || [ ! -f "package.json" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_step "Checking system dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi
print_success "Python 3 found"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed"
    exit 1
fi
print_success "Node.js found"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is required but not installed"
    exit 1
fi
print_success "Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is required but not installed"
    exit 1
fi
print_success "Docker Compose found"

print_step "Setting up Python backend environment..."

# Navigate to backend directory
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_step "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_step "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Navigate back to root
cd ..

print_step "Setting up extension environment..."

# Create extension directory and basic structure
mkdir -p extension/src
mkdir -p extension/src/components
mkdir -p extension/src/utils

# Create basic package.json for extension
if [ ! -f "extension/package.json" ]; then
    cat > extension/package.json << 'EOL'
{
  "name": "multi-agent-dev-extension",
  "version": "1.0.0",
  "description": "VS Code extension for Multi-Agent Development System",
  "main": "out/extension.js",
  "scripts": {
    "vscode:prepublish": "npm run compile",
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./",
    "dev": "tsc -watch -p ./",
    "test": "echo \"Tests not configured yet\" && exit 0"
  },
  "engines": {
    "vscode": "^1.74.0"
  },
  "categories": [
    "Other"
  ],
  "activationEvents": [
    "onCommand:multiAgent.start"
  ],
  "contributes": {
    "commands": [
      {
        "command": "multiAgent.start",
        "title": "Start Multi-Agent Assistant"
      }
    ]
  },
  "devDependencies": {
    "@types/node": "^18.0.0",
    "@types/vscode": "^1.74.0",
    "typescript": "^4.9.0"
  },
  "dependencies": {
    "ws": "^8.14.0"
  }
}
EOL
    print_success "Extension package.json created"
fi

# Navigate to extension directory and install dependencies
cd extension
if [ ! -d "node_modules" ]; then
    print_step "Installing extension dependencies..."
    npm install
    print_success "Extension dependencies installed"
else
    print_success "Extension dependencies already installed"
fi

# Navigate back to root
cd ..

print_step "Setting up Docker environment..."

# Build Docker images
print_step "Building Docker images..."
docker-compose -f docker-compose.dev.yml build
print_success "Docker images built"

print_step "Creating necessary directories..."

# Create required directories
mkdir -p models
mkdir -p logs
mkdir -p workspace
mkdir -p backend/.cache

print_success "Directories created"

print_step "Setting up environment files..."

# Create .env file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    cat > backend/.env << EOL
# Multi-Agent Development System Environment

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Model Configuration
MODEL_PATH=models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
MODEL_TYPE=mistral
MODEL_MAX_TOKENS=4096
MODEL_TEMPERATURE=0.7

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=dev-secret-key-change-in-production

# Agent Configuration
MAX_ITERATIONS=10
TIMEOUT_SECONDS=300
MAX_CONCURRENT_WORKFLOWS=5

# File System
WORKSPACE_DIR=workspace
MAX_FILE_SIZE=10485760
EOL
    print_success "Environment file created"
else
    print_success "Environment file already exists"
fi

print_step "Creating model download script..."

# Create model download script
cat > scripts/download-model.sh << 'EOL'
#!/bin/bash

# Download Mistral 7B model
MODEL_URL="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
MODEL_FILE="models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

echo "📥 Downloading Mistral 7B model..."
echo "This may take a while (model is ~4GB)..."

if [ ! -f "$MODEL_FILE" ]; then
    mkdir -p models
    
    # Try to download with curl first, then wget
    if command -v curl &> /dev/null; then
        curl -L -o "$MODEL_FILE" "$MODEL_URL"
    elif command -v wget &> /dev/null; then
        wget -O "$MODEL_FILE" "$MODEL_URL"
    else
        echo "❌ Neither curl nor wget found. Please download the model manually:"
        echo "URL: $MODEL_URL"
        echo "Save to: $MODEL_FILE"
        exit 1
    fi
    
    echo "✅ Model downloaded successfully"
else
    echo "✅ Model already exists"
fi
EOL

chmod +x scripts/download-model.sh

print_warning "Note: The AI model (Mistral 7B) is not downloaded automatically due to its size (~4GB)"
print_step "To download the model, run: make download-model"

print_step "Testing setup..."

# Test Python environment
print_step "Testing Python environment..."
cd backend
source venv/bin/activate
python -c "import fastapi, uvicorn; print('Python environment OK')" 2>/dev/null || print_warning "Some Python packages may need manual installation"
cd ..
print_success "Python environment test completed"

print_success "🎉 Development environment setup complete!"

echo ""
echo "📋 Next steps:"
echo "1. Download the AI model: make download-model"
echo "2. Start the development environment: make dev"
echo "3. Open VS Code and load the extension for development"
echo ""
echo "📚 Useful commands:"
echo "  make dev          - Start full development environment"
echo "  make dev-backend  - Start backend only"
echo "  make test         - Run tests"
echo "  make lint         - Lint and format code"
echo "  make clean        - Clean up generated files"
echo ""
echo "🌐 Once running, access:"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  WebSocket: ws://localhost:8000/ws/{connection_id}"