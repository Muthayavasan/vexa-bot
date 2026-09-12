"""
bot_core.py - Core Engine for the AI Chatbot
Supports:
1. Google Gemini API (gemini-2.5-flash, gemini-1.5-pro, etc.)
2. Groq API (llama-3.3-70b-versatile, mixtral-8x7b-32768, etc.)
3. Anthropic (claude-3-5-sonnet, etc.)
4. Built-in Offline Mode (zero-key fallback for local testing & demos)
5. Voice Input (speech_recognition + Google Web Speech API)

Features:
- Standard library urllib fallback: Works out of the box with zero third-party dependencies!
- Native token streaming with Python generators
- Conversation memory & history management
- Custom personas & system prompt handling
- Robust, user-friendly exception handling
- Voice recognition with ambient noise adjustment and full error handling
"""

import os
import sys
import json
import re
import math
import datetime
import urllib.request
import urllib.error
from typing import List, Dict, Generator, Optional, Any, Union

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Gracefully load .env if available
def load_env_file(filepath: str = ".env"):
    """Reads key-value pairs from a local .env file into os.environ."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    if key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass

# Initialize environment variables
load_env_file()

# =============================================================================
# Voice Recognition Module with Comprehensive Debug Logging & Fallbacks
# =============================================================================

def check_voice_dependencies():
    """Checks and prints the installation status of voice-related libraries."""
    print("\n--- Voice Recognition Dependency Check ---")
    
    # 1. speech_recognition
    try:
        import speech_recognition as sr
        print(f"  [OK] speech_recognition (version: {getattr(sr, '__version__', 'installed')})")
    except ImportError:
        print("  [FAIL] speech_recognition is NOT installed.")
        print("         Install with: pip install SpeechRecognition")

    # 2. PyAudio
    try:
        import pyaudio
        print("  [OK] pyaudio (native PortAudio bindings installed)")
    except ImportError:
        print("  [INFO] pyaudio is not installed (optional on Windows if sounddevice is present).")

    # 3. sounddevice & scipy (universal zero-compile fallback)
    try:
        import sounddevice as sd
        import scipy
        import numpy
        print("  [OK] sounddevice + scipy (universal audio capture engine active)")
    except ImportError:
        print("  [WARN] sounddevice or scipy missing. Install with: pip install sounddevice scipy")
    
    print("------------------------------------------\n")


def list_available_microphones() -> List[str]:
    """
    Detects and returns all available audio input devices (microphones).
    Prints a clear diagnostic warning if no microphone is found at the OS level.
    """
    print("[Voice] 🔍 Scanning for available microphones...")
    
    # Try SpeechRecognition's native microphone list (uses PyAudio)
    try:
        import speech_recognition as sr
        mics = sr.Microphone.list_microphone_names()
        if mics:
            print(f"[Voice] ✅ Found {len(mics)} microphone device(s) via PortAudio/PyAudio:")
            for idx, name in enumerate(mics):
                print(f"        [{idx}] {name}")
            return mics
    except Exception:
        pass  # PyAudio not installed; try sounddevice fallback

    # Try sounddevice
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_mics = [d["name"] for d in devices if d.get("max_input_channels", 0) > 0]
        if input_mics:
            print(f"[Voice] ✅ Found {len(input_mics)} audio input device(s) via sounddevice:")
            for idx, name in enumerate(input_mics):
                print(f"        [{idx}] {name}")
            return input_mics
        else:
            print("[Voice] ❌ NO microphones detected at the OS/driver level (empty device list).")
            print("        Please check Windows Settings > Sound > Input or microphone privacy permissions.")
            return []
    except Exception as exc:
        print(f"[Voice] ❌ Could not query audio devices: {exc}")
        return []


def listen_and_transcribe(
    timeout: int = 5,
    phrase_time_limit: int = 15,
    language: str = "en-US",
    device_index: Optional[int] = None,
) -> Optional[str]:
    """
    Captures audio from the microphone and transcribes it using Google Web Speech API.
    
    Features:
    - Explicit BEFORE and AFTER print statements for every step.
    - Strict timeout and phrase_time_limit to prevent silent hangs.
    - Specific exception handling for WaitTimeoutError, UnknownValueError, RequestError, OSError.
    - Automatic fallback between PyAudio and sounddevice.

    Args:
        timeout:           Max seconds to wait before speech begins (prevents indefinite hang).
        phrase_time_limit: Max seconds of speech to record once speaking starts.
        language:          BCP-47 language tag (e.g. 'en-US', 'en-IN', 'hi-IN').
        device_index:      Specific microphone index (or None for system default).

    Returns:
        Transcribed text string on success, or None on failure/timeout.
    """
    try:
        import speech_recognition as sr
    except ImportError:
        print("[Voice] ❌ 'speech_recognition' is not installed. Run: pip install SpeechRecognition")
        return None

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    # Attempt 1: Standard PyAudio microphone capture
    pyaudio_available = False
    try:
        import pyaudio
        pyaudio_available = True
    except ImportError:
        pyaudio_available = False

    if pyaudio_available:
        try:
            print(f"[Voice] 🎙️ Step 1/4: Opening microphone (device_index={device_index})...", flush=True)
            mic_kwargs = {}
            if device_index is not None:
                mic_kwargs["device_index"] = device_index

            with sr.Microphone(**mic_kwargs) as source:
                print("[Voice] 🔇 Step 2/4: Calibrating for ambient noise (1.0s)... Please remain quiet.", flush=True)
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                print(f"[Voice]    → Ambient energy threshold set to: {recognizer.energy_threshold:.1f}", flush=True)

                print(
                    f"[Voice] 👂 Step 3/4: Listening (timeout={timeout}s, max speech={phrase_time_limit}s)... Speak now!",
                    flush=True,
                )
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
                print(f"[Voice] 📦 Step 3/4 complete: Audio captured ({len(audio.get_raw_data())} bytes).", flush=True)

        except sr.WaitTimeoutError:
            print(f"[Voice] ⏱️ Timeout: No speech detected within {timeout} seconds.", flush=True)
            return None
        except OSError as exc:
            print(f"[Voice] ❌ Microphone OS/Hardware error: {exc}", flush=True)
            print("        Make sure your microphone is connected and not locked by another application.")
            return None
        except Exception as exc:
            print(f"[Voice] ❌ Microphone access error: {exc}", flush=True)
            return None
    else:
        # Attempt 2: Universal sounddevice fallback (no PyAudio/C++ compiler needed)
        try:
            import sounddevice as sd
            import numpy as np
            from scipy.io import wavfile
            import io
            import time

            samplerate = 16000
            print(f"[Voice] 🎙️ Step 1/4: Opening microphone via sounddevice (samplerate={samplerate}Hz)...", flush=True)
            
            # Simple voice activity detection using sounddevice
            print("[Voice] 🔇 Step 2/4: Calibrating noise floor (0.6s)...", flush=True)
            calib = sd.rec(int(0.6 * samplerate), samplerate=samplerate, channels=1, dtype="int16")
            sd.wait()
            noise_rms = np.sqrt(np.mean(calib.astype(np.float32) ** 2))
            threshold = max(noise_rms * 1.8, 300.0)
            print(f"[Voice]    → Noise RMS: {noise_rms:.1f}, Speech threshold: {threshold:.1f}", flush=True)

            print(f"[Voice] 👂 Step 3/4: Listening (timeout={timeout}s, max speech={phrase_time_limit}s)... Speak now!", flush=True)
            
            chunk_duration = 0.2
            chunk_samples = int(chunk_duration * samplerate)
            recorded_chunks = []
            
            start_time = time.time()
            speech_started = False
            silence_start = None
            
            with sd.InputStream(samplerate=samplerate, channels=1, dtype="int16") as stream:
                while True:
                    now = time.time()
                    elapsed = now - start_time

                    chunk, _ = stream.read(chunk_samples)
                    chunk_rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                    if not speech_started:
                        if chunk_rms > threshold:
                            speech_started = True
                            recorded_chunks.append(chunk)
                            silence_start = None
                            print("[Voice]    → Speech detected! Recording...", flush=True)
                        elif elapsed > timeout:
                            print(f"[Voice] ⏱️ Timeout: No speech detected within {timeout} seconds.", flush=True)
                            return None
                    else:
                        recorded_chunks.append(chunk)
                        if chunk_rms < threshold:
                            if silence_start is None:
                                silence_start = now
                            elif (now - silence_start) >= 1.2:
                                # 1.2 seconds of silence after speech -> finish
                                break
                        else:
                            silence_start = None

                        if (now - start_time) > (timeout + phrase_time_limit):
                            break

            if not recorded_chunks:
                print(f"[Voice] ⏱️ Timeout: No speech captured.", flush=True)
                return None

            audio_data = np.concatenate(recorded_chunks, axis=0)
            wav_buf = io.BytesIO()
            wavfile.write(wav_buf, samplerate, audio_data)
            wav_buf.seek(0)

            with sr.AudioFile(wav_buf) as source:
                audio = recognizer.record(source)
            print(f"[Voice] 📦 Step 3/4 complete: Audio captured ({len(audio.get_raw_data())} bytes).", flush=True)

        except Exception as exc:
            print(f"[Voice] ❌ Sounddevice audio recording failed: {exc}", flush=True)
            return None

    # Step 4: Transcribe using Google Web Speech API
    try:
        print("[Voice] 🌐 Step 4/4: Sending audio to Google Web Speech API for transcription...", flush=True)
        text = recognizer.recognize_google(audio, language=language)
        print(f"[Voice] ✅ Step 4/4 complete: Transcribed: '{text}'", flush=True)
        return text.strip()

    except sr.UnknownValueError:
        print("[Voice] 🤷 Could not understand the audio (speech was unclear or too quiet).", flush=True)
        return None
    except sr.RequestError as exc:
        print(f"[Voice] 🌐 Google Web Speech API error: {exc}", flush=True)
        print("        Check your internet connection.")
        return None
    except Exception as exc:
        print(f"[Voice] ❌ Unexpected recognition error: {exc}", flush=True)
        return None


def search_web_tavily(query: str) -> str:
    """
    Performs a robust web search using the Tavily API.
    Returns a formatted string of the top results.
    """
    import os
    import json
    import urllib.request
    
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("[Web Search] ⚠️ TAVILY_API_KEY not found in environment. Skipping search.", flush=True)
        return ""
        
    print(f"\n[Web Search] 🔍 Searching Tavily for: '{query}'...", flush=True)
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key.strip(),
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "max_results": 3
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get("results", [])
            
            if not results:
                print("[Web Search] ⚠️ No results found.", flush=True)
                return ""
                
            formatted_results = []
            for r in results:
                title = r.get("title", "")
                content = r.get("content", "")
                formatted_results.append(f"- {title}: {content}")
                
            final_text = "\n".join(formatted_results)
            print(f"[Web Search] ✅ Found {len(results)} live snippets from Tavily.", flush=True)
            return final_text
    except Exception as e:
        print(f"[Web Search] ❌ Failed to fetch Tavily search results: {e}", flush=True)
        return ""


def search_finnhub_quote(symbol: str) -> str:
    """
    Fetches real-time stock quote from Finnhub API.
    Returns a formatted string with the live price.
    """
    import os
    import json
    import urllib.request
    
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        print("[Finnhub] ⚠️ FINNHUB_API_KEY not found in environment. Skipping stock fetch.", flush=True)
        return ""
        
    print(f"\n[Finnhub] 📈 Fetching live stock data for: '{symbol}'...", flush=True)
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key.strip()}"
        req = urllib.request.Request(url, method="GET")
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if "c" not in data or data["c"] == 0:
                print(f"[Finnhub] ⚠️ No live data found for symbol {symbol}.", flush=True)
                return ""
            
            price = data.get("c")
            high = data.get("h")
            low = data.get("l")
            open_price = data.get("o")
            prev_close = data.get("pc")
            
            result_str = (
                f"Symbol: {symbol}\n"
                f"Current Live Price: ${price}\n"
                f"Today's High: ${high}\n"
                f"Today's Low: ${low}\n"
                f"Open: ${open_price}\n"
                f"Previous Close: ${prev_close}"
            )
            print(f"[Finnhub] ✅ Successfully fetched live price for {symbol}: ${price}", flush=True)
            return result_str
    except Exception as e:
        print(f"[Finnhub] ❌ Failed to fetch Finnhub data: {e}", flush=True)
        return ""


class ChatbotEngine:
    """
    Core AI Chatbot engine managing conversation state, system instructions,
    and multi-provider LLM streaming (Gemini, Claude, OpenAI, Offline).
    """

    DEFAULT_SYSTEM_PROMPT = (
        "You are an intelligent, thoughtful, and highly capable AI Assistant. "
        "Provide clear, accurate, and well-structured responses. Use Markdown and formatted "
        "code blocks whenever appropriate."
    )

    PERSONAS = {
        "Helpful Assistant": DEFAULT_SYSTEM_PROMPT,
        "Senior Python Engineer": (
            "You are a Principal Software Engineer and Python specialist. You write clean, "
            "idiomatic, production-grade Python code adhering to PEP 8, accompanied by concise "
            "architectural explanations and unit test recommendations."
        ),
        "Creative Writer": (
            "You are an imaginative, expressive creative writer and storyteller. "
            "Craft vivid scenes, engaging narratives, evocative prose, and memorable characters."
        ),
        "Concise Tech Tutor": (
            "You are a concise, patient technical instructor. Break down complex topics into "
            "clear, beginner-friendly bullet points and concrete everyday analogies."
        ),
        "Executive Analyst": (
            "You are a strategic executive business and technology analyst. Provide crisp, data-driven "
            "summaries, SWOT-style tradeoffs, and actionable high-level recommendations."
        ),
    }

    SUPPORTED_MODELS = {
        "gemini": [
            "gemini-3.6-flash",
            "gemini-3.6-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
        "groq": [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "groq/compound",
            "groq/compound-mini",
            "qwen/qwen3.6-27b",
            "qwen/qwen3.8-27b",
        ],
    }

    def __init__(
        self,
        provider: str = "offline",
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        base_url: Optional[str] = None,
    ):
        self.provider = provider.lower().strip()
        self.api_key = (api_key or self._get_default_api_key(self.provider) or "").strip()
        self.model_name = model_name or self._get_default_model(self.provider)
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.temperature = float(temperature)
        self.base_url = base_url or self._get_default_base_url(self.provider)
        self.history: List[Dict[str, str]] = []

    def _get_default_api_key(self, provider: str) -> Optional[str]:
        """Resolves default API key from environment variables."""
        if provider == "gemini":
            return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        elif provider == "groq":
            return os.environ.get("GROQ_API_KEY")
        return None

    def _get_default_model(self, provider: str) -> str:
        """Returns the recommended default model for the chosen provider."""
        if provider == "gemini":
            return "gemini-3.6-flash"
        elif provider == "groq":
            return "openai/gpt-oss-120b"
        return "offline-mode"

    def _get_default_base_url(self, provider: str) -> str:
        """Returns the default endpoint base URL."""
        if provider == "groq":
            return "https://api.groq.com/openai/v1"
        return ""

    def clear_history(self):
        """Clears the current conversation messages."""
        self.history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Returns a copy of the current message history."""
        return list(self.history)

    def set_history(self, messages: List[Dict[str, str]]):
        """Sets the current message history from an external session."""
        self.history = list(messages)

    def add_user_message(self, content: str, image: Optional[str] = None):
        """Appends a user message to the context history."""
        msg: Dict[str, Any] = {"role": "user", "content": content}
        if image:
            msg["image"] = image
        self.history.append(msg)

    def add_assistant_message(self, content: str):
        """Appends an assistant response to the context history."""
        self.history.append({"role": "assistant", "content": content})

    def chat_stream(self, user_input: str, image: Optional[str] = None) -> Generator[Union[str, dict], None, None]:
        """
        Sends user input (and optional image) to the selected LLM provider and yields response
        text chunks in real time. Automatically updates conversation context upon completion.
        """
        user_input_clean = user_input.strip()
        if not user_input_clean and not image:
            return

        # Record user turn in local history
        self.add_user_message(user_input_clean, image=image)
        accumulated_response = []

        # --- NEW: Check for Web Search & Finnhub Heuristics ---
        search_keywords = ["price", "live", "current", "latest", "today", "stock", "weather", "news"]
        lower_input = user_input_clean.lower()
        search_context = ""
        
        # Finnhub Stock Check
        finnhub_symbol = None
        if "stock" in lower_input or "price" in lower_input:
            stock_match = re.search(r'\b([A-Z]{1,5})\b', user_input_clean)
            if stock_match:
                finnhub_symbol = stock_match.group(1)
            else:
                common_stocks = {"apple": "AAPL", "tesla": "TSLA", "google": "GOOGL", "microsoft": "MSFT", "amazon": "AMZN", "nvidia": "NVDA", "meta": "META"}
                for name, sym in common_stocks.items():
                    if name in lower_input:
                        finnhub_symbol = sym
                        break
        
        if finnhub_symbol:
            finnhub_results = search_finnhub_quote(finnhub_symbol)
            if finnhub_results:
                search_context = f"\n\n[Real-time Finnhub Stock Data]:\n{finnhub_results}\n\nInstructions: Answer the user's question accurately using the live stock data provided above."
                
        # Fallback to Tavily if Finnhub wasn't used or failed
        if not search_context and any(kw in lower_input for kw in search_keywords):
            search_results = search_web_tavily(user_input_clean)
            if search_results:
                search_context = f"\n\n[Real-time Web Search Results]:\n{search_results}\n\nInstructions: Answer the user's question accurately using the real-time context provided above if it is relevant."
                
        if search_context:
            self.history[-1]["content"] += search_context
        # --------------------------------------------

        try:
            if self.provider == "gemini":
                stream = self._stream_gemini()
            elif self.provider == "groq":
                stream = self._stream_groq()
            elif self.provider in ("anthropic", "claude"):
                stream = self._stream_anthropic()
            else:
                stream = self._stream_offline(user_input_clean)

            for chunk in stream:
                if isinstance(chunk, dict):
                    yield chunk
                else:
                    accumulated_response.append(chunk)
                    yield chunk

        except Exception as err:
            error_message = getattr(self, '_format_error_message', lambda e: str(e))(err)
            accumulated_response.append(f"\n\n> ⚠️ **Error:** {error_message}")
            yield f"\n\n> ⚠️ **Error:** {error_message}"
        finally:
            # Revert the temporary context injection so it doesn't pollute user-facing chat history
            if search_context:
                self.history[-1]["content"] = user_input_clean

        # Persist complete response into memory
        final_text = "".join(accumulated_response).strip()
        if final_text:
            self.add_assistant_message(final_text)

    def chat(self, user_input: str, image: Optional[str] = None) -> str:
        """Non-streaming convenience wrapper around chat_stream."""
        return "".join(list(self.chat_stream(user_input, image=image)))

    def voice_chat(
        self,
        timeout: int = 5,
        phrase_time_limit: int = 15,
        language: str = "en-US",
    ) -> Optional[Dict]:
        """
        Captures voice from the microphone, transcribes it, sends it to the LLM,
        and records the exchange in conversation history with metadata.

        Returns:
            Dict with keys 'transcription' and 'response' on success,
            or None if no speech was captured / on timeout.
        """
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")

        # Step 1: Capture and transcribe voice
        transcription = listen_and_transcribe(
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
            language=language,
        )

        if not transcription:
            return None

        # Step 2: Save transcribed user turn with metadata
        self.history.append({
            "role": "user",
            "content": transcription,
            "timestamp": timestamp,
            "input_type": "voice",
        })

        # --- NEW: Check for Web Search Heuristics ---
        search_keywords = ["price", "live", "current", "latest", "today", "stock", "weather", "news"]
        lower_input = transcription.lower()
        search_context = ""
        if any(kw in lower_input for kw in search_keywords):
            search_results = search_web_tavily(transcription)
            if search_results:
                search_context = f"\n\n[Real-time Web Search Results]:\n{search_results}\n\nInstructions: Answer the user's question accurately using the real-time context provided above if it is relevant."
                self.history[-1]["content"] += search_context
        # --------------------------------------------

        # Step 3: Stream LLM response
        print(f"\n[Nova AI] ({self.model_name}): ", end="", flush=True)
        response_chunks: List[str] = []

        try:
            if self.provider == "gemini":
                stream = self._stream_gemini()
            elif self.provider == "groq":
                stream = self._stream_groq()
            elif self.provider in ("anthropic", "claude"):
                stream = self._stream_anthropic()
            else:
                stream = self._stream_offline(transcription)

            for chunk in stream:
                response_chunks.append(chunk)
                print(chunk, end="", flush=True)

        except Exception as err:
            error_msg = getattr(self, '_format_error_message', lambda e: str(e))(err)
            response_chunks.append(f"\n\n> ⚠️ Error: {error_msg}")
            print(f"\n[Voice] ❌ {error_msg}", flush=True)
        finally:
            if search_context:
                self.history[-1]["content"] = transcription

        print()  # Newline

        # Step 4: Save assistant turn with metadata
        response_text = "".join(response_chunks).strip()
        if response_text:
            self.history.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                "input_type": "voice",
            })

        return {"transcription": transcription, "response": response_text}

    # -------------------------------------------------------------------------
    # 1. Google Gemini API Provider (Real-time Multimodal Vision & Streaming)
    # -------------------------------------------------------------------------
    def _stream_gemini(self) -> Generator[Union[str, dict], None, None]:
        if not self.api_key:
            raise ValueError(
                "Gemini API key is missing. Please provide your API key in the sidebar "
                "or set GEMINI_API_KEY in your .env file."
            )

        # Real-time streaming endpoint (alt=sse streams each token as it is generated)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:streamGenerateContent"
            f"?alt=sse&key={self.api_key}"
        )

        contents = []
        for msg in self.history:
            role = "user" if msg["role"] == "user" else "model"
            parts = []

            # Multimodal Vision support: If image attached, encode as inlineData
            img = msg.get("image")
            if img:
                try:
                    if "," in img:
                        header, b64data = img.split(",", 1)
                        mime_type = "image/jpeg"
                        if ":" in header and ";" in header:
                            mime_type = header.split(";")[0].split(":")[1]
                    else:
                        mime_type = "image/jpeg"
                        b64data = img

                    parts.append({
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": b64data,
                        }
                    })
                except Exception as img_err:
                    print(f"[Vision] ⚠️ Image parsing warning: {img_err}", flush=True)

            text_content = msg.get("content", "")
            if text_content:
                parts.append({"text": text_content})
            elif not parts:
                parts.append({"text": "Describe this image in detail."})

            if parts:
                contents.append({"role": role, "parts": parts})

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": self.system_prompt}]},
            "generationConfig": {"temperature": self.temperature},
        }
        req_data = json.dumps(payload).encode("utf-8")

        # Models to try in priority order (with fallback if experimental or unreleased 404s)
        models_to_try = [self.model_name]
        for fb in ("gemini-3.6-flash", "gemini-flash-latest", "gemini-2.5-pro", "gemini-1.5-pro"):
            if fb not in models_to_try:
                models_to_try.append(fb)

        last_error = None
        for current_model in models_to_try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:streamGenerateContent"
                f"?alt=sse&key={self.api_key}"
            )
            request = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            try:
                has_yielded = False
                with urllib.request.urlopen(request, timeout=120) as resp:
                    if current_model != self.model_name:
                        yield {"model_changed": current_model}
                        self.model_name = current_model
                    while True:
                        raw_line = resp.readline()
                        if not raw_line:
                            break
                        line_str = raw_line.decode("utf-8").strip()
                        if line_str.startswith("data: "):
                            data_json = line_str[6:].strip()
                            if data_json == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(data_json)
                                candidates = chunk_data.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for p in parts:
                                        text_piece = p.get("text", "")
                                        if text_piece:
                                            has_yielded = True
                                            yield text_piece
                            except Exception:
                                continue
                return  # Completed successfully

            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                try:
                    err_json = json.loads(error_body)
                    msg = err_json.get("error", {}).get("message", error_body)
                except Exception:
                    msg = error_body

                if e.code in (404, 429):
                    print(f"[Gemini API] ⚠️ Model '{current_model}' returned {e.code}, falling back to next available Gemini model...", flush=True)
                    last_error = RuntimeError(f"Gemini API Error ({e.code}): {msg}")
                    continue
                else:
                    raise RuntimeError(f"Gemini API Error ({e.code}): {msg}")

            except (TimeoutError, urllib.error.URLError, Exception) as e:
                last_error = RuntimeError(f"Gemini streaming error: {str(e)}")
                break

        if last_error:
            raise last_error

    # -------------------------------------------------------------------------
    # 2. Groq API Streamer
    # -------------------------------------------------------------------------
    def _stream_groq(self) -> Generator[Union[str, dict], None, None]:
        if not self.api_key:
            raise ValueError(
                "Groq API key is missing. Please provide your API key in the sidebar "
                "or set GROQ_API_KEY in your .env file."
            )

        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in self.history:
            role = msg.get("role")
            if role in ("user", "assistant", "system"):
                messages.append({"role": role, "content": msg.get("content", "")})

        models_to_try = [self.model_name]
        for fb in ("openai/gpt-oss-120b", "openai/gpt-oss-20b", "groq/compound", "groq/compound-mini", "qwen/qwen3.6-27b", "qwen/qwen3.8-27b"):
            if fb not in models_to_try:
                models_to_try.append(fb)

        last_error = None
        for current_model in models_to_try:
            # Groq uses OpenAI-compatible API
            try:
                import openai
                client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
                response = client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=self.temperature,
                    stream=True,
                )
                if current_model != self.model_name:
                    yield {"model_changed": current_model}
                    self.model_name = current_model
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if getattr(delta, "content", None):
                            yield delta.content
                return
            except ImportError:
                pass  # Fallback to standard library urllib
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "rate limit" in err_str or "404" in err_str or "not found" in err_str:
                    print(f"[Groq API] ⚠️ Model '{current_model}' failed with {e}, falling back...", flush=True)
                    last_error = RuntimeError(f"Groq API Error: {str(e)}")
                    continue
                else:
                    raise

            # Standard library HTTP fallback with real streaming
            base = self.base_url.rstrip("/") if self.base_url else "https://api.groq.com/openai/v1"
            url = f"{base}/chat/completions"

            payload = {
                "model": current_model,
                "messages": messages,
                "temperature": self.temperature,
                "stream": True,
            }

            req_data = json.dumps(payload).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; python-urllib)",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            request = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

            try:
                with urllib.request.urlopen(request, timeout=60) as resp:
                    if current_model != self.model_name:
                        yield {"model_changed": current_model}
                        self.model_name = current_model
                    while True:
                        raw_line = resp.readline()
                        if not raw_line:
                            break
                        line_str = raw_line.decode("utf-8").strip()
                        if line_str.startswith("data: "):
                            data_json = line_str[6:].strip()
                            if data_json == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(data_json)
                                choices = chunk_data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except Exception:
                                continue
                return
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                if e.code in (404, 429):
                    print(f"[Groq API] ⚠️ Model '{current_model}' returned {e.code}, falling back...", flush=True)
                    last_error = RuntimeError(f"Groq API Error ({e.code}): {error_body}")
                    continue
                else:
                    raise RuntimeError(f"Groq API Error ({e.code}): {error_body}")
                    
        if last_error:
            raise last_error

    # -------------------------------------------------------------------------
    # 2.5 Anthropic / Claude Provider
    # -------------------------------------------------------------------------
    def _stream_anthropic(self) -> Generator[str, None, None]:
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is missing. Please provide your API key in the sidebar "
                "or set ANTHROPIC_API_KEY in your .env file."
            )

        # Try native SDK if installed
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            messages = []
            for msg in self.history:
                role = msg.get("role")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": msg.get("content", "")})
            while messages and messages[0]["role"] != "user":
                messages.pop(0)

            if not messages:
                return

            stream_kwargs = {
                "model": self.model_name,
                "max_tokens": 4096,
                "system": self.system_prompt,
                "messages": messages,
            }
            # Anthropic SDK signatures vary across versions; pass via extra_body if not an explicit kwarg
            import inspect
            sig = inspect.signature(client.messages.stream)
            if "temperature" in sig.parameters:
                stream_kwargs["temperature"] = self.temperature
            else:
                stream_kwargs["extra_body"] = {"temperature": self.temperature}

            with client.messages.stream(**stream_kwargs) as stream:
                for text in stream.text_stream:
                    yield text
            return
        except ImportError:
            pass  # Fallback to standard library urllib

        # Standard library HTTP fallback
        url = "https://api.anthropic.com/v1/messages"
        messages = []
        for msg in self.history:
            role = msg.get("role")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": msg.get("content", "")})
        while messages and messages[0]["role"] != "user":
            messages.pop(0)

        payload = {
            "model": self.model_name,
            "max_tokens": 4096,
            "temperature": self.temperature,
            "system": self.system_prompt,
            "messages": messages,
        }
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                for block in res_data.get("content", []):
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        words = text.split(" ")
                        for i, w in enumerate(words):
                            yield w + (" " if i < len(words) - 1 else "")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Anthropic API Error ({e.code}): {error_body}")


    # -------------------------------------------------------------------------
    # 4. Built-in Offline Mode (Zero-key fallback & local testing)
    # -------------------------------------------------------------------------
    def _stream_offline(self, text: str) -> Generator[str, None, None]:
        response = self._generate_offline_response(text)
        words = response.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    def _generate_offline_response(self, text: str) -> str:
        clean = text.strip().lower()

        # Math calculation
        math_match = re.search(r"(?:calculate|what is|compute|solve)?\s*([\d\.\s\+\-\*\/\(\)\^\%]+)", clean)
        if math_match and any(op in text for op in ["+", "-", "*", "/", "^", "%"]):
            expr = math_match.group(1).replace("^", "**").strip()
            if re.match(r"^[\d\.\+\-\*\/\(\)\s\*\*]+$", expr):
                try:
                    result = eval(expr, {"__builtins__": None}, {"math": math})
                    return f"The result of `{expr.replace('**', '^')}` is: **{result}**"
                except Exception:
                    pass

        # Greetings
        if re.search(r"^(hi|hello|hey|greetings|howdy|sup)\b", clean):
            return (
                "Hello! 👋 I am your AI Chatbot.\n\n"
                "I am currently operating in **Offline Mode** (ready out-of-the-box!). "
                "You can ask me questions, request math calculations, or discuss Python programming.\n\n"
                "💡 *To connect to live cloud models (Google Gemini, OpenAI, Claude), "
                "select the provider and enter your API key in the settings.*"
            )

        # Date & Time
        if "time" in clean or "date" in clean or "today" in clean:
            now = datetime.datetime.now()
            return f"Current local time: **{now.strftime('%A, %B %d, %Y at %I:%M:%S %p')}**"

        # Python questions
        if "python" in clean:
            return (
                "### Python Quick Reference\n\n"
                "Python is an expressive, high-level programming language ideal for AI, web apps, and data science.\n\n"
                "```python\n"
                "# Example: Streaming with Python generators\n"
                "def token_generator():\n"
                "    tokens = ['Building', 'intelligent', 'apps', 'with', 'Python!']\n"
                "    for token in tokens:\n"
                "        yield token\n"
                "```\n\n"
                "Select **Google Gemini**, **OpenAI**, or **Claude** in settings with an API key to ask advanced coding questions!"
            )

        turn_count = len(self.history)
        return (
            f"You asked: *\"{text}\"*\n\n"
            f"💡 **Notice**: You are currently in offline mode (Turn #{turn_count}). "
            f"I have recorded this in memory. Select **Google Gemini**, **OpenAI**, or **Claude** in settings "
            f"to enable live LLM reasoning!"
        )

    def _format_error_message(self, err: Exception) -> str:
        return str(err).strip()


if __name__ == "__main__":
    import sys as _sys

    if "--check-voice" in _sys.argv:
        # ---------------------------------------------------------------
        # Voice diagnostics: Check libraries and detect microphones
        # Usage:  python bot_core.py --check-voice
        # ---------------------------------------------------------------
        check_voice_dependencies()
        list_available_microphones()

    elif "--voice" in _sys.argv:
        # ---------------------------------------------------------------
        # Voice-input interactive loop
        # Usage:  python bot_core.py --voice
        # ---------------------------------------------------------------
        print("========================================")
        print("✨ Nova AI — Interactive Voice Mode")
        print("========================================")
        print("Commands:")
        print("  Speak when prompted")
        print("  Press Ctrl+C to exit\n")

        # Quick pre-flight check
        mics = list_available_microphones()
        if not mics:
            print("\n⚠️ Warning: No audio input devices detected!")
            print("Please ensure your microphone is plugged in and permissions are granted.\n")

        engine = ChatbotEngine()  # Uses defaults / .env keys
        print(f"Active Provider: {engine.provider.upper()} | Model: {engine.model_name}\n")

        while True:
            try:
                result = engine.voice_chat(timeout=5, phrase_time_limit=15)
                if result is None:
                    print("[Voice] ℹ️ Ready for next phrase...\n")
                else:
                    print("-" * 40 + "\n")
            except KeyboardInterrupt:
                print("\n[Voice] 👋 Goodbye!")
                break
    else:
        try:
            import cli
            cli.main()
        except ImportError:
            # Standalone fallback if cli module is not present
            print("Usage:")
            print("  python bot_core.py --voice        (Interactive voice chat)")
            print("  python bot_core.py --check-voice  (Check mic & dependencies)")
