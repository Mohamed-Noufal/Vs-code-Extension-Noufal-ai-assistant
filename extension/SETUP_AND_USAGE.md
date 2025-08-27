# Noufal AI Assistant (v3.0.0) — Setup & Usage

This guide shows how to install the VSIX, configure models, and use the extension features.

## 1) Requirements
- VS Code 1.74+
- Optional (local models): Ollama installed and running ("ollama serve")
- Optional (cloud): OpenAI/Google API keys

## 2) Install the VSIX
- If you already have the package file:
  - VS Code → Extensions → … → Install from VSIX… → select `noufal-ai-assistant-3.0.0.vsix`
  - OR Terminal:
    ```powershell
    code --install-extension "C:\\path\\to\\noufal-ai-assistant-3.0.0.vsix" --force
    ```
- To build it yourself:
  ```powershell
  cd extension
  npm install
  npm run compile
  npx @vscode/vsce package --no-dependencies
  code --install-extension .\\noufal-ai-assistant-3.0.0.vsix --force
  ```

## 3) Configure
Open VS Code Settings → search "Noufal AI Assistant". Common options:
```json
{
  "aiAssistant.backendUrl": "http://127.0.0.1:8001",
  "aiAssistant.useOpenAI": false,
  "aiAssistant.useGoogleAI": false,
  "aiAssistant.ollamaModel": "Mistral",
  "aiAssistant.memory.enabled": true
}
```
Tip: In the chat UI, you can choose provider (Ollama/OpenAI/Google) and set the model field directly.

## API Keys
If you want to use OpenAI or Google instead of local Ollama, set your keys in Settings or via the command palette.

- Command Palette → "Noufal AI: Configure API Keys"
- Or add to your `settings.json`:

```json
{
  "aiAssistant.openaiApiKey": "sk-...",
  "aiAssistant.googleApiKey": "YOUR_GOOGLE_API_KEY",
  "aiAssistant.useOpenAI": true,   // or set useGoogleAI: true
  "aiAssistant.useGoogleAI": false
}
```

## 4) Use
- Command Palette (Ctrl+Shift+P), run:
  - Noufal AI: Open Chat (Ctrl+Alt+C)
  - Noufal AI: Generate Code (Ctrl+Alt+A)
  - Noufal AI: Explain Code (Ctrl+Alt+E)
  - Noufal AI: Configure API Keys
  - Noufal AI: File Operations
  - Noufal AI: Plan Task (Planner→Coder)
  - Noufal AI: Check Backend Health
  - Noufal AI: Start Backend Workflow

## 5) Backend (optional)
Only needed for multi‑agent workflows. Start locally:
```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```
Then set `aiAssistant.backendUrl` to `http://127.0.0.1:8001` and use the health/workflow commands.

## 6) Notes
- Ollama default model remains "Mistral" per your setup.
- Dry‑run preview shows file/command changes before applying them.
- CSP hardened; no external CDNs used in chat webview.

## 7) Verify install
```powershell
code --list-extensions --show-versions | Select-String noufal
```
If you see `noufal-ai-assistant@3.0.0`, the extension is installed.
