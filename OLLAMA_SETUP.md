# Ollama Setup Guide for Multi-Agent Development System

This guide will help you set up Ollama to work with the Multi-Agent Development System, replacing the previous Mistral GGUF implementation.

## What is Ollama?

Ollama is a powerful, open-source tool that allows you to run large language models locally on your machine. It provides a simple API and manages model downloads, updates, and inference.

## Prerequisites

- **Operating System**: Windows 10/11, macOS, or Linux
- **RAM**: Minimum 8GB, recommended 16GB+ for optimal performance
- **Storage**: At least 5GB free space for models
- **Internet**: Required for initial model download

## Installation

### Windows

1. **Download Ollama**:
   - Visit [https://ollama.ai/download](https://ollama.ai/download)
   - Download the Windows installer (.exe file)
   - Run the installer as Administrator

2. **Verify Installation**:
   - Open Command Prompt or PowerShell
   - Run: `ollama --version`
   - You should see the version number

### macOS

1. **Using Homebrew** (recommended):
   ```bash
   brew install ollama
   ```

2. **Manual Installation**:
   - Visit [https://ollama.ai/download](https://ollama.ai/download)
   - Download the macOS installer
   - Run the installer

3. **Verify Installation**:
   ```bash
   ollama --version
   ```

### Linux

1. **Using curl** (recommended):
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Verify Installation**:
   ```bash
   ollama --version
   ```

## Starting Ollama

### Windows
- Ollama runs as a Windows service automatically
- You can also start it manually: `ollama serve`

### macOS/Linux
```bash
ollama serve
```

The service will start on `http://localhost:11434` by default.

## Downloading Mistral Model

1. **Pull the Mistral 7B Instruct model**:
   ```bash
   ollama pull mistral:7b-instruct
   ```

2. **Verify the model is available**:
   ```bash
   ollama list
   ```

You should see `mistral:7b-instruct` in the list.

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=mistral:7b-instruct

# Model Parameters
MODEL_TEMPERATURE=0.7
MODEL_TOP_P=0.9
MODEL_MAX_TOKENS=4096

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
```

### Model Parameters

You can customize the model behavior by modifying these parameters:

- **Temperature** (0.0 - 1.0): Controls randomness (lower = more deterministic)
- **Top P** (0.0 - 1.0): Controls diversity of responses
- **Max Tokens**: Maximum length of generated responses

## Testing Ollama Integration

### 1. Test Ollama Service

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test model generation
ollama run mistral:7b-instruct "Hello, how are you?"
```

### 2. Test Backend Integration

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run tests
python -m pytest tests/ -v

# Start the backend
python -m uvicorn app.main:app --reload
```

### 3. Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# System info
curl http://localhost:8000/system/info
```

## Troubleshooting

### Common Issues

1. **Ollama service not running**:
   ```bash
   # Start Ollama service
   ollama serve
   ```

2. **Model not found**:
   ```bash
   # Pull the model again
   ollama pull mistral:7b-instruct
   ```

3. **Connection refused**:
   - Check if Ollama is running on port 11434
   - Verify firewall settings
   - Check if another service is using the port

4. **Out of memory**:
   - Close other applications
   - Reduce `MODEL_MAX_TOKENS` in configuration
   - Consider using a smaller model variant

### Performance Optimization

1. **GPU Acceleration** (if available):
   ```bash
   # Check GPU support
   ollama list
   
   # Models will automatically use GPU if available
   ```

2. **Memory Management**:
   - Monitor RAM usage during model operations
   - Adjust `MODEL_MAX_TOKENS` based on available memory

3. **Model Variants**:
   ```bash
   # Smaller, faster variants
   ollama pull mistral:7b-instruct-q4_0
   ollama pull mistral:7b-instruct-q4_1
   ```

## Alternative Models

You can experiment with other models by changing the `MODEL_NAME` in your configuration:

```bash
# Other Mistral variants
ollama pull mistral:7b-instruct-v0.2
ollama pull mistral:7b-instruct-v0.3

# Llama 2 variants
ollama pull llama2:7b-chat
ollama pull llama2:13b-chat

# Code-specific models
ollama pull codellama:7b-instruct
ollama pull codellama:13b-instruct
```

## Development Workflow

### 1. Start Development Environment

```bash
# One-command setup
make dev-setup

# Start development servers
make dev
```

### 2. Monitor Logs

```bash
# Backend logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Or if running locally
tail -f backend/logs/app.log
```

### 3. Update Models

```bash
# Update existing model
ollama pull mistral:7b-instruct

# Try new model
ollama pull mistral:7b-instruct-v0.2
```

## Security Considerations

1. **Local Only**: Ollama runs locally on your machine, keeping your data private
2. **Network Access**: By default, Ollama only accepts local connections
3. **Model Sources**: Only download models from trusted sources
4. **Firewall**: Consider restricting network access if deploying in production

## Support

- **Ollama Documentation**: [https://ollama.ai/docs](https://ollama.ai/docs)
- **GitHub Issues**: [https://github.com/ollama/ollama/issues](https://github.com/ollama/ollama/issues)
- **Community**: [https://ollama.ai/community](https://ollama.ai/community)

## Next Steps

After setting up Ollama:

1. **Run the test suite** to verify integration
2. **Start the development environment** with `make dev`
3. **Test the VS Code extension** with the new Ollama backend
4. **Experiment with different models** and parameters
5. **Monitor performance** and adjust settings as needed

Happy coding with your local AI assistant! 🚀
