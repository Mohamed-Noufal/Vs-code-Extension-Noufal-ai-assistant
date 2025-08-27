# 🤖 Noufal AI Assistant - VS Code Extension (v3.0.0)

A powerful AI coding assistant like GitHub Copilot with file operations, terminal commands, and multi-model support for full-stack development.

## 🚀 Quick Install (VSIX)

1. Build or download `noufal-ai-assistant-3.0.0.vsix`
2. VS Code → Extensions → … (kebab) → Install from VSIX → select the `.vsix`
3. Run: Command Palette → "Noufal AI: Open Chat"

## 📦 Build v3.0.0 VSIX

```powershell
cd extension
npm install
npm run compile
npx @vscode/vsce package --no-dependencies
# Produces noufal-ai-assistant-3.0.0.vsix
code --install-extension .\noufal-ai-assistant-3.0.0.vsix --force
```

## ✨ What’s New (v3.0.0)

- Streaming responses with typing indicator and progress bar
- Modern chat UI with built-in syntax highlighting (no CDN; CSP-hardened)
- Attach files to include context; sidebar attachment management
- Message actions: Copy, Regenerate, Edit & Resend, Hide
- Tool bridge: Read File, Write File (with overwrite confirm), Run CLI (with confirmation)
- Dry-run preview before applying AI file/command operations
- Backend integration commands: Check Health, Start Workflow (configurable backendUrl)
- Resilient network: timeouts, retries with backoff, HTTP keep-alive pooling
- Safer file ops: path validation, workspace boundary checks, progress UI

## 🧠 Configure

- Settings → search "Noufal AI Assistant"
- Or Command Palette → "Noufal AI: Configure API Keys"

Key settings (Workspace or User):

```json
{
  "aiAssistant.backendUrl": "http://127.0.0.1:8001", // optional: backend API
  "aiAssistant.useOpenAI": false,
  "aiAssistant.useGoogleAI": false,
  "aiAssistant.ollamaModel": "Mistral", // your Ollama model name
  "aiAssistant.memory.enabled": true
}
```

## ⌨️ Commands and Shortcuts

- Noufal AI: Start Assistant
- Noufal AI: Open Chat (Ctrl+Alt+C)
- Noufal AI: Generate Code (Ctrl+Alt+A)
- Noufal AI: Explain Code (Ctrl+Alt+E)
- Noufal AI: Configure API Keys
- Noufal AI: File Operations
- Noufal AI: Check Backend Health
- Noufal AI: Start Backend Workflow
- Noufal AI: Plan Task (Planner→Coder)

## 🧪 Local Dev

```powershell
cd extension
npm install
npm run compile
npx @vscode/vsce package --no-dependencies
```
Install the generated `.vsix` via VS Code Extensions panel.

## 🐛 Troubleshooting

- If using Ollama locally, ensure it’s running: `ollama serve`
- To use backend features, run FastAPI: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8001`
- Check Output → "Noufal AI Assistant" for logs
- If packaging fails with invalid relative path, ensure `.vscodeignore` exists with `../.vscode/**` excluded

