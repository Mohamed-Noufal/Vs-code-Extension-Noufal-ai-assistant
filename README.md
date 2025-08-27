# 🚀 Multi-Agent Development System

A powerful AI-powered development environment with multiple intelligent agents working together to help you build software faster and more efficiently.

## 🎯 **What This System Does**

This system uses **three specialized AI agents** that collaborate to:
- 🧠 **Understand** your requirements in natural language
- 📋 **Plan** detailed development projects  
- 💻 **Generate** production-ready code
- 🔄 **Iterate** and improve solutions
- 🚀 **Accelerate** your development workflow

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   VS Code       │    │   Backend API    │    │   Ollama        │
│   Extension     │◄──►│   (FastAPI)      │◄──►│   + Mistral     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  AI Agents       │
                       │  • Q&A Intake    │
                       │  • Manager       │
                       │  • Code          │
                       └──────────────────┘
```

## ✨ **Key Features**

- 🤖 **Multi-Agent Collaboration**: Three AI agents working together
- 🧠 **Local AI Models**: Powered by Ollama + Mistral (7B parameters)
- 🔌 **VS Code Integration**: Seamless extension with interactive commands
- 🚀 **FastAPI Backend**: Modern, async Python backend
- 📊 **Real-time Monitoring**: Health checks and system status
- 🧪 **Complete Test Suite**: 35+ tests ensuring reliability
- 🎮 **Interactive Demos**: See the system in action

## 🚀 **Quick Start (5 minutes)**

### 1. **Start the Backend Server**
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

**Wait for initialization** - you'll see:
- ✅ Ollama service accessible
- ✅ Mistral model downloaded  
- ✅ Workflow manager initialized
- ✅ System startup complete

### 2. **Test the System**
Open your browser and visit:
- **Main API**: http://127.0.0.1:8001
- **Health Check**: http://127.0.0.1:8001/health
- **Interactive Docs**: http://127.0.0.1:8001/docs

### 3. **Use the VS Code Extension (v3.0.0)**
1. **Open Command Palette**: `Ctrl+Shift+P`
2. **Search for "Noufal AI"**
3. **Available Commands**:
   - `Noufal AI: Start Assistant`
   - `Noufal AI: Open Chat`
   - `Noufal AI: Configure API Keys`
   - `Noufal AI: File Operations`
   - `Noufal AI: Plan Task (Planner→Coder)`
   - `Noufal AI: Check Backend Health`
   - `Noufal AI: Start Backend Workflow`

Shortcuts:
- Open Chat: `Ctrl+Alt+C`
- Generate Code: `Ctrl+Alt+A`
- Explain Code: `Ctrl+Alt+E`

## 🎮 **Try the Demo**

### **Simple Demo**
```bash
cd backend
python demo_workflow.py
# Choose option 1
```

### **Interactive Demo**
```bash
cd backend
python demo_workflow.py
# Choose option 2
# Enter your own requests like:
# "Create a React todo app"
# "Build a Python web scraper"
# "Make a JavaScript game"
```

## 🤖 **How the Agents Work**

### 1. **Q&A Intake Agent** 🤔
- **Purpose**: Understands your requirements
- **Input**: Natural language description
- **Output**: Clarified specifications
- **Example**: "Build a login system" → "User authentication with email/password, session management, security features"

### 2. **Manager/Planner Agent** 📋
- **Purpose**: Creates development plans
- **Input**: Clarified requirements
- **Output**: Detailed project plan
- **Example**: Breaks down into: database design, API endpoints, frontend components, testing strategy

### 3. **Code Agent** 💻
- **Purpose**: Generates production code
- **Input**: Project plan + requirements
- **Output**: Working code with best practices
- **Example**: Generates React components, Python classes, database schemas

## 📱 **Example Workflows**

### **Web Application**
1. **Request**: "Create a React dashboard with charts"
2. **Q&A Agent**: Clarifies requirements (user management, chart types, data sources)
3. **Manager Agent**: Plans component structure, suggests libraries (Chart.js, Material-UI)
4. **Code Agent**: Generates React components, styling, and data integration

### **API Development**
1. **Request**: "Build a Node.js REST API for user management"
2. **Q&A Agent**: Defines user fields, authentication needs, API scope
3. **Manager Agent**: Plans endpoints, database schema, middleware
4. **Code Agent**: Generates Express routes, MongoDB models, JWT auth

### **Data Science**
1. **Request**: "Create a Python script for data analysis and visualization"
2. **Q&A Agent**: Clarifies data format, analysis goals, visualization preferences
3. **Manager Agent**: Plans data pipeline, suggests libraries (pandas, matplotlib)
4. **Code Agent**: Generates data processing code, charts, and insights

## 🛠️ **Installation & Setup**

### **Prerequisites**
- Python 3.8+
- Node.js 16+
- VS Code 1.74+
- Ollama (for local AI models)

### **Backend Setup**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### **VS Code Extension Setup (build VSIX)**
```bash
cd extension
npm install
npm run compile
 npx @vscode/vsce package --no-dependencies
 code --install-extension ./noufal-ai-assistant-3.0.0.vsix --force
```

### **Ollama Setup**
```bash
# Install Ollama (see OLLAMA_SETUP.md for details)
ollama serve
ollama pull mistral:7b-instruct
```

## 🔧 **Configuration**

### **Backend Settings**
Create `.env` file in `backend/` directory:
```env
MODEL_NAME=mistral:7b-instruct
OLLAMA_BASE_URL=http://localhost:11434
LOG_LEVEL=INFO
```

### **VS Code Extension Settings**
Open VS Code settings and search for "Noufal AI Assistant":
```json
{
  "aiAssistant.backendUrl": "http://127.0.0.1:8001",
  "aiAssistant.useOpenAI": false,
  "aiAssistant.useGoogleAI": false,
  "aiAssistant.ollamaModel": "Mistral",
  "aiAssistant.memory.enabled": true
}
```
Tip: In the chat UI you can switch provider (Ollama/OpenAI/Google) and set the model field directly.

## 🧪 **Testing**

### **Run All Tests**
```bash
cd backend
python -m pytest tests/ -v
```

### **Run with Coverage**
```bash
cd backend
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### **Run Specific Tests**
```bash
# Test model manager
python -m pytest tests/test_model_manager.py -v

# Test API endpoints
python -m pytest tests/test_api_endpoints.py -v

# Test prompt templates
python -m pytest tests/test_mistral_prompts.py -v
```

## 📚 **API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System information and status |
| `/health` | GET | Health check for all components |
| `/system/info` | GET | Detailed system and agent information |
| `/docs` | GET | Interactive API documentation |
| `/api/v1/workflows/start` | POST | Start new development workflow |

## 🔍 **Troubleshooting**

### **Backend Won't Start?**
1. **Check Ollama**: Ensure Ollama is running (`ollama serve`)
2. **Check Port**: Port 8001 might be in use
3. **Check Dependencies**: Run `pip install -r requirements.txt`

### **Extension Not Working?**
1. **Check Backend**: Ensure server is running on port 8001
2. **Check Commands**: Use Command Palette → "Multi-Agent"
3. **Check Logs**: View → Output → "Multi-Agent Development System"

### **Model Issues?**
1. **Check Ollama**: `ollama list` to see available models
2. **Download Model**: `ollama pull mistral:7b-instruct`
3. **Check Connection**: `curl http://localhost:11434/api/tags`

## 🚀 **Next Steps**

### 1. **Customize Agents**
- Modify prompts in `app/models/mistral.py`
- Add new agent types in `app/agents/`
- Extend workflow logic in `app/orchestrator/`

### 2. **Add New Features**
- Database integration
- File system operations
- Git integration
- Deployment automation

### 3. **Scale Up**
- Multiple model support
- Agent collaboration
- Workflow persistence
- Performance monitoring

## 📁 **Project Structure**

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # AI agent implementations
│   │   ├── api/            # API routes and WebSocket
│   │   ├── core/           # Configuration and logging
│   │   ├── models/         # AI model management
│   │   └── orchestrator/   # Workflow orchestration
│   ├── tests/              # Complete test suite
│   └── requirements.txt    # Python dependencies
├── extension/              # VS Code extension
│   ├── src/               # TypeScript source
│   ├── package.json       # Extension configuration
│   └── README.md          # Extension documentation
├── scripts/                # Setup and utility scripts
├── OLLAMA_SETUP.md        # Ollama installation guide
├── SETUP_GUIDE.md         # Complete setup guide
└── README.md              # This file
```

## 🤝 **Contributing**

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

## 📄 **License**

This project is licensed under the MIT License.

## 🆘 **Support**

If you encounter issues:
- **Check logs** in VS Code Output panel
- **Verify backend** health at http://127.0.0.1:8001/health
- **Test endpoints** using the interactive docs
- **Run demos** to see the system in action

## 🎉 **You're Ready!**

Your **Multi-Agent Development System** is now a powerful tool that can:

- 🧠 **Understand** complex requirements
- 📋 **Plan** development projects
- 💻 **Generate** production-ready code
- 🔄 **Iterate** and improve solutions
- 🚀 **Accelerate** your development workflow

**Start building amazing software with AI agents!** 🎯🤖✨

---

## 📞 **Quick Status Check**

**✅ System Status**: Fully Operational
**✅ Backend**: Running on port 8001
**✅ AI Model**: Mistral 7B ready
**✅ VS Code Extension**: Compiled and ready
**✅ Test Suite**: 35+ tests passing
**✅ Demo System**: Interactive workflows working

**Your Multi-Agent Development System is ready for production use!** 🚀