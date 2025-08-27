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
class LRUCache {
    constructor(capacity) {
        this.capacity = capacity;
        this.map = new Map();
    }
    get(key) {
        if (!this.map.has(key))
            return undefined;
        const value = this.map.get(key);
        this.map.delete(key);
        this.map.set(key, value);
        return value;
    }
    set(key, value) {
        if (this.map.has(key))
            this.map.delete(key);
        this.map.set(key, value);
        if (this.map.size > this.capacity) {
            const firstKey = this.map.keys().next().value;
            this.map.delete(firstKey);
        }
    }
}
class MemoryManager {
    constructor() {
        this.sessionTurns = [];
        this.workspaceFilePath = null;
    }
    initialize(context) {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function* () {
            const cfg = vscode.workspace.getConfiguration('aiAssistant');
            const relPath = cfg.get('memory.workspaceStorePath') || '.vscode/noufal-ai/memory.json';
            const ws = (_b = (_a = vscode.workspace.workspaceFolders) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.uri.fsPath;
            this.workspaceFilePath = ws ? path.join(ws, relPath) : null;
            // ensure dir
            if (this.workspaceFilePath) {
                try {
                    yield fs.promises.mkdir(path.dirname(this.workspaceFilePath), { recursive: true });
                }
                catch (_c) { }
            }
        });
    }
    recordTurn(role, text) {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function* () {
            const cfg = vscode.workspace.getConfiguration('aiAssistant');
            if (!((_a = cfg.get('memory.enabled')) !== null && _a !== void 0 ? _a : true))
                return;
            const maxTurns = (_b = cfg.get('memory.maxRecentTurns')) !== null && _b !== void 0 ? _b : 6;
            this.sessionTurns.push({ role, text });
            if (this.sessionTurns.length > maxTurns * 2) {
                this.sessionTurns = this.sessionTurns.slice(-maxTurns * 2);
            }
            yield this.appendWorkspaceSummaryIfPossible(role, text);
        });
    }
    buildMemoryContext(currentPrompt) {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function* () {
            const cfg = vscode.workspace.getConfiguration('aiAssistant');
            if (!((_a = cfg.get('memory.enabled')) !== null && _a !== void 0 ? _a : true))
                return '';
            const maxTurns = (_b = cfg.get('memory.maxRecentTurns')) !== null && _b !== void 0 ? _b : 6;
            const recent = this.sessionTurns.slice(-maxTurns);
            const recentText = recent.map(t => `${t.role.toUpperCase()}: ${t.text}`).join('\n');
            let workspaceSummary = '';
            if (this.workspaceFilePath && (yield this.exists(this.workspaceFilePath))) {
                try {
                    const data = JSON.parse(yield fs.promises.readFile(this.workspaceFilePath, 'utf8'));
                    const items = (data.summaries || []).slice(-5);
                    workspaceSummary = items.map((s) => `- ${s.when}: ${s.summary}`).join('\n');
                }
                catch (_c) { }
            }
            const header = '[Memory]\n';
            const wsBlock = workspaceSummary ? `Workspace summaries:\n${workspaceSummary}\n` : '';
            const recentBlock = recentText ? `Recent turns:\n${recentText}\n` : '';
            return header + wsBlock + recentBlock;
        });
    }
    clearSession() {
        return __awaiter(this, void 0, void 0, function* () {
            this.sessionTurns = [];
        });
    }
    clearWorkspace() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this.workspaceFilePath && (yield this.exists(this.workspaceFilePath))) {
                try {
                    yield fs.promises.unlink(this.workspaceFilePath);
                }
                catch (_a) { }
            }
        });
    }
    appendWorkspaceSummaryIfPossible(role, text) {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.workspaceFilePath)
                return;
            // keep a lightweight rolling summary; here we store raw last turns, a real impl would summarize
            const record = { when: new Date().toISOString(), role, summary: text.slice(0, 400) };
            let data = { summaries: [] };
            if (yield this.exists(this.workspaceFilePath)) {
                try {
                    data = JSON.parse(yield fs.promises.readFile(this.workspaceFilePath, 'utf8')) || { summaries: [] };
                }
                catch (_a) { }
            }
            data.summaries.push(record);
            if (data.summaries.length > 200)
                data.summaries = data.summaries.slice(-200);
            try {
                yield fs.promises.writeFile(this.workspaceFilePath, JSON.stringify(data, null, 2), 'utf8');
            }
            catch (_b) { }
        });
    }
    exists(p) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                yield fs.promises.access(p);
                return true;
            }
            catch (_a) {
                return false;
            }
        });
    }
}
class AICodingAssistant {
    constructor() {
        this.config = vscode.workspace.getConfiguration('aiAssistant');
        this.outputChannel = vscode.window.createOutputChannel('Noufal AI Assistant');
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.text = '$(robot) Noufal AI';
        this.statusBarItem.tooltip = 'Noufal AI Assistant Ready - Click to open chat';
        this.statusBarItem.command = 'aiAssistant.chat';
        this.statusBarItem.show();
        // Enable connection pooling/keep-alive to reduce latency
        this.httpAgent = new http.Agent({ keepAlive: true, maxSockets: 16, keepAliveMsecs: 10000 });
        this.httpsAgent = new https.Agent({ keepAlive: true, maxSockets: 16, keepAliveMsecs: 10000 });
        this.responseCache = new LRUCache(50);
        this.memoryManager = new MemoryManager();
    }
    // Main AI interaction method
    interactWithAI(prompt, context) {
        var _a;
        return __awaiter(this, void 0, void 0, function* () {
            const cacheKey = this.buildCacheKey(prompt, context);
            const cached = this.responseCache.get(cacheKey);
            if (cached) {
                return cached;
            }
            const useOpenAI = this.config.get('useOpenAI') || false;
            const useGoogleAI = this.config.get('useGoogleAI') || false;
            const useOllama = !useOpenAI && !useGoogleAI; // Default to Ollama if no external APIs
            try {
                // Load memory
                const enabled = (_a = this.config.get('memory.enabled')) !== null && _a !== void 0 ? _a : true;
                const memoryContext = enabled ? yield this.memoryManager.buildMemoryContext(prompt) : '';
                if (useOpenAI) {
                    const res = yield this.callOpenAI(memoryContext + '\n' + prompt, context);
                    this.responseCache.set(cacheKey, res);
                    return res;
                }
                else if (useGoogleAI) {
                    const res = yield this.callGoogleAI(memoryContext + '\n' + prompt, context);
                    this.responseCache.set(cacheKey, res);
                    return res;
                }
                else {
                    const res = yield this.callOllama(memoryContext + '\n' + prompt, context);
                    this.responseCache.set(cacheKey, res);
                    return res;
                }
            }
            catch (error) {
                this.outputChannel.appendLine(`AI Error: ${error}`);
                throw error;
            }
        });
    }
    // Streaming interface for Ollama used by chat view
    interactWithAIStream(prompt, context, onChunk, onDone, onError) {
        return __awaiter(this, void 0, void 0, function* () {
            const useOpenAI = this.config.get('useOpenAI') || false;
            const useGoogleAI = this.config.get('useGoogleAI') || false;
            if (useOpenAI || useGoogleAI) {
                // Fallback to non-streaming for non-Ollama providers
                try {
                    const res = yield this.interactWithAI(prompt, context);
                    onChunk(res.content);
                    onDone(res.content);
                }
                catch (e) {
                    onError(e);
                }
                return;
            }
            try {
                yield this.streamOllama(prompt, context, onChunk, onDone);
            }
            catch (e) {
                onError(e);
            }
        });
    }
    // Ollama Integration - UPDATED WITH YOUR MODEL NAME
    callOllama(prompt, context) {
        return __awaiter(this, void 0, void 0, function* () {
            const model = this.config.get('ollamaModel') || 'Mistral';
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
            }, 30000, 2);
            return this.parseAIResponse(response.response);
        });
    }
    streamOllama(prompt, context, onChunk, onDone) {
        return __awaiter(this, void 0, void 0, function* () {
            const model = this.config.get('ollamaModel') || 'Mistral';
            const fullPrompt = this.buildFullPrompt(prompt, context);
            const url = 'http://localhost:11434/api/generate';
            const body = JSON.stringify({ model, prompt: fullPrompt, stream: true, options: { temperature: 0.7, top_p: 0.9 } });
            const client = http;
            const agent = this.httpAgent;
            const req = client.request(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, agent }, (res) => {
                let buffer = '';
                let total = '';
                res.on('data', (chunk) => {
                    buffer += chunk.toString();
                    let idx;
                    while ((idx = buffer.indexOf('\n')) >= 0) {
                        const line = buffer.slice(0, idx).trim();
                        buffer = buffer.slice(idx + 1);
                        if (!line)
                            continue;
                        try {
                            const obj = JSON.parse(line);
                            if (obj.response) {
                                total += obj.response;
                                onChunk(obj.response);
                            }
                            if (obj.done) {
                                onDone(total);
                            }
                        }
                        catch ( /* ignore parse errors for partial lines */_a) { /* ignore parse errors for partial lines */ }
                    }
                });
            });
            req.on('error', (e) => { throw e; });
            req.write(body);
            req.end();
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
            }, 45000, 2);
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
            }, 45000, 2);
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
            const keywords = prompt.toLowerCase().split(/[^a-z0-9_]+/).filter(Boolean);
            const relevant = context
                .filter(file => this.isRelevantFile(file, keywords))
                .slice(0, 3)
                .map(file => ({
                path: file.path,
                language: file.language,
                content: file.content.slice(0, 1000)
            }));
            if (relevant.length > 0) {
                const contextText = relevant.map(file => `File: ${file.path}\nLanguage: ${file.language}\nContent:\n\`\`\`${file.language}\n${file.content}\n\`\`\``).join('\n\n');
                fullPrompt += `Context:\n${contextText}\n\n`;
            }
            fullPrompt += `Request: ${prompt}`;
        }
        else {
            fullPrompt += `Request: ${prompt}`;
        }
        return fullPrompt;
    }
    isRelevantFile(file, keywords) {
        const hay = (file.path + ' ' + file.content.slice(0, 400)).toLowerCase();
        return keywords.some(k => hay.includes(k));
    }
    buildCacheKey(prompt, context) {
        const ctx = (context || [])
            .slice(0, 3)
            .map(f => ({ p: f.path, l: f.language, c: f.content.slice(0, 200) }));
        return JSON.stringify({ p: prompt, c: ctx });
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
                    throw new Error('No workspace folder found. Please open a folder first.');
                }
                if (!this.isValidFilePath(filePath)) {
                    throw new Error(`Invalid file path: ${filePath}`);
                }
                const fullPath = path.resolve(workspaceRoot, filePath);
                if (!fullPath.startsWith(workspaceRoot)) {
                    throw new Error('File path outside workspace not allowed');
                }
                const dir = path.dirname(fullPath);
                if (yield this.fileExists(fullPath)) {
                    const overwrite = yield vscode.window.showWarningMessage(`File ${filePath} already exists. Overwrite?`, 'Yes', 'No');
                    if (overwrite !== 'Yes') {
                        return;
                    }
                }
                try {
                    yield fs.promises.mkdir(dir, { recursive: true });
                }
                catch (error) {
                    if (error.code !== 'EEXIST') {
                        throw new Error(`Cannot create directory: ${error.message || error}`);
                    }
                }
                yield vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: `Creating ${path.basename(filePath)}...`,
                    cancellable: false
                }, () => __awaiter(this, void 0, void 0, function* () {
                    yield fs.promises.writeFile(fullPath, content, 'utf8');
                }));
                const document = yield vscode.workspace.openTextDocument(fullPath);
                yield vscode.window.showTextDocument(document);
                const result = yield vscode.window.showInformationMessage(`✅ File ${filePath} created successfully`, 'Open Folder', 'Close');
                if (result === 'Open Folder') {
                    vscode.commands.executeCommand('workbench.files.action.showActiveFileInExplorer');
                }
                this.outputChannel.appendLine(`✅ File created: ${filePath}`);
            }
            catch (error) {
                const errorMsg = `Failed to create file ${filePath}: ${error.message || error}`;
                this.outputChannel.appendLine(`❌ ${errorMsg}`);
                vscode.window.showErrorMessage(errorMsg);
                throw error;
            }
        });
    }
    isValidFilePath(filePath) {
        const invalidChars = /[<>:"|?*]/;
        const invalidPatterns = /^(con|prn|aux|nul|com[1-9]|lpt[1-9])$/i;
        return !invalidChars.test(filePath) &&
            !invalidPatterns.test(path.basename(filePath, path.extname(filePath))) &&
            filePath.length > 0 && filePath.length < 260;
    }
    fileExists(filePath) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                yield fs.promises.access(filePath);
                return true;
            }
            catch (_a) {
                return false;
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
    // HTTP request helper with timeout, retries, and keep-alive
    makeHTTPRequest(url, options, timeoutMs = 30000, retries = 3) {
        return __awaiter(this, void 0, void 0, function* () {
            const isHttps = url.startsWith('https');
            const client = isHttps ? https : http;
            const agent = isHttps ? this.httpsAgent : this.httpAgent;
            const attempt = (attemptNum) => {
                return new Promise((resolve, reject) => {
                    const req = client.request(url, Object.assign(Object.assign({}, options), { agent }), (res) => {
                        let data = '';
                        res.on('data', (chunk) => { data += chunk; });
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
                    req.setTimeout(timeoutMs, () => {
                        req.destroy(new Error(`Request timeout after ${timeoutMs}ms`));
                    });
                    req.on('error', (error) => {
                        reject(error);
                    });
                    if (options.body) {
                        req.write(options.body);
                    }
                    req.end();
                });
            };
            for (let i = 0; i <= retries; i++) {
                try {
                    return yield attempt(i);
                }
                catch (error) {
                    if (i === retries)
                        throw error;
                    const backoffMs = Math.min(2000 * Math.pow(2, i), 10000);
                    yield new Promise(r => setTimeout(r, backoffMs));
                }
            }
        });
    }
}
// Global instance
let aiAssistant;
// Activation function
function activate(context) {
    aiAssistant = new AICodingAssistant();
    // Initialize memory manager with workspace path
    aiAssistant['memoryManager'].initialize(context);
    // Register all commands
    const commands = [
        vscode.commands.registerCommand('aiAssistant.start', () => __awaiter(this, void 0, void 0, function* () {
            vscode.window.showInformationMessage('🚀 Noufal AI Assistant is ready! Use Ctrl+Alt+C to open chat or Ctrl+Alt+A to generate code.');
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
                    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
                    <title>Noufal AI Chat</title>
                    <style>
                        :root {
                            --bg-primary: var(--vscode-editor-background);
                            --bg-secondary: var(--vscode-input-background);
                            --text-primary: var(--vscode-editor-foreground);
                            --accent: var(--vscode-button-background);
                        }
                        * { box-sizing: border-box; }
                        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background: var(--bg-primary); color: var(--text-primary); }
                        .chat-container { display: flex; flex-direction: column; height: 100vh; }
                        .header { padding: 12px 20px; border-bottom: 1px solid var(--vscode-input-border); display: flex; align-items: center; justify-content: space-between; gap: 12px; }
                        .brand { display: flex; align-items: center; gap: 8px; }
                        .toolbar { display: flex; align-items: center; gap: 8px; }
                        .pill { padding: 4px 8px; border: 1px solid var(--vscode-input-border); border-radius: 999px; font-size: 12px; opacity: .9; }
                        .btn { padding: 6px 10px; border-radius: 6px; border: 1px solid var(--vscode-input-border); background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); cursor: pointer; }
                        .btn:hover { background: var(--vscode-button-secondaryHoverBackground); }
                        .messages { flex: 1; overflow: auto; padding: 16px 20px; }
                        .message { position: relative; padding: 12px 16px; margin: 8px 0; border-radius: 8px; background: var(--bg-secondary); border: 1px solid var(--vscode-input-border); opacity: 0; animation: fadeIn .2s ease-in forwards; max-width: 80%; }
                        .msg-actions { position: absolute; top: 8px; right: 8px; display: flex; gap: 4px; opacity: 0; transition: opacity .15s; }
                        .message:hover .msg-actions { opacity: 1; }
                        .user { align-self: flex-end; background: var(--accent); color: var(--vscode-button-foreground); }
                        .assistant { align-self: flex-start; }
                        .footer { padding: 12px 20px; border-top: 1px solid var(--vscode-input-border); }
                        .row { display: flex; gap: 8px; }
                        textarea { flex: 1; resize: vertical; min-height: 56px; padding: 10px 12px; border: 1px solid var(--vscode-input-border); border-radius: 6px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); }
                        button { padding: 10px 14px; border-radius: 6px; border: none; cursor: pointer; background: var(--vscode-button-background); color: var(--vscode-button-foreground); }
                        button:hover { background: var(--vscode-button-hoverBackground); }
                        .typing { display: none; opacity: .8; font-size: 12px; margin-top: 6px; }
                        .typing.active { display: block; }
                        pre { background: #111; padding: 12px; border-radius: 6px; overflow: auto; border-left: 3px solid var(--accent); }
                        code { font-family: ui-monospace, Menlo, Monaco, 'Courier New', monospace; }
                        @keyframes fadeIn { to { opacity: 1; } }
                        .templates { padding: 8px 20px; display: flex; gap: 6px; flex-wrap: wrap; border-bottom: 1px solid var(--vscode-input-border); }
                        .attachments { padding: 8px 20px; border-bottom: 1px solid var(--vscode-input-border); }
                        .attachment-item { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 6px 10px; border: 1px solid var(--vscode-input-border); border-radius: 6px; margin: 4px 0; font-size: 12px; }
                        .template { background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); }
                        .template:hover { background: var(--vscode-button-secondaryHoverBackground); }
                        .progress { height: 2px; width: 100%; background: transparent; position: relative; overflow: hidden; }
                        .progress.active::after { content: ''; position: absolute; left: -40%; width: 40%; height: 100%; background: var(--vscode-button-background); animation: bar 1.2s infinite; }
                        @keyframes bar { 0% { left: -40%; } 50% { left: 60%; } 100% { left: 100%; } }
                        .copy-btn { position: absolute; top: 8px; right: 8px; background: rgba(255,255,255,0.06); border: 1px solid var(--vscode-input-border); color: var(--text-primary); padding: 2px 6px; border-radius: 4px; font-size: 11px; cursor: pointer; }
                    </style>
                </head>
                <body>
                    <div class="chat-container">
                        <div class="header">
                            <div class="brand"><span>🤖</span><strong>Noufal AI Assistant</strong></div>
                            <div class="toolbar">
                                <span id="model" class="pill">Model: Ollama</span>
                                <span id="latency" class="pill">Latency: —</span>
                                <select id="providerSelect" class="btn">
                                    <option value="ollama">Ollama</option>
                                    <option value="openai">OpenAI</option>
                                    <option value="google">Google AI</option>
                                </select>
                                <input id="modelInput" class="btn" placeholder="Model (Mistral | gpt-4 | gemini-pro)" />
                                <button class="btn" id="memoryToggleBtn">Memory: On</button>
                                <button class="btn" id="clearSessionBtn">Clear Session</button>
                                <button class="btn" id="clearWorkspaceBtn">Clear Workspace</button>
                                <button class="btn" id="planBtn">Plan</button>
                                <button class="btn" id="attachBtn">Attach</button>
                                <button class="btn" id="clearBtn">Clear</button>
                                <button class="btn" id="checkHealthBtn">Health</button>
                            </div>
                        </div>
                        <div id="progress" class="progress"></div>
                        <div class="templates">
                            <button class="template" onclick="insertTemplate('Generate a React component')">⚛️ React</button>
                            <button class="template" onclick="insertTemplate('Create a Python function')">🐍 Python</button>
                            <button class="template" onclick="insertTemplate('Explain this code')">❓ Explain</button>
                            <button class="template" onclick="insertTemplate('Fix this bug')">🐛 Debug</button>
                        </div>
                        <div id="attachmentsPanel" class="attachments" style="display:none;">
                            <div style="display:flex; align-items:center; justify-content: space-between; margin-bottom:6px;">
                                <strong>Attachments</strong>
                                <div>
                                    <button class="btn" id="detachAllBtn">Remove All</button>
                                    <button class="btn" id="toggleAttachPanelBtn">Hide</button>
                                </div>
                            </div>
                            <div id="attachmentsList"></div>
                        </div>
                        <div id="messages" class="messages">
                            <div class="message assistant">👋 Hello! I'm Noufal AI Assistant. What would you like to work on?</div>
                        </div>
                        <div class="footer">
                            <div class="row">
                                <textarea id="messageInput" placeholder="Type your message... (Shift+Enter for newline)"></textarea>
                                <button onclick="sendMessage()">Send</button>
                            </div>
                            <div id="typing" class="typing">Noufal AI is thinking...</div>
                        </div>
                    </div>
                    
                    <script>
                        const vscode = acquireVsCodeApi();
                        const state = vscode.getState() || { messages: [], attachments: [] };
                        let lastRequestId = 0;
                        let startTime = 0;

                        async function sendMessage() {
                            const input = document.getElementById('messageInput');
                            const typing = document.getElementById('typing');
                            const text = input.value.trim();
                            if (!text) return;

                            addMessage(text, 'user');
                            typing.classList.add('active');
                            document.getElementById('progress').classList.add('active');
                            const requestId = Date.now();
                            lastRequestId = requestId;
                            vscode.postMessage({ command: 'sendMessage', text, requestId, attachments: state.attachments });
                            input.value = '';
                            input.focus();
                        }

                        function addMessage(text, role) {
                            const messagesDiv = document.getElementById('messages');
                            const messageDiv = document.createElement('div');
                            messageDiv.className = 'message ' + (role === 'user' ? 'user' : 'assistant');
                            messageDiv.innerHTML = '<div class="msg-actions">' +
                                '<button class="btn" onclick="copyText(this)">Copy</button>' +
                                (role === 'user' ? '<button class="btn" onclick="regenerate(this)">Regenerate</button><button class="btn" onclick="editResend(this)">Edit & Resend</button>' : '<button class="btn" onclick="deleteMsg(this)">Hide</button>') +
                                '</div>' + renderMarkdown(text);
                            messagesDiv.appendChild(messageDiv);
                            messagesDiv.scrollTop = messagesDiv.scrollHeight;
                            if (typeof (window as any).Prism !== 'undefined' && (window as any).Prism.highlightAllUnder) {
                                (window as any).Prism.highlightAllUnder(messageDiv);
                            }
                            enhanceCodeBlocks(messageDiv);
                            state.messages.push({ role, text });
                            vscode.setState(state);
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
                            if (message.command === 'aiChunk') {
                                // Append chunk to last assistant message or create a new one
                                const messagesDiv = document.getElementById('messages');
                                let last = messagesDiv.lastElementChild;
                                const typing = document.getElementById('typing');
                                if (!last || !last.className.includes('assistant')) {
                                    last = document.createElement('div');
                                    last.className = 'message assistant';
                                    last.innerHTML = '<div class="msg-actions">' +
                                        '<button class="btn" onclick="copyText(this)">Copy</button>' +
                                        '<button class="btn" onclick="deleteMsg(this)">Hide</button>' +
                                        '</div>';
                                    messagesDiv.appendChild(last);
                                }
                                last.innerHTML += renderMarkdown(message.text);
                                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                                enhanceCodeBlocks(last);
                            }
                            if (message.command === 'aiResponse') {
                                const typing = document.getElementById('typing');
                                typing.classList.remove('active');
                                document.getElementById('progress').classList.remove('active');
                                addMessage(message.text, 'assistant');
                                const latency = Date.now() - startTime;
                                document.getElementById('latency').textContent = 'Latency: ' + latency + 'ms';
                            }
                            if (message.command === 'attachmentsAdded') {
                                addAttachments(message.attachments || []);
                            }
                            if (message.command === 'toolResult') {
                                addMessage(message.text, 'assistant');
                            }
                        });

                        // Restore history
                        (function restore(){
                            if (!state.messages || !Array.isArray(state.messages)) return;
                            for (const m of state.messages) addMessage(m.text, m.role);
                        })();

                        document.getElementById('clearBtn').addEventListener('click', () => {
                            document.getElementById('messages').innerHTML = '';
                            state.messages = [];
                            vscode.setState(state);
                        });
                        // Memory toggle reflects current assumption (default on); actual truth will be confirmed after toggle
                        document.getElementById('memoryToggleBtn').addEventListener('click', () => {
                            const btn = document.getElementById('memoryToggleBtn');
                            const on = btn.textContent.includes('On');
                            const next = !on;
                            vscode.postMessage({ command: 'toggleMemory', enabled: next });
                            btn.textContent = 'Memory: ' + (next ? 'On' : 'Off');
                        });
                        document.getElementById('clearSessionBtn').addEventListener('click', () => {
                            vscode.postMessage({ command: 'clearSessionMemory' });
                        });
                        document.getElementById('clearWorkspaceBtn').addEventListener('click', () => {
                            vscode.postMessage({ command: 'clearWorkspaceMemory' });
                        });
                        document.getElementById('planBtn').addEventListener('click', () => {
                            const input = document.getElementById('messageInput');
                            const text = (input.value || '').trim();
                            if (!text) { alert('Enter a goal in the message box first.'); return; }
                            vscode.postMessage({ command: 'plan', goal: text });
                        });
                        document.getElementById('attachBtn').addEventListener('click', () => {
                            vscode.postMessage({ command: 'attachFilesRequest' });
                            document.getElementById('attachmentsPanel').style.display = 'block';
                        });
                        document.getElementById('toggleAttachPanelBtn')?.addEventListener('click', () => {
                            const p = document.getElementById('attachmentsPanel');
                            p.style.display = p.style.display === 'none' ? 'block' : 'none';
                        });
                        document.getElementById('detachAllBtn')?.addEventListener('click', () => {
                            state.attachments = [];
                            renderAttachments();
                            vscode.setState(state);
                        });

                        function addAttachments(list){
                            // list: [{ path: string }]
                            state.attachments = state.attachments.concat(list);
                            renderAttachments();
                            vscode.setState(state);
                        }
                        function renderAttachments(){
                            const list = document.getElementById('attachmentsList');
                            list.innerHTML = '';
                            state.attachments.forEach((a, idx) => {
                                const item = document.createElement('div');
                                item.className = 'attachment-item';
                                item.innerHTML = '<span>' + a.path + '</span><button class="btn" onclick="removeAttachment(' + idx + ')">Remove</button>';
                                list.appendChild(item);
                            });
                        }
                        window.removeAttachment = function(idx){
                            state.attachments.splice(idx,1);
                            renderAttachments();
                            vscode.setState(state);
                        }

                        function regenerate(btn){
                            const text = btn.closest('.message').innerText || '';
                            document.getElementById('messageInput').value = text;
                            sendMessage();
                        }
                        function editResend(btn){
                            const text = btn.closest('.message').innerText || '';
                            const input = document.getElementById('messageInput');
                            input.value = text;
                            input.focus();
                        }

                        function copyText(btn){
                            const container = btn.closest('.message');
                            const text = container.innerText || '';
                            navigator.clipboard.writeText(text);
                        }
                        function deleteMsg(btn){
                            const container = btn.closest('.message');
                            container.remove();
                        }

                        function enhanceCodeBlocks(scope){
                            const blocks = scope.querySelectorAll('pre');
                            blocks.forEach(pre => {
                                if (pre.dataset.enhanced) return;
                                pre.dataset.enhanced = '1';
                                const btn = document.createElement('button');
                                btn.className = 'copy-btn';
                                btn.textContent = 'Copy';
                                btn.addEventListener('click', () => {
                                    const code = pre.innerText || '';
                                    navigator.clipboard.writeText(code);
                                });
                                pre.style.position = 'relative';
                                pre.appendChild(btn);
                            });
                        }

                        function renderMarkdown(text) {
                            // Minimal code fence handling with Prism-compatible markup
                            const bt = String.fromCharCode(96); // backtick
                            const fence = bt + bt + bt;
                            const re = new RegExp(fence + '(\\w+)?\\n([\\s\\S]*?)' + fence, 'g');
                            return text.replace(re, (m, lang, code) => {
                                const safeLang = (lang || 'markup').toLowerCase();
                                const escaped = code.replace(/&/g, '&amp;').replace(/</g, '&lt;');
                                return '<pre><code class="language-' + safeLang + '">' + escaped + '</code></pre>';
                            }).replace(/\n/g, '<br/>' );
                        }

                        // Provider/model controls
                        document.getElementById('providerSelect').addEventListener('change', (e) => {
                            const v = e.target.value;
                            vscode.postMessage({ command: 'setProvider', provider: v });
                        });
                        document.getElementById('modelInput').addEventListener('change', (e) => {
                            const m = e.target.value;
                            vscode.postMessage({ command: 'setModel', model: m });
                            document.getElementById('model').textContent = 'Model: ' + m;
                        });
                        document.getElementById('checkHealthBtn').addEventListener('click', () => {
                            vscode.postMessage({ command: 'checkBackendHealth' });
                        });
                    </script>
                </body>
                </html>
            `;
            panel.webview.onDidReceiveMessage((message) => __awaiter(this, void 0, void 0, function* () {
                var _a, _b;
                if (message.command === 'sendMessage') {
                    try {
                        yield aiAssistant['memoryManager'].recordTurn('user', message.text);
                        const context = yield aiAssistant.getWorkspaceContext();
                        let finalText = '';
                        yield aiAssistant.interactWithAIStream(message.text, context, (chunk) => {
                            panel.webview.postMessage({ command: 'aiChunk', text: chunk });
                        }, (doneText) => {
                            finalText = doneText;
                            panel.webview.postMessage({ command: 'aiResponse', text: doneText });
                            aiAssistant['memoryManager'].recordTurn('assistant', doneText);
                        }, (err) => {
                            panel.webview.postMessage({ command: 'aiResponse', text: `❌ Error: ${err}` });
                        });
                        // Parse operations and show dry-run preview
                        const response = aiAssistant.parseAIResponse(finalText);
                        const filesCount = ((_a = response.files) === null || _a === void 0 ? void 0 : _a.length) || 0;
                        const cmdsCount = ((_b = response.commands) === null || _b === void 0 ? void 0 : _b.length) || 0;
                        if (filesCount + cmdsCount > 0) {
                            const previewLines = [];
                            if (filesCount) {
                                previewLines.push(`Files (${filesCount}):`);
                                for (const f of response.files)
                                    previewLines.push(` - [${f.operation}] ${f.path}`);
                            }
                            if (cmdsCount) {
                                previewLines.push(`Commands (${cmdsCount}):`);
                                for (const c of response.commands)
                                    previewLines.push(` - ${c.command}`);
                            }
                            const choice = yield vscode.window.showInformationMessage(`Apply AI operations?\n\n${previewLines.join('\n')}`, { modal: true }, 'Apply', 'Cancel');
                            if (choice === 'Apply') {
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
                                if (response.commands) {
                                    for (const cmd of response.commands) {
                                        yield aiAssistant.runTerminalCommand(cmd.command);
                                    }
                                }
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
                if (message.command === 'attachFilesRequest') {
                    try {
                        const picks = yield vscode.window.showOpenDialog({ canSelectMany: true, openLabel: 'Attach' });
                        if (!picks || picks.length === 0)
                            return;
                        // Map to workspace-relative paths and read snippets
                        const attachments = [];
                        for (const uri of picks) {
                            const rel = vscode.workspace.asRelativePath(uri);
                            let snippet;
                            try {
                                snippet = (yield fs.promises.readFile(uri.fsPath, 'utf8')).slice(0, 2000);
                            }
                            catch (_c) { }
                            attachments.push({ path: rel, snippet });
                        }
                        panel.webview.postMessage({ command: 'attachmentsAdded', attachments });
                    }
                    catch (e) {
                        panel.webview.postMessage({ command: 'aiResponse', text: `❌ Attach failed: ${e}` });
                    }
                }
                if (message.command === 'toolReadFile') {
                    try {
                        const picked = yield vscode.window.showOpenDialog({ canSelectMany: false, openLabel: 'Read' });
                        if (!picked || picked.length === 0)
                            return;
                        const rel = vscode.workspace.asRelativePath(picked[0]);
                        const text = yield aiAssistant.readFile(rel);
                        panel.webview.postMessage({ command: 'toolResult', text: `📖 Read ${rel}:\n\n\`\`\`\n${text}\n\`\`\`` });
                    }
                    catch (e) {
                        panel.webview.postMessage({ command: 'toolResult', text: `❌ Read failed: ${e}` });
                    }
                }
                if (message.command === 'toolWriteFile') {
                    try {
                        yield aiAssistant.writeFile(message.filePath, message.content);
                        panel.webview.postMessage({ command: 'toolResult', text: `✅ Wrote ${message.filePath}` });
                    }
                    catch (e) {
                        panel.webview.postMessage({ command: 'toolResult', text: `❌ Write failed: ${e}` });
                    }
                }
                if (message.command === 'toolRunCommand') {
                    try {
                        yield aiAssistant.runTerminalCommand(message.commandText);
                        panel.webview.postMessage({ command: 'toolResult', text: `✅ Ran: ${message.commandText}` });
                    }
                    catch (e) {
                        panel.webview.postMessage({ command: 'toolResult', text: `❌ Command failed: ${e}` });
                    }
                }
                if (message.command === 'clearSessionMemory') {
                    yield aiAssistant['memoryManager'].clearSession();
                    vscode.window.showInformationMessage('✅ Session memory cleared');
                }
                if (message.command === 'clearWorkspaceMemory') {
                    yield aiAssistant['memoryManager'].clearWorkspace();
                    vscode.window.showInformationMessage('✅ Workspace memory cleared');
                }
                if (message.command === 'toggleMemory') {
                    try {
                        const cfg = vscode.workspace.getConfiguration('aiAssistant');
                        yield cfg.update('memory.enabled', !!message.enabled, vscode.ConfigurationTarget.Workspace);
                        vscode.window.showInformationMessage(`✅ Memory ${message.enabled ? 'enabled' : 'disabled'}`);
                    }
                    catch (e) {
                        vscode.window.showErrorMessage(`❌ Failed to toggle memory: ${e}`);
                    }
                }
                if (message.command === 'setProvider') {
                    const cfg = vscode.workspace.getConfiguration('aiAssistant');
                    const p = String(message.provider || '').toLowerCase();
                    if (p === 'openai') {
                        yield cfg.update('useOpenAI', true, vscode.ConfigurationTarget.Workspace);
                        yield cfg.update('useGoogleAI', false, vscode.ConfigurationTarget.Workspace);
                    }
                    else if (p === 'google') {
                        yield cfg.update('useOpenAI', false, vscode.ConfigurationTarget.Workspace);
                        yield cfg.update('useGoogleAI', true, vscode.ConfigurationTarget.Workspace);
                    }
                    else {
                        yield cfg.update('useOpenAI', false, vscode.ConfigurationTarget.Workspace);
                        yield cfg.update('useGoogleAI', false, vscode.ConfigurationTarget.Workspace);
                    }
                    vscode.window.showInformationMessage(`✅ Provider set to ${p || 'ollama'}`);
                }
                if (message.command === 'setModel') {
                    const cfg = vscode.workspace.getConfiguration('aiAssistant');
                    const m = String(message.model || '').trim();
                    if (!m)
                        return;
                    yield cfg.update('ollamaModel', m, vscode.ConfigurationTarget.Workspace);
                    yield cfg.update('openaiModel', m, vscode.ConfigurationTarget.Workspace);
                    yield cfg.update('googleModel', m, vscode.ConfigurationTarget.Workspace);
                    vscode.window.showInformationMessage(`✅ Model set to ${m}`);
                }
                if (message.command === 'checkBackendHealth') {
                    try {
                        const base = vscode.workspace.getConfiguration('aiAssistant').get('backendUrl') || 'http://127.0.0.1:8001';
                        const res = yield aiAssistant['makeHTTPRequest'](`${base}/health`, { method: 'GET' }, 10000, 0);
                        vscode.window.showInformationMessage(`✅ Backend health: ${JSON.stringify(res).slice(0, 200)}`);
                    }
                    catch (e) {
                        vscode.window.showErrorMessage(`❌ Backend health failed: ${e}`);
                    }
                }
                if (message.command === 'plan') {
                    try {
                        // Reuse plannerCoderCommand with provided goal
                        const goal = message.goal;
                        if (!goal)
                            return;
                        // Lightweight inline planner using the shared function
                        // We call plannerCoderCommand via executing its logic here to keep scope simple
                        const context = yield aiAssistant.getWorkspaceContext();
                        const planPrompt = `You are a Planner agent. Break this goal into 3-7 actionable steps with brief descriptions and expected outputs. Respond as a numbered list only.\n\nGoal: ${goal}`;
                        const plan = yield aiAssistant.interactWithAI(planPrompt, context);
                        const planPanel = vscode.window.createWebviewPanel('aiPlan', 'Plan', vscode.ViewColumn.Beside, {});
                        planPanel.webview.html = `<html><body><h2>Plan</h2><pre>${plan.content}</pre></body></html>`;
                    }
                    catch (e) {
                        vscode.window.showErrorMessage(`❌ Planning failed: ${e}`);
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
        vscode.commands.registerCommand('aiAssistant.fileOps', fileOperations),
        vscode.commands.registerCommand('aiAssistant.clearSessionMemory', () => __awaiter(this, void 0, void 0, function* () {
            yield aiAssistant['memoryManager'].clearSession();
            vscode.window.showInformationMessage('✅ Session memory cleared');
        })),
        vscode.commands.registerCommand('aiAssistant.clearWorkspaceMemory', () => __awaiter(this, void 0, void 0, function* () {
            yield aiAssistant['memoryManager'].clearWorkspace();
            vscode.window.showInformationMessage('✅ Workspace memory cleared');
        })),
        vscode.commands.registerCommand('aiAssistant.plan', plannerCoderCommand),
        vscode.commands.registerCommand('aiAssistant.checkBackendHealth', () => __awaiter(this, void 0, void 0, function* () {
            try {
                const base = vscode.workspace.getConfiguration('aiAssistant').get('backendUrl') || 'http://127.0.0.1:8001';
                const res = yield aiAssistant['makeHTTPRequest'](`${base}/health`, { method: 'GET' }, 10000, 0);
                vscode.window.showInformationMessage(`✅ Backend health: ${JSON.stringify(res).slice(0, 200)}`);
            }
            catch (e) {
                vscode.window.showErrorMessage(`❌ Backend health failed: ${e}`);
            }
        })),
        vscode.commands.registerCommand('aiAssistant.startBackendWorkflow', () => __awaiter(this, void 0, void 0, function* () {
            try {
                const base = vscode.workspace.getConfiguration('aiAssistant').get('backendUrl') || 'http://127.0.0.1:8001';
                const res = yield aiAssistant['makeHTTPRequest'](`${base}/api/v1/workflows/start`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source: 'vscode' }) }, 15000, 0);
                vscode.window.showInformationMessage(`✅ Workflow started: ${JSON.stringify(res).slice(0, 200)}`);
            }
            catch (e) {
                vscode.window.showErrorMessage(`❌ Start workflow failed: ${e}`);
            }
        }))
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
// Planner→Coder simple loop
function plannerCoderCommand() {
    return __awaiter(this, void 0, void 0, function* () {
        const goal = yield vscode.window.showInputBox({ prompt: '📝 Describe your goal/task to plan and implement' });
        if (!goal)
            return;
        try {
            const context = yield aiAssistant.getWorkspaceContext();
            const planPrompt = `You are a Planner agent. Break this goal into 3-7 actionable steps with brief descriptions and expected outputs. Respond as a numbered list only.\n\nGoal: ${goal}`;
            const plan = yield aiAssistant.interactWithAI(planPrompt, context);
            const panel = vscode.window.createWebviewPanel('aiPlan', 'Plan', vscode.ViewColumn.Beside, {});
            panel.webview.html = `<html><body><h2>Plan</h2><pre>${plan.content}</pre></body></html>`;
            const proceed = yield vscode.window.showQuickPick(['Proceed to Coder', 'Cancel'], { placeHolder: 'Execute the plan?' });
            if (proceed !== 'Proceed to Coder')
                return;
            const coderPrompt = `You are a Coder agent. Implement the plan below step by step. For file changes, output code fence blocks and explicit file ops as \`\`\`file:path\n...\`\`\`. Plan:\n${plan.content}`;
            const result = yield aiAssistant.interactWithAI(coderPrompt, context);
            // Apply any file operations
            if (result.files) {
                for (const f of result.files) {
                    if (f.operation === 'delete')
                        yield aiAssistant.deleteFile(f.path);
                    else
                        yield aiAssistant.writeFile(f.path, f.content);
                }
            }
            // Show result
            const resultPanel = vscode.window.createWebviewPanel('aiResult', 'Coder Result', vscode.ViewColumn.Beside, {});
            resultPanel.webview.html = `<html><body><h2>Coder Output</h2><pre>${result.content}</pre></body></html>`;
        }
        catch (e) {
            vscode.window.showErrorMessage(`❌ Planner→Coder failed: ${e}`);
        }
    });
}
// Deactivation
function deactivate() { }
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map