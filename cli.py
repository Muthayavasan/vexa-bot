"""
cli.py - Terminal Command-Line Interface for the AI Chatbot
Run with:
    python cli.py
"""

import sys
import os

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from bot_core import ChatbotEngine, load_env_file

load_env_file()

def print_banner():
    banner = r"""
============================================================
              ✨  PYTHON AI CHATBOT (CLI)  ✨
============================================================
Commands:
  /help       - Display available commands
  /clear      - Reset current conversation history
  /history    - Show conversation history length
  /provider   - Change AI provider (gemini, openai, anthropic, offline)
  /exit       - Quit the chatbot
============================================================
"""
    print(banner)

def main():
    print_banner()

    provider = "offline"
    if os.environ.get("GEMINI_API_KEY"):
        provider = "gemini"
    elif os.environ.get("OPENAI_API_KEY"):
        provider = "openai"
    elif os.environ.get("ANTHROPIC_API_KEY"):
        provider = "anthropic"

    bot = ChatbotEngine(provider=provider)
    print(f"[*] Initialized with provider: [{bot.provider.upper()}] (Model: {bot.model_name})")
    if bot.provider == "offline":
        print("[*] Running in Offline Mode (ready immediately!). Enter an API key or switch /provider to connect live cloud models.")
    print("-" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Command handling
        cmd = user_input.lower()
        if cmd in ("/exit", "/quit"):
            print("Goodbye!")
            break
        elif cmd == "/clear":
            bot.clear_history()
            print("[*] Conversation cleared.")
            continue
        elif cmd == "/history":
            print(f"[*] Total messages in history: {len(bot.history)}")
            continue
        elif cmd == "/help":
            print_banner()
            continue
        elif cmd.startswith("/provider"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                new_prov = parts[1].strip().lower()
                bot.provider = new_prov
                bot.model_name = bot._get_default_model(new_prov)
                bot.api_key = bot._get_default_api_key(new_prov)
                print(f"[*] Switched provider to: {new_prov} (Model: {bot.model_name})")
            else:
                print(f"[*] Current provider: {bot.provider}. Usage: /provider <anthropic|openai|offline>")
            continue

        # Stream response
        print("AI: ", end="", flush=True)
        for chunk in bot.chat_stream(user_input):
            print(chunk, end="", flush=True)
        print()

if __name__ == "__main__":
    main()
