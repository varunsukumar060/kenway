#!/usr/bin/env python3
"""
core/llm_bridge.py — KENWAY LLM Bridge (Ollama)
Only called when user enables LLM mode via tray toggle.
The LLM acts as a smart intent parser — it outputs JSON, never free-text chat.
"""

import requests
import json
import logging
import os
import yaml

log = logging.getLogger("kenway.llm_bridge")

# Short conversation memory — last 6 exchanges kept in RAM
_memory: list[dict] = []
MAX_MEMORY = 6

SYSTEM_PROMPT = """You are KENWAY's intent parser brain. Your ONLY job is to parse the user's command and return a JSON object.

Available actions:
  YOUTUBE_PLAY     - data: search query string
  GOOGLE_SEARCH    - data: search query string
  OPEN_URL         - data: full URL
  OPEN_APP         - data: app name
  CLOSE_APP        - data: app name
  OPEN_FOLDER      - data: folder name (desktop/documents/downloads/music/pictures/videos/kenway/arduino/home)
  OPEN_FILE        - data: filename
  FILE_READ        - data: filename
  FILE_WRITE       - data: [content, filename] as a list
  FILE_LIST        - data: folder name or null
  VOLUME_SET       - data: up / down / mute / unmute / 0-100
  BRIGHTNESS_SET   - data: up / down / 0-100
  BRIGHTNESS_GET   - data: null
  BATTERY_STATUS   - data: null
  READ_SCREEN      - data: null
  SHUTDOWN         - data: null
  REBOOT           - data: null

Rules:
- Return ONLY valid JSON. No explanation, no extra text.
- Format: {"action": "ACTION_NAME", "data": <value or null>}
- If the command is ambiguous, pick the most likely action.
- Never return anything other than the JSON object.

Examples:
  "play old town road" -> {"action": "YOUTUBE_PLAY", "data": "old town road"}
  "what's in my downloads?" -> {"action": "FILE_LIST", "data": "downloads"}
  "make it brighter" -> {"action": "BRIGHTNESS_SET", "data": "up"}
  "open the file I was editing" -> {"action": "OPEN_FILE", "data": "last_edited"}
  "turn down the music" -> {"action": "VOLUME_SET", "data": "down"}
"""


def _cfg():
    path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)["llm"]


def _is_ollama_running() -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def ask(command: str) -> dict:
    """
    Send command to Ollama, get back a parsed intent dict.
    Falls back to direct parser if Ollama is unreachable.
    """
    global _memory

    if not _is_ollama_running():
        log.warning("Ollama not running — falling back to direct parser.")
        from core.intent_parser import parse
        return parse(command)

    cfg = _cfg()
    model = cfg.get("model", "qwen2.5:1.5b")

    # Build context from memory
    memory_ctx = ""
    if _memory:
        lines = [f"User: {m['user']}\nIntent: {m['intent']}" for m in _memory[-3:]]
        memory_ctx = "\nRecent context:\n" + "\n".join(lines) + "\n"

    prompt = f"{SYSTEM_PROMPT}{memory_ctx}\nCommand: {command}\nJSON:"

    try:
        log.info(f"Sending to Ollama [{model}]: {command}")
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=cfg.get("timeout", 30)
        )
        raw = r.json().get("response", "").strip()
        log.info(f"Ollama raw response: {raw}")

        # Extract JSON even if wrapped in markdown code blocks
        if "```" in raw:
            raw = raw.split("```")[1].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()

        intent = json.loads(raw)
        intent["mode"] = "llm"

        # Store in memory
        _memory.append({"user": command, "intent": json.dumps(intent)})
        if len(_memory) > MAX_MEMORY:
            _memory.pop(0)

        log.info(f"LLM intent: {intent}")
        return intent

    except json.JSONDecodeError as e:
        log.error(f"LLM JSON parse failed: {e} | raw: {raw}")
        from core.intent_parser import parse
        return parse(command)
    except Exception as e:
        log.error(f"LLM bridge error: {e}")
        from core.intent_parser import parse
        return parse(command)


def clear_memory():
    global _memory
    _memory = []
    log.info("LLM memory cleared.")


def get_memory_summary() -> str:
    if not _memory:
        return "No conversation memory yet."
    lines = [f"{i+1}. {m['user']}" for i, m in enumerate(_memory)]
    return "Recent commands: " + "; ".join(lines)
