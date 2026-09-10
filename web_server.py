"""
web_server.py - Zero-Dependency Web UI Server for AI Chatbot
Runs with standard Python without installing ANY third-party packages!
Usage:
    python web_server.py
Then open http://localhost:8000 in your browser.
"""

import http.server
import socketserver
import json
import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from bot_core import ChatbotEngine

PORT = 8000
bot_instance = ChatbotEngine(provider="offline")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Python AI Chatbot</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --bubble-ai: #334155;
      --bubble-user: #2563eb;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
      --accent: #38bdf8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background-color: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }
    
    /* Sidebar */
    .sidebar { width: 320px; background: var(--card-bg); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: 20px; gap: 16px; overflow-y: auto; }
    .sidebar h2 { font-size: 1.25rem; font-weight: 700; color: var(--accent); display: flex; align-items: center; gap: 8px; }
    .sidebar label { font-size: 0.85rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-top: 8px; display: block; }
    .sidebar select, .sidebar input, .sidebar textarea {
      width: 100%; background: #0f172a; border: 1px solid var(--border); color: #fff; padding: 10px; border-radius: 8px; font-size: 0.9rem; margin-top: 4px;
    }
    .btn { background: var(--accent); color: #0f172a; font-weight: 600; border: none; padding: 10px 14px; border-radius: 8px; cursor: pointer; transition: 0.2s; width: 100%; margin-top: 6px; }
    .btn:hover { filter: brightness(1.1); }
    .btn-secondary { background: #334155; color: #fff; }
    .btn-secondary:hover { background: #475569; }

    /* Chat Area */
    .main-chat { flex: 1; display: flex; flex-direction: column; height: 100vh; }
    .chat-header { padding: 16px 24px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.5); backdrop-filter: blur(8px); }
    .chat-header h1 { font-size: 1.2rem; font-weight: 600; }
    .status-badge { background: #166534; color: #4ade80; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
    
    .messages-container { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }
    .msg { display: flex; gap: 12px; max-width: 80%; line-height: 1.5; font-size: 0.95rem; }
    .msg.user { align-self: flex-end; flex-direction: row-reverse; }
    .msg.assistant { align-self: flex-start; }
    
    .avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0; background: #334155; }
    .msg.user .avatar { background: #1d4ed8; }
    
    .bubble { padding: 12px 16px; border-radius: 14px; background: var(--bubble-ai); white-space: pre-wrap; word-break: break-word; }
    .msg.user .bubble { background: var(--bubble-user); border-bottom-right-radius: 4px; }
    .msg.assistant .bubble { border-bottom-left-radius: 4px; }
    
    pre { background: #0b0f19; padding: 10px; border-radius: 6px; overflow-x: auto; margin: 8px 0; font-family: monospace; font-size: 0.85rem; border: 1px solid #1e293b; }
    code { font-family: monospace; background: rgba(255,255,255,0.1); padding: 2px 4px; border-radius: 4px; }

    /* Input Area */
    .input-bar { padding: 16px 24px; border-top: 1px solid var(--border); display: flex; gap: 10px; background: var(--card-bg); }
    .input-bar input { flex: 1; background: #0f172a; border: 1px solid var(--border); color: #fff; padding: 14px 18px; border-radius: 10px; font-size: 1rem; outline: none; }
    .input-bar input:focus { border-color: var(--accent); }
    .send-btn { width: 100px; }
  </style>
</head>
<body>
  <div class="sidebar">
    <h2>🤖 Bot Settings</h2>
    
    <label>Provider</label>
    <select id="providerSelect" onchange="updateProviderUI()">
      <option value="offline">Offline Mode (No Key Needed)</option>
      <option value="gemini">Google Gemini</option>
      <option value="openai">OpenAI / Compatible</option>
    </select>

    <div id="apiKeyGroup" style="display: none;">
      <label id="apiKeyLabel">API Key</label>
      <input type="password" id="apiKeyInput" placeholder="Enter API Key" />
    </div>

    <div id="modelGroup" style="display: none;">
      <label>Model Name</label>
      <input type="text" id="modelInput" placeholder="Model name" />
    </div>

    <label>Persona / System Role</label>
    <select id="personaSelect">
      <option value="Helpful Assistant">Helpful Assistant</option>
      <option value="Python Coding Expert">Python Coding Expert</option>
      <option value="Creative Writer">Creative Writer</option>
      <option value="Concise Tech Tutor">Concise Tech Tutor</option>
    </select>

    <button class="btn" onclick="applySettings()">Apply Settings</button>
    <button class="btn btn-secondary" onclick="clearConversation()">Clear History</button>
  </div>

  <div class="main-chat">
    <div class="chat-header">
      <h1 id="headerTitle">Python AI Chatbot</h1>
      <span class="status-badge" id="statusBadge">Active</span>
    </div>

    <div class="messages-container" id="chatContainer">
      <div class="msg assistant">
        <div class="avatar">🤖</div>
        <div class="bubble">Hello! 👋 I'm your Python AI Chatbot.<br><br>I'm currently running in <b>Offline Mode</b> with zero external dependencies or API keys required! Ask me questions, request math calculations, or discuss Python programming.</div>
      </div>
    </div>

    <div class="input-bar">
      <input type="text" id="userInput" placeholder="Type a message and press Enter..." onkeypress="handleKey(event)" />
      <button class="btn send-btn" id="sendBtn" onclick="sendMessage()">Send</button>
    </div>
  </div>

  <script>
    function updateProviderUI() {
      const p = document.getElementById("providerSelect").value;
      const keyGroup = document.getElementById("apiKeyGroup");
      const modelGroup = document.getElementById("modelGroup");
      const modelInput = document.getElementById("modelInput");

      if (p === "gemini") {
        keyGroup.style.display = "block";
        modelGroup.style.display = "block";
        modelInput.value = "gemini-2.5-flash";
      } else if (p === "openai") {
        keyGroup.style.display = "block";
        modelGroup.style.display = "block";
        modelInput.value = "gpt-4o-mini";
      } else {
        keyGroup.style.display = "none";
        modelGroup.style.display = "none";
      }
    }

    async function applySettings() {
      const payload = {
        provider: document.getElementById("providerSelect").value,
        api_key: document.getElementById("apiKeyInput").value,
        model_name: document.getElementById("modelInput").value,
        persona: document.getElementById("personaSelect").value,
      };
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      alert('Settings updated successfully!');
    }

    async function clearConversation() {
      await fetch('/api/clear', { method: 'POST' });
      document.getElementById("chatContainer").innerHTML = `
        <div class="msg assistant">
          <div class="avatar">🤖</div>
          <div class="bubble">Conversation cleared. How can I help you?</div>
        </div>
      `;
    }

    function appendMessage(role, text) {
      const container = document.getElementById("chatContainer");
      const div = document.createElement("div");
      div.className = `msg ${role}`;
      div.innerHTML = `
        <div class="avatar">${role === 'user' ? '🧑' : '🤖'}</div>
        <div class="bubble">${text.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
      `;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    }

    function handleKey(e) {
      if (e.key === "Enter") sendMessage();
    }

    async function sendMessage() {
      const input = document.getElementById("userInput");
      const text = input.value.trim();
      if (!text) return;
      
      input.value = "";
      appendMessage("user", text);

      const sendBtn = document.getElementById("sendBtn");
      sendBtn.disabled = true;
      sendBtn.innerText = "...";

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        appendMessage("assistant", data.reply);
      } catch (err) {
        appendMessage("assistant", "[Error communicating with backend: " + err + "]");
      } finally {
        sendBtn.disabled = false;
        sendBtn.innerText = "Send";
      }
    }
  </script>
</body>
</html>
"""

class ChatRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence verbose request logs
        return

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(body) if body else {}

        if self.path == "/api/chat":
            user_msg = data.get("message", "")
            reply = bot_instance.chat(user_msg)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply}).encode("utf-8"))

        elif self.path == "/api/clear":
            bot_instance.clear_history()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))

        elif self.path == "/api/settings":
            provider = data.get("provider", "offline")
            bot_instance.provider = provider
            bot_instance.api_key = data.get("api_key") or bot_instance._get_default_api_key(provider)
            bot_instance.model_name = data.get("model_name") or bot_instance._get_default_model(provider)
            persona = data.get("persona")
            if persona and persona in ChatbotEngine.PERSONAS:
                bot_instance.system_prompt = ChatbotEngine.PERSONAS[persona]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "updated"}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ("", PORT)
    with socketserver.TCPServer(server_address, ChatRequestHandler) as httpd:
        print("============================================================")
        print(f"  🚀 AI Chatbot Web UI running at http://localhost:{PORT}")
        print(f"  👉 Open http://localhost:{PORT} in your browser to chat!")
        print("  Press Ctrl+C in terminal to stop.")
        print("============================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()
