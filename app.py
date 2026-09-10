"""
app.py - Production AI Chatbot Application
Built using Streamlit, Google Gemini API, and Groq API.

Features:
- Pure Python implementation (No React / separate JS frontend required)
- Multi-session management with "New Chat", session switching, renaming, and deleting
- Google Gemini & Groq general-purpose Q&A streaming engines
- Dark-themed UI with purple-to-blue gradient accents (#7C3AED -> #2563EB)
- Rounded chat bubbles with custom user and bot avatars
- Animated 3-dot pulsing typing indicator while awaiting responses
- Context memory preservation across conversation turns within sessions
- Graceful error handling for missing keys, network issues, and empty input
"""

import os
import uuid
from datetime import datetime

import streamlit as st
from bot_core import ChatbotEngine, load_env_file

# ==============================================================================
# 1. Branding & Configuration Defaults
# ==============================================================================
load_env_file()

DEFAULT_COMPANY = os.environ.get("COMPANY_NAME", "Aether Dynamics")
DEFAULT_BOT = os.environ.get("BOT_NAME", "Nova AI")

# Page configuration
st.set_page_config(
    page_title=f"{DEFAULT_BOT} • {DEFAULT_COMPANY}",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# 2. Custom CSS: Dark Theme, Purple-to-Blue Gradients, Rounded Bubbles, Typing Indicator
# ==============================================================================
st.markdown(
    """
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Overall App Dark Theme Background */
    .stApp {
        background-color: #0B0F19;
        color: #F1F5F9;
    }

    /* Top Header Bar Styling */
    .main-header {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.12) 0%, rgba(37, 99, 235, 0.12) 100%);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        backdrop-filter: blur(8px);
    }
    .brand-title {
        font-size: 1.6rem;
        font-weight: 700;
        background: linear-gradient(135deg, #A78BFA 0%, #60A5FA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-subtitle {
        color: #94A3B8;
        font-size: 0.88rem;
        margin-top: 4px;
    }
    .badge-status {
        background: linear-gradient(135deg, #7C3AED 0%, #2563EB 100%);
        color: white;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 10px rgba(124, 58, 237, 0.3);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0D111D;
        border-right: 1px solid rgba(30, 41, 59, 0.8);
    }
    [data-testid="stSidebar"] .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    /* New Chat Button - Vibrant Purple-to-Blue Gradient */
    .new-chat-btn button {
        background: linear-gradient(135deg, #7C3AED 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 18px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35) !important;
        width: 100% !important;
    }
    .new-chat-btn button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5) !important;
    }

    /* Chat Session List Item */
    .session-item {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(51, 65, 85, 0.4);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .session-item:hover {
        background: rgba(51, 65, 85, 0.5);
        border-color: rgba(139, 92, 246, 0.4);
    }
    .session-active {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.25) 0%, rgba(37, 99, 235, 0.25) 100%) !important;
        border: 1px solid #8B5CF6 !important;
        box-shadow: 0 0 12px rgba(139, 92, 246, 0.2);
    }

    /* Chat Bubbles Styling */
    [data-testid="stChatMessage"] {
        border-radius: 18px !important;
        padding: 14px 18px !important;
        margin-bottom: 14px !important;
        border: 1px solid rgba(51, 65, 85, 0.3) !important;
        transition: all 0.2s ease;
    }

    /* User Chat Bubble: Purple Accent */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
    [data-testid="stChatMessage"]:has([aria-label="chat message user"]) {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.14) 0%, rgba(37, 99, 235, 0.14) 100%) !important;
        border: 1px solid rgba(139, 92, 246, 0.35) !important;
        border-bottom-right-radius: 4px !important;
    }

    /* Assistant Chat Bubble: Dark Card with Soft Slate Border */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    [data-testid="stChatMessage"]:has([aria-label="chat message assistant"]) {
        background: rgba(19, 27, 46, 0.75) !important;
        border: 1px solid rgba(51, 65, 85, 0.5) !important;
        border-bottom-left-radius: 4px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }

    /* Code Block Dark Accents */
    pre {
        background-color: #0A0D14 !important;
        border: 1px solid rgba(51, 65, 85, 0.6) !important;
        border-radius: 10px !important;
    }

    /* Animated Typing Indicator */
    .typing-indicator-box {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(19, 27, 46, 0.85);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 16px;
        padding: 10px 18px;
        margin: 8px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
    }
    .typing-dots {
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .typing-dot {
        width: 8px;
        height: 8px;
        background: linear-gradient(135deg, #A78BFA 0%, #38BDF8 100%);
        border-radius: 50%;
        animation: typingPulse 1.4s infinite ease-in-out both;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }

    @keyframes typingPulse {
        0%, 80%, 100% {
            transform: scale(0.6);
            opacity: 0.35;
        }
        40% {
            transform: scale(1.15);
            opacity: 1;
        }
    }
    .typing-label {
        font-size: 0.86rem;
        color: #94A3B8;
        font-weight: 500;
    }

    /* Welcome Banner */
    .welcome-card {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.08) 0%, rgba(37, 99, 235, 0.08) 100%);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 16px;
        padding: 32px 28px;
        text-align: center;
        margin: 40px auto 20px auto;
        max-width: 680px;
    }
    .welcome-title {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #C4B5FD 0%, #93C5FD 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .welcome-desc {
        color: #94A3B8;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 24px;
    }
    .prompt-chip-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 12px;
        text-align: left;
    }
    .prompt-chip {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(51, 65, 85, 0.5);
        border-radius: 10px;
        padding: 12px 16px;
        color: #CBD5E1;
        font-size: 0.86rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .prompt-chip:hover {
        background: rgba(124, 58, 237, 0.15);
        border-color: rgba(139, 92, 246, 0.5);
        color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 3. Avatar Definitions (Custom SVG / Emoji Icons)
# ==============================================================================
USER_AVATAR = "🧑‍💻"
BOT_AVATAR = "✨"

# ==============================================================================
# 4. Multi-Session State Initialization
# ==============================================================================
def create_new_session(title: str = "New Conversation") -> str:
    """Creates a new chat session and returns its unique ID."""
    session_id = str(uuid.uuid4())[:8]
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    
    st.session_state.sessions[session_id] = {
        "id": session_id,
        "title": title,
        "created_at": datetime.now().strftime("%b %d, %H:%M"),
        "messages": [],
    }
    return session_id


if "sessions" not in st.session_state or not st.session_state.sessions:
    initial_id = create_new_session("Welcome Chat")
    st.session_state.current_session_id = initial_id

if "current_session_id" not in st.session_state or st.session_state.current_session_id not in st.session_state.sessions:
    st.session_state.current_session_id = next(iter(st.session_state.sessions.keys()))

active_session = st.session_state.sessions[st.session_state.current_session_id]

# ==============================================================================
# 5. Sidebar: Branding, New Chat, Session List, AI Configuration
# ==============================================================================
with st.sidebar:
    # Company & Bot Branding
    st.markdown(
        f"""
        <div style="padding: 6px 0 16px 0; border-bottom: 1px solid rgba(51, 65, 85, 0.4); margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="background: linear-gradient(135deg, #7C3AED 0%, #2563EB 100%); width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);">
                    ✨
                </div>
                <div>
                    <div style="font-weight: 700; font-size: 1.1rem; color: #FFFFFF;">{DEFAULT_BOT}</div>
                    <div style="font-size: 0.78rem; color: #94A3B8;">{DEFAULT_COMPANY}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # "+ New Chat" Button
    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("➕ New Chat", use_container_width=True):
        new_id = create_new_session(f"Chat #{len(st.session_state.sessions) + 1}")
        st.session_state.current_session_id = new_id
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Conversations Section
    st.markdown(
        "<div style='font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #64748B; margin-bottom: 8px;'>Chat Sessions</div>",
        unsafe_allow_html=True,
    )

    # Session items listing
    session_keys = list(st.session_state.sessions.keys())
    for s_id in reversed(session_keys):
        s_data = st.session_state.sessions[s_id]
        is_active = (s_id == st.session_state.current_session_id)
        msg_count = len(s_data["messages"])
        
        # Display session row with selection and delete
        col_session, col_del = st.columns([0.84, 0.16])
        with col_session:
            button_label = f"{'💬 ' if not is_active else '🟣 '}{s_data['title'][:22]}"
            if st.button(
                button_label,
                key=f"sess_btn_{s_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.current_session_id = s_id
                st.rerun()
        
        with col_del:
            if len(st.session_state.sessions) > 1:
                if st.button("✕", key=f"del_btn_{s_id}", help="Delete chat session", use_container_width=True):
                    del st.session_state.sessions[s_id]
                    if st.session_state.current_session_id == s_id:
                        st.session_state.current_session_id = next(iter(st.session_state.sessions.keys()))
                    st.rerun()

    st.divider()

    # AI Engine Configuration
    st.markdown(
        "<div style='font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #64748B; margin-bottom: 8px;'>AI Provider & Model</div>",
        unsafe_allow_html=True,
    )

    provider_label = st.selectbox(
        "AI Provider",
        options=["Google Gemini (Recommended)", "Groq", "Offline Demo Mode"],
        index=0,
        help="Select the AI platform powering responses. Gemini and Groq support full general-purpose Q&A.",
    )

    provider_key_map = {
        "Google Gemini (Recommended)": "gemini",
        "Groq": "groq",
        "Offline Demo Mode": "offline",
    }
    active_provider = provider_key_map[provider_label]

    # Model Selection
    selected_model = ""

    if active_provider == "gemini":
        selected_model = st.selectbox(
            "Gemini Model",
            options=ChatbotEngine.SUPPORTED_MODELS["gemini"],
            index=0,
            help="Gemini 2.5 Flash offers exceptional reasoning and code accuracy.",
        )

    elif active_provider == "groq":
        selected_model = st.selectbox(
            "Groq Model",
            options=ChatbotEngine.SUPPORTED_MODELS["groq"],
            index=0,
            help="Llama 3.3 70B Versatile delivers high-intelligence performance with fast inference.",
        )

    else:
        st.info("💡 Offline mode enables local testing, math, and code templates with 0 API keys.")
        selected_model = "offline-mode"

    st.divider()

    # Persona / System Instruction
    st.markdown(
        "<div style='font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #64748B; margin-bottom: 8px;'>Persona & Creativity</div>",
        unsafe_allow_html=True,
    )

    persona_choice = st.selectbox(
        "Bot Persona",
        options=list(ChatbotEngine.PERSONAS.keys()) + ["Custom Persona"],
        index=0,
    )

    if persona_choice == "Custom Persona":
        system_instruction = st.text_area(
            "Custom System Prompt",
            value="You are a highly capable AI assistant.",
            height=90,
        )
    else:
        system_instruction = ChatbotEngine.PERSONAS[persona_choice]
        st.caption(f"_{system_instruction[:85]}..._")

    temperature = st.slider(
        "Temperature (Creativity)",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Lower values produce more deterministic responses; higher values increase creativity.",
    )

    st.divider()

    # Session Management Actions: Rename & Export
    with st.expander("⚙️ Session Options"):
        new_title = st.text_input("Rename Current Chat", value=active_session["title"])
        if new_title and new_title != active_session["title"]:
            active_session["title"] = new_title

        # Export Chat
        chat_markdown = f"# {active_session['title']}\n"
        chat_markdown += f"*Created: {active_session['created_at']} | Provider: {active_provider} | Model: {selected_model}*\n\n---\n\n"
        for m in active_session["messages"]:
            sender = DEFAULT_BOT if m["role"] == "assistant" else "User"
            chat_markdown += f"### {sender}\n\n{m['content']}\n\n"

        st.download_button(
            label="💾 Export Conversation (.md)",
            data=chat_markdown,
            file_name=f"{active_session['title'].replace(' ', '_').lower()}.md",
            mime="text/markdown",
            use_container_width=True,
            disabled=len(active_session["messages"]) == 0,
        )

        if st.button("🗑️ Clear Current Messages", use_container_width=True):
            active_session["messages"] = []
            st.rerun()

# ==============================================================================
# 6. Main Chat Area: Header & Messages
# ==============================================================================
# Top Header Banner
header_col1, header_col2 = st.columns([0.7, 0.3])
with header_col1:
    st.markdown(
        f"""
        <div class="main-header">
            <div>
                <h1 class="brand-title">
                    <span>✨</span> {active_session['title']}
                </h1>
                <div class="brand-subtitle">
                    {DEFAULT_COMPANY} • Powered by <strong>{selected_model}</strong> ({active_provider.capitalize()})
                </div>
            </div>
            <div>
                <span class="badge-status">{active_provider}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_col2:
    # Key status warning badge if key missing
    if active_provider in ("gemini", "groq"):
        env_key = os.environ.get("GEMINI_API_KEY" if active_provider == "gemini" else "GROQ_API_KEY", "")
        if not env_key:
            st.warning(
                f"⚠️ Missing {active_provider.capitalize()} API key in .env file!",
                icon="🔑",
            )

# Welcome Screen for Empty Conversation
if len(active_session["messages"]) == 0:
    st.markdown(
        f"""
        <div class="welcome-card">
            <div class="welcome-title">How can {DEFAULT_BOT} help you today?</div>
            <div class="welcome-desc">
                Equipped with multi-turn context retention, streaming responses, and advanced reasoning.
                Ask any question, brainstorm creative ideas, or request code.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick Starter Chips
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💡 Explain quantum computing with simple analogies", use_container_width=True):
            st.session_state["preset_prompt"] = "Explain quantum computing using simple real-world analogies."
            st.rerun()
        if st.button("🐍 Write a Python async web scraper with error handling", use_container_width=True):
            st.session_state["preset_prompt"] = "Write a production-ready Python async web scraper using httpx and asyncio with retry logic."
            st.rerun()
    with col2:
        if st.button("🚀 Draft a product launch strategy for a developer tool", use_container_width=True):
            st.session_state["preset_prompt"] = "Draft a comprehensive go-to-market product launch plan for a new developer SaaS tool."
            st.rerun()
        if st.button("🔍 Explain the difference between REST, GraphQL, and gRPC", use_container_width=True):
            st.session_state["preset_prompt"] = "Compare REST, GraphQL, and gRPC in terms of performance, caching, and developer experience."
            st.rerun()

# Display Conversation History
for msg in active_session["messages"]:
    role = msg["role"]
    avatar = USER_AVATAR if role == "user" else BOT_AVATAR
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# ==============================================================================
# 7. User Input & Streaming Handler with Typing Indicator
# ==============================================================================
# Check for starter chip preset
starter_prompt = st.session_state.pop("preset_prompt", None)
user_prompt = st.chat_input("Ask any question, explore ideas, or paste code...")

# Use whichever input was triggered
prompt_to_send = starter_prompt or user_prompt

if prompt_to_send:
    clean_prompt = prompt_to_send.strip()
    if clean_prompt:
        # Auto-update conversation title from the first question
        if len(active_session["messages"]) == 0:
            truncated_title = clean_prompt[:30].strip() + ("..." if len(clean_prompt) > 30 else "")
            active_session["title"] = truncated_title

        # Append user message to session state
        active_session["messages"].append({"role": "user", "content": clean_prompt})

        # Render user message
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(clean_prompt)

        # Prepare Chatbot Engine
        engine = ChatbotEngine(
            provider=active_provider,
            model_name=selected_model,
            system_prompt=system_instruction,
            temperature=temperature,
        )
        # Sync conversation memory (excluding the user prompt we just appended, chat_stream handles it)
        engine.set_history(active_session["messages"][:-1])

        # Render Assistant Response with animated typing indicator and token streaming
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            response_placeholder = st.empty()

            # Render Animated 3-dot Typing Indicator while awaiting the first token
            typing_indicator_html = f"""
            <div class="typing-indicator-box">
                <div class="typing-dots">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
                <span class="typing-label">{DEFAULT_BOT} is thinking...</span>
            </div>
            """
            response_placeholder.markdown(typing_indicator_html, unsafe_allow_html=True)

            # Stream generator
            accumulated_text = ""
            first_chunk_received = False

            try:
                for chunk in engine.chat_stream(clean_prompt):
                    if not first_chunk_received:
                        first_chunk_received = True
                        # Clear typing indicator on first token arrival
                        response_placeholder.empty()

                    accumulated_text += chunk
                    # Render with subtle streaming cursor
                    response_placeholder.markdown(accumulated_text + " ▌")

                # Final render without cursor
                response_placeholder.markdown(accumulated_text)

                # Persist assistant response to session history
                active_session["messages"].append({"role": "assistant", "content": accumulated_text})

            except Exception as e:
                response_placeholder.error(f"⚠️ Error while generating response: {str(e)}")
