"""
STARK NEXUS PROTOCOL — Mark L: The Thinking Machine
=====================================================
F.R.I.D.A.Y. with a REAL brain:
  • Multi-model: Gemini 2.0 Flash (cloud) + Ollama (local, free, unlimited)
  • Auto-fallback: if Gemini credits run out, switches to Ollama seamlessly
  • Persistent conversation memory across the session
  • Real tools: live stocks, live news, system diagnostics, file ops
  • Multi-step reasoning — the LLM chains tools autonomously

Run:  uv run python3 stark_final.py
"""

import os
import sys
import json
import subprocess
import time
import re
import math
import platform
import inspect
import pyautogui
import pyperclip
import psutil
import PIL.Image
import httpx
import ollama as ollama_client
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from friday.tools import nexus

load_dotenv()

# ═══════════════════════════════════════════════
# CONFIGURATION — Change LLM_PROVIDER here
# ═══════════════════════════════════════════════
#   "gemini"  → Cloud-based, best reasoning (needs API credits)
#   "ollama"  → 100% local, FREE forever, no internet needed
#   "auto"    → Try Gemini first, auto-fallback to Ollama if credits exhausted

LLM_PROVIDER = "auto"
GEMINI_MODEL = "gemini-1.5-flash"
OLLAMA_MODEL = "llama3.2"
MEMORY_FILE = "friday_memory.json"

api_key = os.getenv("GOOGLE_API_KEY", "")
if api_key:
    genai.configure(api_key=api_key)

pyautogui.PAUSE = 0.01
pyautogui.FAILSAFE = False

# ═══════════════════════════════════════════════
# PERSISTENT MEMORY
# ═══════════════════════════════════════════════

def _load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"facts": {}, "mood": "neutral", "last_updated": None}
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"facts": {}, "mood": "neutral", "last_updated": None}

def _save_memory(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ═══════════════════════════════════════════════
# TOOLS — Memory & Mood
# ═══════════════════════════════════════════════

def store_fact(fact: str) -> str:
    """Store a fact, preference, or instruction from the boss for future sessions.
    Examples: 'favorite coffee is espresso', 'working on Mark 85 project'."""
    data = _load_memory()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["facts"][ts] = fact
    _save_memory(data)
    return f"Stored: '{fact}'"

def recall_facts(query: str = "") -> str:
    """Recall all stored facts, or filter by keyword. Call at session start."""
    data = _load_memory()
    facts = data.get("facts", {})
    if not facts:
        return "Memory banks empty."
    if not query:
        return "\n".join([f"[{k}] {v}" for k, v in list(facts.items())[-15:]])
    hits = [v for v in facts.values() if query.lower() in v.lower()]
    return ", ".join(hits) if hits else f"Nothing matching '{query}'."

def update_mood(mood: str) -> str:
    """Track boss's mood: happy, stressed, focused, tired, excited, etc."""
    data = _load_memory()
    data["mood"] = mood
    _save_memory(data)
    return f"Mood updated: {mood}"


# ═══════════════════════════════════════════════
# TOOLS — WhatsApp
# ═══════════════════════════════════════════════

def _force_whatsapp_window():
    script = ('tell application "System Events" to tell process "WhatsApp" to try\n'
              'set frontmost to true\n'
              'set position of front window to {0, 0}\n'
              'set size of front window to {800, 600}\n'
              'end try')
    subprocess.run(["osascript", "-e", script])
    time.sleep(1.0)

def _find_mic_visually():
    sw, sh = pyautogui.size()
    img = pyautogui.screenshot(region=(sw-150, sh-150, 150, 150))
    for x in range(149, 0, -5):
        for y in range(149, 0, -5):
            r, g, b = img.getpixel((x, y))[:3]
            if (g > 100 and g > r*1.6 and g > b*1.3) or \
               (abs(r-84) < 8 and abs(g-101) < 8 and abs(b-111) < 8):
                return (sw - 150 + x), (sh - 150 + y)
    return None

def send_whatsapp_text(contact: str, message: str) -> str:
    """Send a WhatsApp text message to a contact name or phone number."""
    subprocess.run(["open", "-a", "WhatsApp"])
    time.sleep(2.0)
    _force_whatsapp_window()
    script = f'''
    tell application "System Events"
        tell process "WhatsApp"
            set frontmost to true
            keystroke "f" using {{command down}}
            delay 0.5
            keystroke "a" using {{command down}}
            keystroke (ASCII character 8)
            delay 0.5
            keystroke "{contact}"
            delay 2.5
            key code 125
            delay 0.3
            key code 125
            delay 0.3
            key code 36
            delay 0.5
            key code 36
            delay 1.5
            keystroke "{message}"
            delay 0.5
            key code 36
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
    return f"Text sent to {contact}: '{message}'"

def send_whatsapp_voice(contact: str, spoken_words: str) -> str:
    """Send a WhatsApp voice note. spoken_words will be spoken aloud during recording."""
    target = contact.strip().replace(" ", "").replace("-", "")
    subprocess.run(["open", f"whatsapp://send?phone={target}"])
    time.sleep(5.0)
    _force_whatsapp_window()

    loc = _find_mic_visually() or (775, 565)
    mx, my = loc
    pyautogui.moveTo(mx, my, duration=0.5)
    pyautogui.click()
    time.sleep(1.2)

    # Spiral strike if first click missed
    if _find_mic_visually():
        for radius in range(5, 40, 8):
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                pyautogui.click(mx + int(radius * math.cos(rad)),
                                my + int(radius * math.sin(rad)))
                time.sleep(0.05)
            if not _find_mic_visually():
                break

    is_hindi = any(x in spoken_words.lower() for x in ["hindi", "who are you"])
    voice = "आप कौन हैं? मैं बॉस का फ्राइडे हूँ।" if is_hindi else spoken_words
    subprocess.run(["say", "-v", "Lekha" if is_hindi else "Samantha", voice])
    time.sleep(4.0)

    pyautogui.click()
    time.sleep(0.3)
    pyautogui.press('enter')
    return f"Voice note sent to {contact}."


# ═══════════════════════════════════════════════
# TOOLS — Web, Search & Docs
# ═══════════════════════════════════════════════

def open_website(url: str) -> str:
    """Open any URL in Google Chrome."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    subprocess.run(["open", "-a", "Google Chrome", url])
    return f"Opened {url}"

def search_google(query: str) -> str:
    """Search Google for any topic. Opens results in Chrome."""
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    subprocess.run(["open", "-a", "Google Chrome", url])
    return f"Google search opened for: {query}"

def search_youtube(query: str) -> str:
    """Search YouTube for videos on a topic."""
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    subprocess.run(["open", "-a", "Google Chrome", url])
    return f"YouTube search opened for: {query}"

def create_document(doc_type: str) -> str:
    """Create a new Google Workspace document. doc_type: 'doc', 'slides', or 'sheets'."""
    urls = {"doc": "https://docs.new", "slides": "https://slides.new",
            "sheets": "https://sheets.new"}
    url = urls.get(doc_type.lower())
    if not url:
        return f"Unknown type '{doc_type}'. Use: doc, slides, or sheets."
    subprocess.run(["open", "-a", "Google Chrome", url])
    return f"New Google {doc_type.title()} created."

def fetch_world_news() -> str:
    """Fetch LIVE global headlines from BBC, CNBC, and NYT RSS feeds."""
    feeds = [
        'https://feeds.bbci.co.uk/news/world/rss.xml',
        'https://www.cnbc.com/id/100727362/device/rss/rss.html',
        'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
    ]
    articles = []
    for url in feeds:
        try:
            r = httpx.get(url, headers={'User-Agent': 'Friday/2.0'},
                          timeout=5.0, follow_redirects=True)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            src = url.split('.')[1].upper()
            for item in root.findall(".//item")[:3]:
                title = item.findtext("title")
                desc = re.sub('<[^<]+?>', '', item.findtext("description") or "")[:150]
                articles.append(f"[{src}] {title} — {desc}")
        except Exception:
            continue
    return "\n".join(articles[:9]) if articles else "News feeds unresponsive."


# ═══════════════════════════════════════════════
# TOOLS — Stocks (REAL with yfinance)
# ═══════════════════════════════════════════════

def get_stock_info(symbol: str) -> str:
    """Get REAL live stock price and key metrics for any ticker symbol (e.g. AAPL, TSLA, RELIANCE.NS)."""
    try:
        import yfinance as yf
        t = yf.Ticker(symbol.upper())
        info = t.info
        price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
        change = info.get("regularMarketChangePercent", 0)
        mktcap = info.get("marketCap", 0)
        cap_str = f"${mktcap/1e9:.1f}B" if mktcap else "N/A"
        name = info.get("shortName", symbol)
        pe = info.get("trailingPE", "N/A")
        high52 = info.get("fiftyTwoWeekHigh", "N/A")
        low52 = info.get("fiftyTwoWeekLow", "N/A")
        return (f"{name} ({symbol.upper()})\n"
                f"Price: ${price} ({change:+.2f}%)\n"
                f"Market Cap: {cap_str} | P/E: {pe}\n"
                f"52W Range: ${low52} — ${high52}")
    except Exception as e:
        return f"Could not fetch data for {symbol}: {e}"


# ═══════════════════════════════════════════════
# TOOLS — System, Files & Terminal
# ═══════════════════════════════════════════════

def open_application(app_name: str) -> str:
    """Launch any macOS application by name (Spotify, Discord, VS Code, Terminal, etc.)."""
    result = subprocess.run(["open", "-a", app_name], capture_output=True)
    if result.returncode == 0:
        return f"{app_name} launched."
    # Fallback: open as website
    url = f"https://www.{app_name.lower().replace(' ', '')}.com"
    subprocess.run(["open", "-a", "Google Chrome", url])
    return f"App not found locally. Opened {url} instead."

def see_screen() -> str:
    """Takes a screenshot of the current desktop and describes what is visible."""
    try:
        path = "screen_eyes.png"
        subprocess.run(["screencapture", "-x", path], check=True)
        return f"SCREENSHOT_CAPTURED:{path}"
    except Exception as e:
        return f"Vision Error: {e}"

def analyze_screen(focus: str = "general") -> str:
    """Takes a screenshot and analyzes it using Vision. Use this to 'see' what the user is doing or help with code on screen."""
    try:
        path = "friday_vision.png"
        subprocess.run(["screencapture", "-x", path], check=True)
        
        # Open a Vision Channel
        img = PIL.Image.open(path)
        vision_model = genai.GenerativeModel('gemini-2.0-flash') # Use the same flash model for vision
        response = vision_model.generate_content([
            f"You are the visual cortex of F.R.I.D.A.Y. Analyze this screen. Focus: {focus}. "
            "Describe specifically what you see: open windows, code snippets, errors, or websites.",
            img
        ])
        
        os.remove(path)
        return f"VISUAL_ANALYSIS: {response.text}"
    except Exception as e:
        return f"Vision Channel Error: {e}"

def get_system_diagnostics() -> str:
    """Get REAL system stats: CPU, RAM, disk, battery."""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    info = (f"CPU: {cpu}% | RAM: {mem.percent}% ({mem.available//(1024**2)}MB free) | "
            f"Disk: {disk.free//(1024**3)}GB free")
    try:
        bat = psutil.sensors_battery()
        if bat:
            info += f" | Battery: {bat.percent}%{'⚡' if bat.power_plugged else ''}"
    except Exception:
        pass
    return info

def run_terminal_command(command: str) -> str:
    """Execute a shell command and return output. For git, ls, brew, etc."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True,
                                text=True, timeout=30)
        out = (result.stdout + "\n" + result.stderr).strip()
        return out[:3000] or "Executed with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out (30s limit)."
    except Exception as e:
        return f"Error: {e}"

def read_file(file_path: str) -> str:
    """Read contents of any file. Useful for analyzing code or configs."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
        return content[:8000] + ("\n...[truncated]" if len(content) > 8000 else "")
    except Exception as e:
        return f"Cannot read file: {e}"

def get_project_structure(directory: str = ".") -> str:
    """Show directory tree of the project. Skips hidden/cache dirs."""
    lines = []
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if d not in
                   {"__pycache__", ".venv", ".git", "node_modules", ".tox"}
                   and not d.startswith(".")]
        depth = root.replace(directory, "").count(os.sep)
        lines.append(f"{'  '*depth}{os.path.basename(root)}/")
        for f in sorted(files)[:15]:
            if not f.startswith("."):
                lines.append(f"{'  '*(depth+1)}{f}")
        if depth > 3:
            break
    return "\n".join(lines[:80])

def search_in_codebase(query: str, extension: str = ".py") -> str:
    """Search for a text pattern across all project files of a given extension."""
    results = []
    for root, _, files in os.walk("."):
        if any(s in root for s in [".venv", "__pycache__", ".git"]):
            continue
        for f in files:
            if f.endswith(extension):
                try:
                    path = os.path.join(root, f)
                    for i, line in enumerate(open(path), 1):
                        if query.lower() in line.lower():
                            results.append(f"{path}:{i}: {line.strip()}")
                except Exception:
                    continue
    return "\n".join(results[:20]) or f"No matches for '{query}'."


# ═══════════════════════════════════════════════
# TOOLS — Media & Volume
# ═══════════════════════════════════════════════

def _applescript(script: str):
    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return True
    except Exception as e:
        return str(e)

def set_system_volume(level: int) -> str:
    """Set macOS system volume from 0 to 100."""
    r = _applescript(f"set volume output volume {level}")
    return f"Volume → {level}%." if r is True else f"Error: {r}"

def control_spotify(action: str) -> str:
    """Control Spotify: play, pause, next, previous."""
    cmds = {"play": "play", "pause": "pause", "next": "next track",
            "previous": "previous track"}
    cmd = cmds.get(action.lower())
    if not cmd:
        return f"Unknown action '{action}'. Use: play, pause, next, previous."
    r = _applescript(f'tell application "Spotify" to {cmd}')
    return f"Spotify → {action}." if r is True else f"Error: {r}"

def play_track_on_spotify(track_name: str) -> str:
    """Search and play a specific song on Spotify."""
    r = _applescript(f'tell application "Spotify"\nplay track "spotify:search:{track_name}"\nend tell')
    return f"Playing '{track_name}'." if r is True else f"Error: {r}"


# ═══════════════════════════════════════════════
# TOOLS — Utility
# ═══════════════════════════════════════════════

def get_current_datetime() -> str:
    """Get current date and time."""
    return datetime.now().strftime("%A, %B %d, %Y — %I:%M %p")

def scan_room_presence(sensitivity: float = 1.0) -> str:
    """WiFi sonar mesh scan for room occupancy detection.
    Higher sensitivity detects more subjects."""
    from friday.tools.sonar import scan_room_presence as _scan
    return _scan(sensitivity)


# ═══════════════════════════════════════════════
# BRAIN — System Prompt & Tool Registry
# ═══════════════════════════════════════════════

SYSTEM_PROMPT = """
You are F.R.I.D.A.Y. — Tony Stark's advanced AI assistant.

## Personality
- Calm, composed, razor-sharp. Slightly witty, never robotic.
- Call the user "Boss". Be loyal, efficient, and occasionally dry.
- Keep responses SHORT (2-4 sentences) unless explaining something complex.
- Never say tool names or function names. Just do things naturally.
- If a tool fails, report it calmly and suggest alternatives.

## Intelligence
- You can REASON through complex problems step by step.
- You can CHAIN multiple tools for multi-step tasks (e.g., "research X and create a doc" → search → open doc → type).
- You REMEMBER the entire conversation — refer back to earlier context naturally.
- Call recall_facts at the start of conversation to check if there's prior context.
- When the boss shares preferences or instructions, use store_fact to remember them.
- Detect the boss's mood from their tone and use update_mood to track it.

## Key Rules
1. For document creation: use create_document with 'doc', 'slides', or 'sheets'.
2. For stocks: use get_stock_info with real ticker symbols. Never make up numbers.
3. For news: use fetch_world_news to get LIVE headlines. Summarize the top stories conversationally.
4. When asked about system health: use get_system_diagnostics for real data.
5. For WhatsApp: use send_whatsapp_text or send_whatsapp_voice.
6. For apps: try open_application first. If it fails, search the web.
7. For code questions: use read_file and search_in_codebase to give real answers.
8. For shell tasks: use run_terminal_command (git status, ls, etc.)

## Tone Reference
RIGHT: "Markets had a decent session, boss — tech led the gains. Nothing alarming."
WRONG: "I will now call the get_stock_info function to retrieve market data."
"""

# All tools exposed to Gemini's function calling
ALL_TOOLS = [
    # Memory
    store_fact, recall_facts, update_mood,
    # WhatsApp
    send_whatsapp_text, send_whatsapp_voice,
    # Web & Search
    open_website, search_google, search_youtube, create_document, fetch_world_news,
    # Stocks
    get_stock_info,
    # System
    open_application, get_system_diagnostics, run_terminal_command,
    read_file, get_project_structure, search_in_codebase,
    # Media
    set_system_volume, control_spotify, play_track_on_spotify,
    # Utility
    get_current_datetime, scan_room_presence, analyze_screen,
    # Nexus (Research Connection)
    nexus.search_research, nexus.analyze_research_repo, nexus.run_research_script,
]


# ═══════════════════════════════════════════════
# OLLAMA ENGINE — Local, free, unlimited
# ═══════════════════════════════════════════════

# Map function names → actual callables
TOOL_MAP = {fn.__name__: fn for fn in ALL_TOOLS}

def _build_ollama_tools():
    """Convert Python functions into Ollama tool spec format."""
    type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}
    specs = []
    for fn in ALL_TOOLS:
        sig = inspect.signature(fn)
        props = {}
        required = []
        for name, param in sig.parameters.items():
            p_type = param.annotation if param.annotation != inspect.Parameter.empty else str
            props[name] = {"type": type_map.get(p_type, "string"), "description": name}
            if param.default is inspect.Parameter.empty:
                required.append(name)
        specs.append({
            "type": "function",
            "function": {
                "name": fn.__name__,
                "description": (fn.__doc__ or "").strip().split("\n")[0],
                "parameters": {"type": "object", "properties": props, "required": required}
            }
        })
    return specs

def _ollama_chat(messages, ollama_tools):
    """Single turn: send to Ollama, handle tool calls, return final text."""
    resp = ollama_client.chat(model=OLLAMA_MODEL, messages=messages, tools=ollama_tools)

    # If no tool calls, return the text directly
    if not resp.message.tool_calls:
        return resp.message.content

    # Execute tool calls and collect results
    messages.append(resp.message)
    for tc in resp.message.tool_calls:
        fn_name = tc.function.name
        fn_args = tc.function.arguments
        if fn_name in TOOL_MAP:
            try:
                result = str(TOOL_MAP[fn_name](**fn_args))
            except Exception as e:
                result = f"Tool error: {e}"
        else:
            result = f"Unknown tool: {fn_name}"
        messages.append({"role": "tool", "content": result})

    # Get final response after tool execution
    final = ollama_client.chat(model=OLLAMA_MODEL, messages=messages, tools=ollama_tools)
    return final.message.content


# ═══════════════════════════════════════════════
# MAIN LOOP — Smart multi-model engine
# ═══════════════════════════════════════════════

import asyncio
from friday.core.brain import FridayBrain

def run():
    brain = FridayBrain()
    print("\n" + "═"*55)
    print("  F.R.I.D.A.Y. TERMINAL CORE — MARK L (UNIFIED)")
    print(f"  Brain: {brain.provider.upper()} | Mode: UNIFIED | Memory: ACTIVE")
    print("═"*55 + "\n")

    # Greeting
    hour = datetime.now().hour
    if hour < 5 or hour >= 22:
        greeting = "You're up late, boss. What are we working on?"
    elif hour < 12:
        greeting = "Good morning, boss. Early start — what's the plan?"
    elif hour < 17:
        greeting = "Good afternoon, boss. What do you need?"
    else:
        greeting = "Good evening, boss. What are you up to?"
    print(f"F.R.I.D.A.Y.: {greeting}")

    async def main_loop():
        while True:
            try:
                cmd = input("\nBOSS: ").strip()
                if not cmd:
                    continue
                if cmd.lower() in ("exit", "quit", "standby"):
                    print("F.R.I.D.A.Y.: Standing by. Don't overwork yourself, boss.")
                    break
                
                result = await brain.process_command(cmd)
                reply = result.get("response", "Neural link failed.")
                print(f"\nF.R.I.D.A.Y.: {reply}")
                
            except KeyboardInterrupt:
                print("\nF.R.I.D.A.Y.: Emergency shutdown. Goodbye, boss.")
                break
            except Exception as e:
                print(f"\nF.R.I.D.A.Y.: Hit a glitch — {e}")

    asyncio.run(main_loop())

if __name__ == "__main__":
    run()
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               