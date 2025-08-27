# 🔧 Ollama Setup for AI Coding Assistant

Quick setup guide for using local AI models with the AI Coding Assistant extension.

## 🚀 Quick Start

### 1. Install Ollama
```bash
# Windows
# Download from https://ollama.ai/download

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Start Ollama
```bash
ollama serve
```

### 3. Download Models
```bash
# Mistral 7B (Recommended for coding)
ollama pull mistral:7b-instruct

# DeepSeek Coder V2 (Specialized for coding)
ollama pull deepseek-coder:6.7b

# CodeLlama 7B (Another coding specialist)
ollama pull codellama:7b
```

### 4. Configure Extension
1. Open VS Code Command Palette (`Ctrl+Shift+P`)
2. Run `AI Assistant: Configure API Keys`
3. Select "Ollama (Local)"
4. Choose your preferred model

## 🎯 Model Comparison

| Model | Size | Speed | Coding Quality | Best For |
|-------|------|-------|----------------|----------|
| `mistral:7b-instruct` | 7B | Fast | Good | General coding |
| `deepseek-coder:6.7b` | 6.7B | Fast | Excellent | Code generation |
| `codellama:7b` | 7B | Fast | Very Good | Code completion |

## 🔧 Configuration

### VS Code Settings
```json
{
  "aiAssistant.useOpenAI": false,
  "aiAssistant.useGoogleAI": false,
  "aiAssistant.ollamaModel": "mistral:7b-instruct"
}
```

### Environment Variables (Optional)
```bash
# Set Ollama URL if different
export OLLAMA_HOST=http://localhost:11434
```

## 🧪 Testing

### Check Ollama Status
```bash
# List available models
ollama list

# Test model
ollama run mistral:7b-instruct "Write a Python function to calculate fibonacci"
```

### Test Extension
1. Open VS Code
2. Press `Ctrl+Shift+A`
3. Enter: "Create a simple React component"
4. Check if AI responds

## 🐛 Troubleshooting

### Ollama Not Starting?
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### Model Not Found?
```bash
# List models
ollama list

# Pull missing model
ollama pull model-name
```

### Extension Not Working?
1. Check VS Code Output panel → "AI Coding Assistant"
2. Verify Ollama is running on port 11434
3. Ensure model is downloaded

## 🚀 Performance Tips

### For Better Speed
- Use smaller models (7B vs 13B)
- Close other applications
- Ensure sufficient RAM (8GB+)

### For Better Quality
- Use specialized coding models (DeepSeek, CodeLlama)
- Provide clear, specific prompts
- Include context from your codebase

## 📝 Example Usage

### Generate React Component
```
Prompt: "Create a React component for a user profile card with avatar, name, and bio"
Model: deepseek-coder:6.7b
```

### Explain Code
```
Prompt: "Explain this JavaScript function"
Model: mistral:7b-instruct
```

### Refactor Code
```
Prompt: "Refactor this Python code to be more efficient"
Model: codellama:7b
```

## 🎉 Benefits of Local Models

- ✅ **Privacy**: No data sent to external servers
- ✅ **Speed**: No network latency
- ✅ **Cost**: No API charges
- ✅ **Offline**: Works without internet
- ✅ **Customization**: Can fine-tune models

## 🔄 Switching Models

You can easily switch between models:

1. **Via Command Palette**:
   - `AI Assistant: Configure API Keys`
   - Select "Ollama (Local)"
   - Choose different model

2. **Via Settings**:
   - Open VS Code settings
   - Search "aiAssistant.ollamaModel"
   - Change to desired model

## 📚 Advanced Usage

### Custom Prompts
The AI understands context from your workspace, so you can ask:
- "Create a test file for this component"
- "Add error handling to this function"
- "Optimize this database query"

### File Operations
The AI can:
- Create new files with proper structure
- Modify existing files
- Generate test files
- Create documentation

### Terminal Commands
The AI can suggest and execute:
- `npm install` for dependencies
- `git` commands for version control
- Build and deployment commands

---

**Happy coding with local AI! 🚀💻**
