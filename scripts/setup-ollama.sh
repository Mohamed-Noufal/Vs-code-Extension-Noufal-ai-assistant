#!/bin/bash
# Ollama Setup Script for Multi-Agent Development System
# This script helps set up Ollama on different operating systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Ollama on Linux
install_ollama_linux() {
    print_status "Installing Ollama on Linux..."
    
    if command_exists curl; then
        print_status "Using curl to install Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        print_error "curl is not installed. Please install curl first:"
        print_error "  Ubuntu/Debian: sudo apt-get install curl"
        print_error "  CentOS/RHEL: sudo yum install curl"
        exit 1
    fi
}

# Function to install Ollama on macOS
install_ollama_macos() {
    print_status "Installing Ollama on macOS..."
    
    if command_exists brew; then
        print_status "Using Homebrew to install Ollama..."
        brew install ollama
    else
        print_warning "Homebrew not found. Please install Homebrew first:"
        print_warning "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        print_warning "Then run: brew install ollama"
        exit 1
    fi
}

# Function to install Ollama on Windows
install_ollama_windows() {
    print_status "Installing Ollama on Windows..."
    print_warning "Please download and install Ollama manually from:"
    print_warning "  https://ollama.ai/download"
    print_warning "Run the installer as Administrator"
    print_warning "After installation, restart your terminal and run this script again"
    exit 1
}

# Function to start Ollama service
start_ollama() {
    print_status "Starting Ollama service..."
    
    if ! command_exists ollama; then
        print_error "Ollama is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Ollama is already running
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama is already running"
        return 0
    fi
    
    # Start Ollama in background
    print_status "Starting Ollama service in background..."
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for service to start
    print_status "Waiting for Ollama service to start..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_success "Ollama service started successfully"
            return 0
        fi
        sleep 1
    done
    
    print_error "Failed to start Ollama service"
    kill $OLLAMA_PID 2>/dev/null || true
    exit 1
}

# Function to download Mistral model
download_mistral() {
    print_status "Downloading Mistral 7B Instruct model..."
    
    if ! command_exists ollama; then
        print_error "Ollama is not installed"
        exit 1
    fi
    
    # Check if model is already downloaded
    if ollama list | grep -q "mistral:7b-instruct"; then
        print_success "Mistral model is already downloaded"
        return 0
    fi
    
    # Download the model
    print_status "Pulling Mistral 7B Instruct model (this may take a while)..."
    if ollama pull mistral:7b-instruct; then
        print_success "Mistral model downloaded successfully"
    else
        print_error "Failed to download Mistral model"
        exit 1
    fi
}

# Function to verify installation
verify_installation() {
    print_status "Verifying Ollama installation..."
    
    # Check Ollama version
    if command_exists ollama; then
        VERSION=$(ollama --version)
        print_success "Ollama version: $VERSION"
    else
        print_error "Ollama is not installed or not in PATH"
        exit 1
    fi
    
    # Check if service is running
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama service is running"
    else
        print_error "Ollama service is not running"
        exit 1
    fi
    
    # Check if model is available
    if ollama list | grep -q "mistral:7b-instruct"; then
        print_success "Mistral model is available"
    else
        print_error "Mistral model is not available"
        exit 1
    fi
    
    print_success "Ollama installation verified successfully!"
}

# Main function
main() {
    echo "🚀 Ollama Setup Script for Multi-Agent Development System"
    echo "========================================================"
    
    OS=$(detect_os)
    print_status "Detected operating system: $OS"
    
    # Install Ollama if not already installed
    if ! command_exists ollama; then
        print_status "Ollama not found. Installing..."
        case $OS in
            "linux")
                install_ollama_linux
                ;;
            "macos")
                install_ollama_macos
                ;;
            "windows")
                install_ollama_windows
                ;;
            *)
                print_error "Unsupported operating system: $OS"
                exit 1
                ;;
        esac
    else
        print_success "Ollama is already installed"
    fi
    
    # Start Ollama service
    start_ollama
    
    # Download Mistral model
    download_mistral
    
    # Verify installation
    verify_installation
    
    echo ""
    print_success "🎉 Ollama setup completed successfully!"
    echo ""
    print_status "Next steps:"
    print_status "1. Run 'make dev-setup' to set up the development environment"
    print_status "2. Run 'make dev' to start the development servers"
    print_status "3. Check OLLAMA_SETUP.md for more detailed information"
    echo ""
}

# Run main function
main "$@"
