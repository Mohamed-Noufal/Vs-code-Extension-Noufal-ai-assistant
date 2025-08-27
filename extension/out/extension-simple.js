"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
/**
 * Noufal AI Assistant - VS Code Extension
 * Enhanced with Interactive Chat GUI
 */
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
const https = require("https");
const http = require("http");
const child_process_1 = require("child_process");
const util_1 = require("util");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
class AICodingAssistant {
    constructor() {
        this.config = vscode.workspace.getConfiguration('aiAssistant');
        this.outputChannel = vscode.window.createOutputChannel('Noufal AI Assistant');
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.text = '$(robot) Noufal AI';
        this.statusBarItem.tooltip = 'Noufal AI Assistant Ready - Click to open chat';
        this.statusBarItem.command = 'aiAssistant.chat';
        this.statusBarItem.show();
    }
    // Main AI interaction method
    interactWithAI(prompt, context) {
        return __awaiter(this, void 0, void 0, function* () {
            const useOpenAI = this.config.get('useOpenAI') || false;
            const useGoogleAI = this.config.get('useGoogleAI') || false;
            const useOllama = !useOpenAI && !useGoogleAI; // Default to Ollama if no external APIs
            try {
                if (useOpenAI) {
                    return yield this.callOpenAI(prompt, context);
                }
                else if (useGoogleAI) {
                    return yield this.callGoogleAI(prompt, context);
                }
                else {
                    return yield this.callOllama(prompt, context);
                }
            }
            catch (error) {
                this.outputChannel.appendLine(`AI Error: ${error}`);
                throw error;
            }
        });
    }
    // Ollama Integration - UPDATED WITH YOUR MODEL NAME
    callOllama(prompt, context) {
        return __awaiter(this, void 0, void 0, function* () {
            const model = this.config.get('ollamaModel') || 'Mistral'; // FIXED: Using your model name
            const fullPrompt = this.buildFullPrompt(prompt, context);
            const response = yield this.makeHTTPRequest('http://localhost:11434/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: model,
                    prompt: fullPrompt,
                    stream: false,
                    options: {
                        temperature: 0.7,
                        top_p: 0.9
                    }
                })
            });
            return this.parseAIResponse(response.response);
        });
    }
    // OpenAI Integration
    callOpenAI(prompt, context) {
        return __awaiter(this, void 0, void 0, function* () {
            const apiKey = this.config.get('openaiApiKey');
            const model = this.config.get('openaiModel') || 'gpt-4';
            if (!apiKey) {
                throw new Error('OpenAI API key not configured');
            }
            const messages = this.buildPrompt(prompt, context);
            const response = yield this.makeHTTPRequest('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: model,
                    messages: messages,
                    temperature: 0.7,
                    max_tokens: 4000
                })
            });
            return this.parseAIResponse(response.choices[0].message.content);
        });
    }
    // Google AI Integration
    callGoogleAI(prompt, context) {
        return __awaiter(this, void 0, void 0, function* () {
            const apiKey = this.config.get('googleApiKey');
            const model = this.config.get('googleModel') || 'gemini-pro';
            if (!apiKey) {
                throw new Error('Google AI API key not configured');
            }
            const fullPrompt = this.buildFullPrompt(prompt, context);
            const response = yield this.makeHTTPRequest(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    contents: [{
                            parts: [{
                                    text: fullPrompt
                                }]
                        }],
                    generationConfig: {
                        temperature: 0.7,
                        maxOutputTokens: 4000
                    }
                })
            });
            return this.parseAIResponse(response.candidates[0].content.parts[0].text);
        });
    }
    // Build context-aware prompts
    buildPrompt(prompt, context) {
        const messages = [
            {
                role: 'system',
                content: `You are Noufal AI Assistant, a senior full-stack developer AI. You can:
- Generate production-ready code for web, desktop, and mobile apps
- Write comprehensive tests and documentation
- Refactor and optimize code for better performance
- Explain complex code concepts clearly
- Suggest architectural improvements
- Handle file operations and terminal commands
- Deploy applications to various platforms

Always provide clear explanations and follow best practices. Format code blocks properly and suggest actionable next steps.`
            }
        ];
        if (context && context.length > 0) {
            const contextText = context.map(file => `File: ${file.path}\nLanguage: ${file.language}\nContent:\n\`\`\`${file.language}\n${file.content}\n\`\`\``).join('\n\n');
            messages.push({
                role: 'user',
                content: `Context:\n${contextText}\n\nRequest: ${prompt}`
            });
        }
        else {
            messages.push({
                role: 'user',
                content: prompt
            });
        }
        return messages;
    }
    buildFullPrompt(prompt, context) {
        let fullPrompt = `You are Noufal AI Assistant, a senior full-stack developer AI. You can:
- Generate production-ready code for web, desktop, and mobile apps
- Write comprehensive tests and documentation
- Refactor and optimize code for better performance
- Explain complex code concepts clearly
- Suggest architectural improvements
- Handle file operations and terminal commands
- Deploy applications to various platforms

Always provide clear explanations and follow best practices. Format code blocks properly and suggest actionable next steps.

`;
        if (context && context.length > 0) {
            const contextText = context.map(file => `File: ${file.path}\nLanguage: ${file.language}\nContent:\n\`\`\`${file.language}\n${file.content}\n\`\`\``).join('\n\n');
            fullPrompt += `Context:\n${contextText}\n\nRequest: ${prompt}`;
        }
        else {
            fullPrompt += `Request: ${prompt}`;
        }
        return fullPrompt;
    }
    // Parse AI responses
    parseAIResponse(response) {
        // Extract file operations
        const fileMatches = response.match(/```file:(.+?)\n([\s\S]*?)```/g);
        const files = [];
        if (fileMatches) {
            fileMatches.forEach(match => {
                const lines = match.split('\n');
                const filePath = lines[0].replace('```file:', '').trim();
                const operation = filePath.startsWith('+') ? 'create' :
                    filePath.startsWith('-') ? 'delete' : 'modify';
                const cleanPath = filePath.replace(/^[+\-]/, '');
                const content = lines.slice(1, -1).join('\n');
                files.push({ path: cleanPath, content, operation });
            });
        }
        // Extract terminal commands
        const cmdMatches = response.match(/```bash\n([\s\S]*?)```/g) ||
            response.match(/```shell\n([\s\S]*?)```/g) ||
            response.match(/```terminal\n([\s\S]*?)```/g);
        const commands = [];
        if (cmdMatches) {
            cmdMatches.forEach(match => {
                const command = match.replace(/```(bash|shell|terminal)\n/, '').replace(/```$/, '').trim();
                commands.push({ command, description: `Run: ${command}` });
            });
        }
        return {
            content: response,
            files: files.length > 0 ? files : undefined,
            commands: commands.length > 0 ? commands : undefined
        };
    }
    // File operations
    readFile(filePath) {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const workspaceRoot = (_b = (_a = vscode.workspace.workspaceFolders) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.uri.fsPath;
                if (!workspaceRoot) {
                    throw new Error('No workspace folder found');
                }
                const fullPath = path.join(workspaceRoot, filePath);
                return yield fs.promises.readFile(fullPath, 'utf8');
            }
            catch (error) {
                throw new Error(`Failed to read file ${filePath}: ${error}`);
            }
        });
    }
    writeFile(filePath, content) {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const workspaceRoot = (_b = (_a = vscode.workspace.workspaceFolders) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.uri.fsPath;
                if (!workspaceRoot) {
                    throw new Error('No workspace folder found');
                }
                const fullPath = path.join(workspaceRoot, filePath);
                const dir = path.dirname(fullPath);
                // Create directory if it doesn't exist
                yield fs.promises.mkdir(dir, { recursive: true });
                // Write file
                yield fs.promises.writeFile(fullPath, content, 'utf8');
                // Open file in editor
                const document = yield vscode.workspace.openTextDocument(fullPath);
                yield vscode.window.showTextDocument(document);
                this.outputChannel.appendLine(`File created/updated: ${filePath}`);
                vscode.window.showInformationMessage(`✅ File ${filePath} created/updated successfully`);
            }
            catch (error) {
                throw new Error(`Failed to write file ${filePath}: ${error}`);
            }
        });
    }
    deleteFile(filePath) {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const workspaceRoot = (_b = (_a = vscode.workspace.workspaceFolders) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.uri.fsPath;
                if (!workspaceRoot) {
                    throw new Error('No workspace folder found');
                }
                const fullPath = path.join(workspaceRoot, filePath);
                yield fs.promises.unlink(fullPath);
                this.outputChannel.appendLine(`File deleted: ${filePath}`);
                vscode.window.showInformationMessage(`✅ File ${filePath} deleted successfully`);
            }
            catch (error) {
                throw new Error(`Failed to delete file ${filePath}: ${error}`);
            }
        });
    }
    // Terminal operations
    runTerminalCommand(command) {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function* () {
            try {
                const workspaceRoot = (_b = (_a = vscode.workspace.workspaceFolders) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.uri.fsPath;
                if (!workspaceRoot) {
                    throw new Error('No workspace folder found');
                }
                // Show confirmation dialog
                const confirm = yield vscode.window.showQuickPick(['Yes', 'No'], {
                    placeHolder: `Execute command: ${command}?`
                });
                if (confirm === 'Yes') {
                    const { stdout, stderr } = yield execAsync(command, { cwd: workspaceRoot });
                    if (stdout) {
                        this.outputChannel.appendLine(`Command output: ${stdout}`);
                    }
                    if (stderr) {
                        this.outputChannel.appendLine(`Command error: ${stderr}`);
                    }
                    vscode.window.showInformationMessage(`✅ Command executed: ${command}`);
                }
            }
            catch (error) {
                this.outputChannel.appendLine(`Command failed: ${error}`);
                vscode.window.showErrorMessage(`❌ Command failed: ${error}`);
            }
        });
    }
    // Get workspace context
    getWorkspaceContext() {
        return __awaiter(this, void 0, void 0, function* () {
            const context = [];
            // Get all open editors
            const editors = vscode.window.visibleTextEditors;
            for (const editor of editors) {
                const document = editor.document;
                const language = document.languageId;
                const content = document.getText();
                const relativePath = vscode.workspace.asRelativePath(document.uri);
                context.push({
                    path: relativePath,
                    content: content,
                    language: language,
                    isModified: document.isDirty
                });
            }
            return context;
        });
    }
    // HTTP request helper
    makeHTTPRequest(url, options) {
        return new Promise((resolve, reject) => {
            const isHttps = url.startsWith('https');
            const client = isHttps ? https : http;
            const req = client.request(url, options, (res) => {
                let data = '';
                res.on('data', (chunk) => {
                    data += chunk;
                });
                res.on('end', () => {
                    try {
                        const jsonData = JSON.parse(data);
                        resolve(jsonData);
                    }
                    catch (error) {
                        reject(new Error(`Failed to parse response: ${error}`));
                    }
                });
            });
            req.on('error', (error) => {
                reject(error);
            });
            if (options.body) {
                req.write(options.body);
            }
            req.end();
        });
    }
}
// Global instance
let aiAssistant;
// Activation function
function activate(context) {
    aiAssistant = new AICodingAssistant();
    // Register all commands
    const commands = [
        vscode.commands.registerCommand('aiAssistant.start', () => __awaiter(this, void 0, void 0, function* () {
            vscode.window.showInformationMessage('🚀 Noufal AI Assistant is ready! Use Ctrl+Shift+C to open chat or Ctrl+Shift+A to generate code.');
        })),
        vscode.commands.registerCommand('aiAssistant.chat', () => __awaiter(this, void 0, void 0, function* () {
            // Simple chat implementation - opens a webview panel
            const panel = vscode.window.createWebviewPanel('noufalAIChat', '💬 Noufal AI Chat', vscode.ViewColumn.Beside, {
                enableScripts: true,
                retainContextWhenHidden: true
            });
            panel.webview.html = `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Noufal AI Chat</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            margin: 0;
                            padding: 20px;
                            background: var(--vscode-editor-background);
                            color: var(--vscode-editor-foreground);
                        }
                        .header {
                            text-align: center;
                            margin-bottom: 30px;
                        }
                        .chat-container {
                            max-width: 800px;
                            margin: 0 auto;
                        }
                        .message {
                            margin-bottom: 20px;
                            padding: 15px;
                            border-radius: 8px;
                            background: var(--vscode-input-background);
                            border: 1px solid var(--vscode-input-border);
                        }
                        .user-message {
                            background: var(--vscode-button-background);
                            color: var(--vscode-button-foreground);
                        }
                        .input-container {
                            margin-top: 30px;
                        }
                        .message-input {
                            width: 100%;
                            padding: 12px;
                            border: 1px solid var(--vscode-input-border);
                            border-radius: 4px;
                            background: var(--vscode-input-background);
                            color: var(--vscode-input-foreground);
                            font-size: 14px;
                            resize: vertical;
                            min-height: 60px;
                        }
                        .send-button {
                            margin-top: 10px;
                            padding: 10px 20px;
                            background: var(--vscode-button-background);
                            color: var(--vscode-button-foreground);
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 14px;
                        }
                        .send-button:hover {
                            background: var(--vscode-button-hoverBackground);
                        }
                        .template-buttons {
                            margin-bottom: 20px;
                        }
                        .template-button {
                            margin: 5px;
                            padding: 8px 12px;
                            background: var(--vscode-button-secondaryBackground);
                            color: var(--vscode-button-secondaryForeground);
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 12px;
                        }
                        .template-button:hover {
                            background: var(--vscode-button-secondaryHoverBackground);
                        }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🤖 Noufal AI Assistant</h1>
                        <p>Your AI coding assistant is ready to help!</p>
                    </div>
                    
                    <div class="chat-container">
                        <div class="template-buttons">
                            <button class="template-button" onclick="insertTemplate('Generate a React component')">⚛️ React</button>
                            <button class="template-button" onclick="insertTemplate('Create a Python function')">🐍 Python</button>
                            <button class="template-button" onclick="insertTemplate('Explain this code')">❓ Explain</button>
                            <button class="template-button" onclick="insertTemplate('Fix this bug')">🐛 Debug</button>
                        </div>
                        
                        <div id="messages">
                            <div class="message">
                                👋 Hello! I'm Noufal AI Assistant. I can help you with coding, debugging, and development tasks. What would you like to work on?
                            </div>
                        </div>
                        
                        <div class="input-container">
                            <textarea 
                                id="messageInput" 
                                class="message-input" 
                                placeholder="Type your message here... (Shift+Enter for new line)"
                                rows="3"
                            ></textarea>
                            <button class="send-button" onclick="sendMessage()">📤 Send Message</button>
                        </div>
                    </div>
                    
                    <script>
                        const vscode = acquireVsCodeApi();
                        
                        function sendMessage() {
                            const input = document.getElementById('messageInput');
                            const text = input.value.trim();
                            
                            if (!text) return;
                            
                            // Add user message
                            addMessage(text, 'user');
                            
                            // Send to extension
                            vscode.postMessage({
                                command: 'sendMessage',
                                text: text
                            });
                            
                            input.value = '';
                        }
                        
                        function addMessage(text, role) {
                            const messagesDiv = document.getElementById('messages');
                            const messageDiv = document.createElement('div');
                            messageDiv.className = 'message ' + (role === 'user' ? 'user-message' : '');
                            messageDiv.textContent = text;
                            messagesDiv.appendChild(messageDiv);
                            messagesDiv.scrollTop = messagesDiv.scrollHeight;
                        }
                        
                        function insertTemplate(template) {
                            const input = document.getElementById('messageInput');
                            input.value = template;
                            input.focus();
                        }
                        
                        // Handle Enter key
                        document.getElementById('messageInput').addEventListener('keydown', function(e) {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                sendMessage();
                            }
                        });
                        
                        // Handle messages from extension
                        window.addEventListener('message', event => {
                            const message = event.data;
                            if (message.command === 'aiResponse') {
                                addMessage(message.text, 'assistant');
                            }
                        });
                    </script>
                </body>
                </html>
            `;
            panel.webview.onDidReceiveMessage((message) => __awaiter(this, void 0, void 0, function* () {
                if (message.command === 'sendMessage') {
                    try {
                        const context = yield aiAssistant.getWorkspaceContext();
                        const response = yield aiAssistant.interactWithAI(message.text, context);
                        panel.webview.postMessage({
                            command: 'aiResponse',
                            text: response.content
                        });
                        // Apply file operations
                        if (response.files) {
                            for (const file of response.files) {
                                if (file.operation === 'create' || file.operation === 'modify') {
                                    yield aiAssistant.writeFile(file.path, file.content);
                                }
                                else if (file.operation === 'delete') {
                                    yield aiAssistant.deleteFile(file.path);
                                }
                            }
                        }
                        // Execute terminal commands
                        if (response.commands) {
                            for (const cmd of response.commands) {
                                yield aiAssistant.runTerminalCommand(cmd.command);
                            }
                        }
                    }
                    catch (error) {
                        panel.webview.postMessage({
                            command: 'aiResponse',
                            text: `❌ Error: ${error}`
                        });
                    }
                }
            }));
        })),
        vscode.commands.registerCommand('aiAssistant.configure', configureAPIKeys),
        vscode.commands.registerCommand('aiAssistant.code', generateCode),
        vscode.commands.registerCommand('aiAssistant.explain', explainCode),
        vscode.commands.registerCommand('aiAssistant.refactor', refactorCode),
        vscode.commands.registerCommand('aiAssistant.test', generateTests),
        vscode.commands.registerCommand('aiAssistant.deploy', deployProject),
        vscode.commands.registerCommand('aiAssistant.terminal', runTerminalCommand),
        vscode.commands.registerCommand('aiAssistant.fileOps', fileOperations)
    ];
    context.subscriptions.push(...commands);
}
exports.activate = activate;
// Configuration function - UPDATED WITH YOUR MODEL NAME
function configureAPIKeys() {
    return __awaiter(this, void 0, void 0, function* () {
        const service = yield vscode.window.showQuickPick(['OpenAI GPT', 'Google AI', 'Ollama (Local)'], { placeHolder: 'Select AI service to configure' });
        if (!service)
            return;
        const config = vscode.workspace.getConfiguration('aiAssistant');
        if (service === 'OpenAI GPT') {
            const apiKey = yield vscode.window.showInputBox({
                prompt: 'Enter your OpenAI API key',
                placeHolder: 'sk-...',
                password: true
            });
            if (apiKey) {
                yield config.update('openaiApiKey', apiKey);
                yield config.update('useOpenAI', true);
                yield config.update('useGoogleAI', false);
                vscode.window.showInformationMessage('✅ OpenAI configured successfully');
            }
        }
        else if (service === 'Google AI') {
            const apiKey = yield vscode.window.showInputBox({
                prompt: 'Enter your Google AI API key',
                placeHolder: 'your-google-ai-key',
                password: true
            });
            if (apiKey) {
                yield config.update('googleApiKey', apiKey);
                yield config.update('useOpenAI', false);
                yield config.update('useGoogleAI', true);
                vscode.window.showInformationMessage('✅ Google AI configured successfully');
            }
        }
        else {
            // UPDATED: Added your "Mistral" model as default option
            const model = yield vscode.window.showQuickPick(['Mistral', 'deepseek-coder:6.7b', 'codellama:7b', 'mistral:7b-instruct'], { placeHolder: 'Select Ollama model (Mistral is your current model)' });
            if (model) {
                yield config.update('ollamaModel', model);
                yield config.update('useOpenAI', false);
                yield config.update('useGoogleAI', false);
                vscode.window.showInformationMessage(`✅ Ollama configured with ${model}`);
            }
        }
    });
}
// Command functions
function generateCode() {
    return __awaiter(this, void 0, void 0, function* () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        const prompt = yield vscode.window.showInputBox({
            prompt: '💻 What code would you like to generate?',
            placeHolder: 'e.g., "Create a React component for user login"'
        });
        if (!prompt)
            return;
        try {
            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: '🤖 Generating code...',
                cancellable: false
            }, (progress) => __awaiter(this, void 0, void 0, function* () {
                const context = yield aiAssistant.getWorkspaceContext();
                const response = yield aiAssistant.interactWithAI(prompt, context);
                // Apply file operations
                if (response.files) {
                    for (const file of response.files) {
                        if (file.operation === 'create' || file.operation === 'modify') {
                            yield aiAssistant.writeFile(file.path, file.content);
                        }
                        else if (file.operation === 'delete') {
                            yield aiAssistant.deleteFile(file.path);
                        }
                    }
                }
                // Execute terminal commands
                if (response.commands) {
                    for (const cmd of response.commands) {
                        yield aiAssistant.runTerminalCommand(cmd.command);
                    }
                }
                // Show response
                if (response.content) {
                    const panel = vscode.window.createWebviewPanel('aiResponse', 'AI Response', vscode.ViewColumn.Beside, {});
                    panel.webview.html = `
                    <html>
                        <body>
                            <h2>AI Generated Code</h2>
                            <pre>${response.content}</pre>
                        </body>
                    </html>
                `;
                }
            }));
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Error: ${error}`);
        }
    });
}
function explainCode() {
    return __awaiter(this, void 0, void 0, function* () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        const selection = editor.selection;
        const text = editor.document.getText(selection) || editor.document.getText();
        if (!text.trim()) {
            vscode.window.showErrorMessage('No code to explain');
            return;
        }
        const prompt = `📖 Explain this code:\n\n${text}`;
        try {
            const response = yield aiAssistant.interactWithAI(prompt);
            const panel = vscode.window.createWebviewPanel('aiExplanation', 'Code Explanation', vscode.ViewColumn.Beside, {});
            panel.webview.html = `
            <html>
                <body>
                    <h2>Code Explanation</h2>
                    <pre>${response.content}</pre>
                </body>
            </html>
        `;
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Error: ${error}`);
        }
    });
}
function refactorCode() {
    return __awaiter(this, void 0, void 0, function* () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        const selection = editor.selection;
        const text = editor.document.getText(selection) || editor.document.getText();
        if (!text.trim()) {
            vscode.window.showErrorMessage('No code to refactor');
            return;
        }
        const prompt = `🔧 Refactor this code to improve readability, performance, and best practices:\n\n${text}`;
        try {
            const response = yield aiAssistant.interactWithAI(prompt);
            const panel = vscode.window.createWebviewPanel('aiRefactor', 'Refactored Code', vscode.ViewColumn.Beside, {});
            panel.webview.html = `
            <html>
                <body>
                    <h2>Refactored Code</h2>
                    <pre>${response.content}</pre>
                </body>
            </html>
        `;
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Error: ${error}`);
        }
    });
}
function generateTests() {
    return __awaiter(this, void 0, void 0, function* () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }
        const text = editor.document.getText();
        const fileName = editor.document.fileName;
        const prompt = `🧪 Generate comprehensive tests for this code in ${fileName}:\n\n${text}`;
        try {
            const context = yield aiAssistant.getWorkspaceContext();
            const response = yield aiAssistant.interactWithAI(prompt, context);
            const panel = vscode.window.createWebviewPanel('aiTests', 'Generated Tests', vscode.ViewColumn.Beside, {});
            panel.webview.html = `
            <html>
                <body>
                    <h2>Generated Tests</h2>
                    <pre>${response.content}</pre>
                </body>
            </html>
        `;
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Error: ${error}`);
        }
    });
}
function deployProject() {
    return __awaiter(this, void 0, void 0, function* () {
        const prompt = yield vscode.window.showInputBox({
            prompt: '🚀 Where would you like to deploy?',
            placeHolder: 'e.g., "Deploy to Vercel", "Create Docker container", "Deploy to AWS"'
        });
        if (!prompt)
            return;
        try {
            const context = yield aiAssistant.getWorkspaceContext();
            const response = yield aiAssistant.interactWithAI(`Deploy project: ${prompt}`, context);
            const panel = vscode.window.createWebviewPanel('aiDeploy', 'Deployment Guide', vscode.ViewColumn.Beside, {});
            panel.webview.html = `
            <html>
                <body>
                    <h2>Deployment Guide</h2>
                    <pre>${response.content}</pre>
                </body>
            </html>
        `;
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Error: ${error}`);
        }
    });
}
function runTerminalCommand() {
    return __awaiter(this, void 0, void 0, function* () {
        const command = yield vscode.window.showInputBox({
            prompt: '💻 Enter terminal command',
            placeHolder: 'e.g., "npm install", "git status", "python app.py"'
        });
        if (!command)
            return;
        try {
            yield aiAssistant.runTerminalCommand(command);
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Error: ${error}`);
        }
    });
}
function fileOperations() {
    return __awaiter(this, void 0, void 0, function* () {
        const operation = yield vscode.window.showQuickPick(['📁 Create File', '📖 Read File', '✏️ Modify File', '🗑️ Delete File'], { placeHolder: 'Select file operation' });
        if (!operation)
            return;
        const filePath = yield vscode.window.showInputBox({
            prompt: 'Enter file path',
            placeHolder: 'e.g., "src/components/Button.tsx"'
        });
        if (!filePath)
            return;
        try {
            if (operation.includes('Create') || operation.includes('Modify')) {
                const content = yield vscode.window.showInputBox({
                    prompt: 'Enter file content (or describe what to generate)',
                    placeHolder: 'File content or description for AI to generate'
                });
                if (content) {
                    if (content.length < 50) {
                        // If content is short, treat as description for AI
                        const prompt = `Create file ${filePath} with: ${content}`;
                        const response = yield aiAssistant.interactWithAI(prompt);
                        const panel = vscode.window.createWebviewPanel('aiFile', 'Generated File', vscode.ViewColumn.Beside, {});
                        panel.webview.html = `
                        <html>
                            <body>
                                <h2>Generated File: ${filePath}</h2>
                                <pre>${response.content}</pre>
                            </body>
                        </html>
                    `;
                    }
                    else {
                        // Use content directly
                        yield aiAssistant.writeFile(filePath, content);
                    }
                }
            }
            else if (operation.includes('Read')) {
                const content = yield aiAssistant.readFile(filePath);
                const prompt = `Show and explain the content of ${filePath}:\n\n${content}`;
                const response = yield aiAssistant.interactWithAI(prompt);
                const panel = vscode.window.createWebviewPanel('aiFile', 'File Content', vscode.ViewColumn.Beside, {});
                panel.webview.html = `
                <html>
                    <body>
                        <h2>File Content: ${filePath}</h2>
                        <pre>${response.content}</pre>
                    </body>
                </html>
            `;
            }
            else if (operation.includes('Delete')) {
                yield aiAssistant.deleteFile(filePath);
            }
        }
        catch (error) {
            vscode.window.showErrorMessage(`❌ Error: ${error}`);
        }
    });
}
// Deactivation
function deactivate() { }
exports.deactivate = deactivate;
//# sourceMappingURL=extension-simple.js.map