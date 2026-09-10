# ✨ VEXA AI — Python AI Chatbot

A complete, production-grade AI Chatbot application built **100% in Python** using **Streamlit**, with native support for the **Anthropic Claude API** and **OpenAI API**.

Designed for **Aether Dynamics**, featuring a dark-themed UI with purple-to-blue gradients, rounded chat bubbles, avatars, multi-session management, animated typing indicators, and multi-turn context retention.

---

## 🚀 Highlights & Features

- **🐍 100% Pure Python**: Powered by Streamlit — no React, Node.js, or separate JavaScript frontend required.
- **🧠 Live LLM Intelligence**:
  - **Anthropic Claude**: `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`, `claude-3-opus-20240229`
  - **OpenAI GPT**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`
  - Real-time token streaming via Python generators.
- **💬 Multi-Session Chat Management**:
  - Prominent **➕ New Chat** button in the sidebar.
  - Switch seamlessly between conversation sessions.
  - Automatic session naming based on initial user prompts, with inline renaming and deletion.
- **🎨 Dark Theme with Purple-to-Blue Gradients**:
  - Elegant deep space palette (`#0B0F19`) with `#7C3AED` to `#2563EB` gradient accents.
  - Smooth rounded chat bubbles with custom user and bot avatars.
- **⏳ Animated Typing Indicator**:
  - Real-time CSS keyframe 3-dot pulsing animation while awaiting API response streaming.
- **🔄 Multi-Turn Context Retention**:
  - Preserves full conversation history within each session and feeds historical turns to the LLM.
- **🛡️ Robust Error Handling**:
  - Missing API key detection with direct links to obtain keys.
  - Network and API rate limit protection.
  - Empty or whitespace input prevention.
- **🎭 Personas & Creativity Slider**:
  - Switch between *Helpful Assistant*, *Senior Python Engineer*, *Creative Writer*, *Concise Tech Tutor*, or *Custom Persona*.
  - Temperature slider (`0.0` - `1.0`) to fine-tune response creativity.
- **💾 Export Chats**:
  - Download any session history as formatted Markdown (`.md`).

---

## 📋 Prerequisites

- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- An **Anthropic Claude API Key** (from [Anthropic Console](https://console.anthropic.com/)) OR an **OpenAI API Key** (from [OpenAI Platform](https://platform.openai.com/api-keys))

---

## ⚡ Quickstart & Installation

### 1. Clone or Open the Project
```bash
cd d:\ChatBot
```

### 2. (Optional) Create and Activate a Virtual Environment
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure API Keys
Copy the `.env.example` file to `.env`:
```powershell
copy .env.example .env
```
Open `.env` and add your API keys:
```env
# Anthropic Claude API Key (Recommended)
ANTHROPIC_API_KEY=sk-ant-api03-...

# OpenAI API Key
OPENAI_API_KEY=sk-...

# Company & Bot Branding
COMPANY_NAME=Aether Dynamics
BOT_NAME=Nova AI
```

*(Note: You can also enter or paste your API keys directly into the sidebar in the Web UI!)*

### 5. Launch the Application
Run the Streamlit app:
```powershell
streamlit run app.py
```
Streamlit will launch local server at: **`http://localhost:8501`**

---

## 🖥️ User Interface Overview

| Component | Description |
|---|---|
| **Header Bar** | Shows active chat title, company name, active model tag, and live provider badge |
| **Sidebar (Top)** | Brand logo, **➕ New Chat** button, and list of saved sessions |
| **Sidebar (Middle)** | Provider picker (Anthropic vs OpenAI vs Offline), Model dropdown, and API key input |
| **Sidebar (Bottom)** | Persona selection, Temperature slider, Session rename tool, and Export button |
| **Chat Stream** | Styled user/bot chat bubbles, avatar icons, and animated 3-dot typing indicator |
| **Chat Input** | Bottom input box for prompts, questions, and code |

---

## ⚙️ Project File Structure

```
d:\ChatBot\
├── app.py             # Streamlit application with custom styling & session state
├── bot_core.py        # Core ChatbotEngine (Anthropic & OpenAI streaming, memory)
├── test_bot.py        # Unit test suite verifying engine logic & error handling
├── cli.py             # Terminal-based chat interface
├── requirements.txt   # Dependencies (streamlit, anthropic, openai, python-dotenv)
├── .env.example       # Template for API keys and branding
└── README.md          # Project documentation and guide
```

---

## 🧪 Running Unit Tests

Run the automated test suite to verify history management, model defaults, and error handlers:
```powershell
python test_bot.py
```

---

## 🏷️ Customizing Branding

To rebrand the chatbot for your organization:
1. Open `.env` (or set environment variables):
   ```env
   COMPANY_NAME="Your Company Name"
   BOT_NAME="Your Bot Name"
   ```
2. Restart or refresh the Streamlit app. The header, sidebar, and bot messages will update automatically.
