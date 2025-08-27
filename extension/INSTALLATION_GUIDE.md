# 🚀 AI Coding Assistant - Complete Installation & Testing Guide

## 📋 **Step-by-Step Process**

### **Step 1: Verify Your Environment**
```bash
# Check VS Code version (should be 1.60.0+)
code --version

# Check Node.js version (should be 16+)
node --version
npm --version
```

### **Step 2: Navigate to Extension Directory**
```bash
# Go to your project directory
cd "D:\prorjects\Multy agent vs code extintion\extension"

# Verify you're in the right place
dir
# Should show: package.json, src/, out/, etc.
```

### **Step 3: Install Dependencies**
```bash
# Install extension dependencies
npm install

# Install VS Code extension tools
npm install -g @vscode/vsce
```

### **Step 4: Compile the Extension**
```bash
# Compile TypeScript to JavaScript
npm run compile

# Verify compilation succeeded
dir out
# Should show: extension.js, extension.js.map
```

### **Step 5: Package the Extension**
```bash
# Create VSIX package
vsce package

# Verify package created
dir *.vsix
# Should show: ai-coding-assistant-1.0.0.vsix
```

### **Step 6: Install Extension in VS Code**

#### **Option A: Development Mode (Recommended for Testing)**
```bash
# Open extension in VS Code
code .

# Press F5 to run in development mode
# New VS Code window will open with extension loaded
```

#### **Option B: Install VSIX Package**
```bash
# Install the VSIX package
code --install-extension ai-coding-assistant-1.0.0.vsix

# Restart VS Code
code .
```

## 🧪 **Testing the Extension**

### **Test 1: Verify Extension Loaded**
1. **Open Command Palette**: `Ctrl+Shift+P`
2. **Search**: "AI Assistant"
3. **Verify these commands appear**:
   - ✅ `AI Assistant: Start`
   - ✅ `AI Assistant: Configure API Keys`
   - ✅ `AI Assistant: Generate Code`
   - ✅ `AI Assistant: Explain Code`
   - ✅ `AI Assistant: Refactor Code`
   - ✅ `AI Assistant: Generate Tests`
   - ✅ `AI Assistant: Deploy Project`
   - ✅ `AI Assistant: Run Terminal Command`
   - ✅ `AI Assistant: File Operations`

### **Test 2: Configure API Keys**
1. **Run**: `AI Assistant: Configure API Keys`
2. **Choose**: "Ollama (Local)" (for testing)
3. **Select**: `mistral:7b-instruct`
4. **Verify**: Success message appears

### **Test 3: Setup Ollama (for Local AI)**
```bash
# Start Ollama (in separate terminal)
ollama serve

# Download test model
ollama pull mistral:7b-instruct

# Test connection
curl http://localhost:11434/api/tags
```

### **Test 4: Test Code Generation**
1. **Create test file**: `test.js`
2. **Press**: `Ctrl+Shift+A`
3. **Enter**: "Create a JavaScript function to add two numbers"
4. **Verify**: AI generates code

### **Test 5: Test File Operations**
1. **Run**: `AI Assistant: File Operations`
2. **Choose**: "Create File"
3. **Path**: `test-component.jsx`
4. **Content**: "React component"
5. **Verify**: File is created

### **Test 6: Test Terminal Commands**
1. **Run**: `AI Assistant: Run Terminal Command`
2. **Enter**: `echo "Hello from AI Assistant"`
3. **Verify**: Command executes

## 🔧 **Configuration Options**

### **VS Code Settings**
1. **Open Settings**: `Ctrl+,`
2. **Search**: "aiAssistant"
3. **Configure**:
   ```json
   {
     "aiAssistant.openaiApiKey": "sk-your-key",
     "aiAssistant.googleApiKey": "your-google-key",
     "aiAssistant.useOpenAI": false,
     "aiAssistant.useGoogleAI": false,
     "aiAssistant.ollamaModel": "mistral:7b-instruct",
     "aiAssistant.autoSave": true,
     "aiAssistant.showExplanations": true
   }
   ```

### **Keyboard Shortcuts**
- **`Ctrl+Shift+A`**: Generate Code
- **`Ctrl+Shift+E`**: Explain Code

## 🎯 **Quick Test Commands**

### **Test Basic Functionality**
```bash
# Command Palette: AI Assistant: Start
# Expected: Welcome message
```

### **Test Code Generation**
```bash
# Press Ctrl+Shift+A
# Enter: "Create a Python function to calculate factorial"
# Expected: Python code generated
```

### **Test File Creation**
```bash
# Command Palette: AI Assistant: File Operations
# Choose: Create File
# Path: test.py
# Content: print("Hello World")
# Expected: File created with content
```

### **Test Terminal Command**
```bash
# Command Palette: AI Assistant: Run Terminal Command
# Enter: dir
# Expected: Directory listing shown
```

## 🐛 **Troubleshooting**

### **Extension Not Loading**
1. **Check Output panel**: View → Output → "AI Coding Assistant"
2. **Reload window**: `Ctrl+Shift+P` → "Developer: Reload Window"
3. **Check compilation**: Run `npm run compile`

### **Commands Not Appearing**
1. **Verify activation events** in package.json
2. **Check extension is enabled** in Extensions panel
3. **Restart VS Code**

### **Ollama Connection Issues**
1. **Check Ollama is running**: `ollama serve`
2. **Test connection**: `curl http://localhost:11434/api/tags`
3. **Check model is downloaded**: `ollama list`

### **API Key Issues**
1. **Verify key format**: OpenAI keys start with "sk-"
2. **Check key validity**: Test in OpenAI/Google AI console
3. **Switch to Ollama**: Use local models for testing

## 📊 **Expected Results**

### **✅ Success Indicators**
- [ ] Extension loads without errors
- [ ] All 9 commands appear in Command Palette
- [ ] API key configuration works
- [ ] Ollama integration works
- [ ] Code generation produces results
- [ ] File operations work
- [ ] Terminal commands execute
- [ ] Keyboard shortcuts work
- [ ] Settings are accessible

### **❌ Failure Indicators**
- [ ] Extension doesn't load
- [ ] Commands don't appear
- [ ] API configuration fails
- [ ] Ollama connection fails
- [ ] Code generation fails
- [ ] File operations fail
- [ ] Terminal commands fail

## 🎉 **What You Can Do Now**

Once the extension is working, you can:

### **Generate Code**
- **React components**: "Create a React login form"
- **Python APIs**: "Build a Flask REST API"
- **Mobile apps**: "Create a React Native app"
- **Full-stack**: "Build a complete todo app"

### **Explain Code**
- **Select code** and press `Ctrl+Shift+E`
- **Get detailed explanations** of complex functions
- **Understand** unfamiliar codebases

### **Refactor Code**
- **Improve performance** of existing code
- **Fix bugs** and issues
- **Apply best practices**

### **Generate Tests**
- **Unit tests** for functions
- **Integration tests** for APIs
- **E2E tests** for applications

### **Deploy Projects**
- **Docker containers**
- **Cloud platforms** (AWS, Azure, GCP)
- **CI/CD pipelines**

## 🔄 **Complete Workflow Example**

1. **Start new project**:
   ```
   AI Assistant: Generate Code
   "Create a React todo app with Node.js backend"
   ```

2. **Explain generated code**:
   ```
   Select code → Ctrl+Shift+E
   "Explain this React component"
   ```

3. **Add features**:
   ```
   AI Assistant: Generate Code
   "Add user authentication to the todo app"
   ```

4. **Generate tests**:
   ```
   AI Assistant: Generate Tests
   "Create tests for the todo app"
   ```

5. **Deploy**:
   ```
   AI Assistant: Deploy Project
   "Deploy this todo app to Heroku"
   ```

## 🏆 **Success!**

Your AI Coding Assistant is now ready to help you build amazing software! 

**Next Steps**:
1. ✅ **Test all features** using the guide above
2. ✅ **Configure your preferred AI model** (OpenAI, Google AI, or Ollama)
3. ✅ **Start building** your next project with AI assistance
4. ✅ **Share feedback** and report any issues

**Happy coding with AI!** 🚀💻✨
