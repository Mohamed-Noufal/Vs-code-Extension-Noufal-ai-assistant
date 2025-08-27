# 🧪 AI Coding Assistant - Step-by-Step Test Guide

This guide will walk you through testing the AI Coding Assistant extension to ensure everything works correctly.

## 📋 Prerequisites Check

### 1. Verify VS Code Installation
```bash
# Check if VS Code is installed
code --version
```

### 2. Verify Node.js Installation
```bash
# Check Node.js version (should be 16+)
node --version
npm --version
```

### 3. Verify Extension Compilation
```bash
# In the extension directory
cd extension
npm run compile
```

## 🚀 Step-by-Step Testing

### Step 1: Open Extension in VS Code
```bash
# Navigate to extension directory
cd extension

# Open VS Code
code .
```

### Step 2: Run Extension in Development Mode
1. **Press F5** in VS Code
2. **New VS Code window** will open with extension loaded
3. **Check Output panel** → "AI Coding Assistant" for any errors

### Step 3: Test Extension Activation
1. **Open Command Palette**: `Ctrl+Shift+P`
2. **Search for "AI Assistant"**
3. **Verify commands appear**:
   - ✅ `AI Assistant: Start`
   - ✅ `AI Assistant: Configure API Keys`
   - ✅ `AI Assistant: Generate Code`
   - ✅ `AI Assistant: Explain Code`
   - ✅ `AI Assistant: Refactor Code`
   - ✅ `AI Assistant: Generate Tests`
   - ✅ `AI Assistant: Deploy Project`
   - ✅ `AI Assistant: Run Terminal Command`
   - ✅ `AI Assistant: File Operations`

### Step 4: Test API Key Configuration
1. **Run**: `AI Assistant: Configure API Keys`
2. **Choose**: "Ollama (Local)" (for testing without API keys)
3. **Select**: `mistral:7b-instruct`
4. **Verify**: Success message appears

### Step 5: Test Ollama Integration
```bash
# Start Ollama (in separate terminal)
ollama serve

# Download test model
ollama pull mistral:7b-instruct

# Test Ollama connection
curl http://localhost:11434/api/tags
```

### Step 6: Test Code Generation
1. **Create test file**: `test.js`
2. **Press**: `Ctrl+Shift+A`
3. **Enter prompt**: "Create a simple JavaScript function to add two numbers"
4. **Verify**: AI responds and generates code

### Step 7: Test File Operations
1. **Run**: `AI Assistant: File Operations`
2. **Choose**: "Create File"
3. **Enter path**: `test-component.jsx`
4. **Enter content**: "React component"
5. **Verify**: File is created

### Step 8: Test Terminal Integration
1. **Run**: `AI Assistant: Run Terminal Command`
2. **Enter**: `echo "Hello from AI Assistant"`
3. **Verify**: Command executes and shows output

## 🔧 Configuration Testing

### Test VS Code Settings
1. **Open Settings**: `Ctrl+,`
2. **Search**: "aiAssistant"
3. **Verify settings appear**:
   - `aiAssistant.openaiApiKey`
   - `aiAssistant.googleApiKey`
   - `aiAssistant.useOpenAI`
   - `aiAssistant.useGoogleAI`
   - `aiAssistant.ollamaModel`

### Test Keyboard Shortcuts
1. **Press**: `Ctrl+Shift+A`
   - Should open code generation prompt
2. **Press**: `Ctrl+Shift+E`
   - Should open code explanation prompt

## 🐛 Troubleshooting Tests

### Test Error Handling
1. **Disconnect Ollama**: Stop `ollama serve`
2. **Try code generation**: Should show error message
3. **Restart Ollama**: `ollama serve`
4. **Try again**: Should work

### Test API Key Validation
1. **Configure invalid OpenAI key**: "sk-invalid"
2. **Try OpenAI generation**: Should show error
3. **Switch to Ollama**: Should work

## 📊 Expected Results

### ✅ Success Indicators
- [ ] Extension loads without errors
- [ ] All 9 commands appear in Command Palette
- [ ] API key configuration works
- [ ] Ollama integration works
- [ ] Code generation produces results
- [ ] File operations work
- [ ] Terminal commands execute
- [ ] Keyboard shortcuts work
- [ ] Settings are accessible

### ❌ Failure Indicators
- [ ] Extension doesn't load
- [ ] Commands don't appear
- [ ] API configuration fails
- [ ] Ollama connection fails
- [ ] Code generation fails
- [ ] File operations fail
- [ ] Terminal commands fail

## 🎯 Quick Test Commands

### Test 1: Basic Functionality
```bash
# In VS Code Command Palette
AI Assistant: Start
# Expected: Welcome message
```

### Test 2: Code Generation
```bash
# Press Ctrl+Shift+A
# Enter: "Create a Python function to calculate factorial"
# Expected: Python code generated
```

### Test 3: File Creation
```bash
# Command Palette: AI Assistant: File Operations
# Choose: Create File
# Path: test.py
# Content: print("Hello World")
# Expected: File created with content
```

### Test 4: Terminal Command
```bash
# Command Palette: AI Assistant: Run Terminal Command
# Enter: dir
# Expected: Directory listing shown
```

## 🔄 Complete Test Cycle

1. **Setup**: Install dependencies, compile extension
2. **Load**: Open VS Code, press F5
3. **Configure**: Set up API keys (Ollama for testing)
4. **Test Basic**: Verify commands appear
5. **Test AI**: Generate some code
6. **Test Files**: Create/modify files
7. **Test Terminal**: Run commands
8. **Test Errors**: Verify error handling
9. **Cleanup**: Close test window

## 📝 Test Results Template

```
Test Date: _______________
Extension Version: _______________

✅ Extension Loading: [ ] Pass [ ] Fail
✅ Command Palette: [ ] Pass [ ] Fail
✅ API Configuration: [ ] Pass [ ] Fail
✅ Ollama Integration: [ ] Pass [ ] Fail
✅ Code Generation: [ ] Pass [ ] Fail
✅ File Operations: [ ] Pass [ ] Fail
✅ Terminal Commands: [ ] Pass [ ] Fail
✅ Keyboard Shortcuts: [ ] Pass [ ] Fail
✅ Error Handling: [ ] Pass [ ] Fail

Notes: ________________________________
```

## 🎉 Success Criteria

The extension is working correctly if:
- ✅ All commands appear in Command Palette
- ✅ API key configuration works
- ✅ Code generation produces meaningful results
- ✅ File operations work correctly
- ✅ Terminal commands execute properly
- ✅ Error messages are helpful
- ✅ No crashes or freezes occur

---

**Run these tests to verify your AI Coding Assistant is working perfectly!** 🚀

