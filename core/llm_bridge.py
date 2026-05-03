#!/usr/bin/env python3
"""
core/llm_bridge.py — KENWAY LLM Mode Bridge
Calls local Ollama only when LLM mode is toggled ON by user.
Never touches the internet — Ollama runs at localhost:11434.
"""

import requests
import json
import logging
import yaml
import os

log = logging.getLogger("kenway.llm_bridge")


def _load_llm_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f).get("llm", {})
    except Exception:
        return {"model": "qwen2.5:1.5b", "endpoint": "http://localhost:11434/api/generate", "timeout": 30}


SYSTEM_PROMPT = """You are KENWAY's command parser. Your ONLY job is to convert natural language into a JSON action.
Return ONLY valid JSON. No explanations. No chat. No markdown.

Format: {"action": "ACTION_TAG", "data": "extracted_value"}

Valid actions:
YOUTUBE_PLAY, YOUTUBE_SEARCH, GOOGLE_SEARCH, OPEN_URL,
SPOTIFY_PLAY, OPEN_APP, CLOSE_APP, VOLUME_SET,
BATTERY_STATUS, SHUTDOWN, REBOOT, SLEEP, BRIGHTNESS_SET,
READ_SCREEN, FILE_READ, FILE_WRITE, FILE_OPEN,
WINDOW_MINIMIZE, WINDOW_MAXIMIZE, WINDOW_FOCUS, UNKNOWN

Examples:
User: play gangnam style on youtube
Response: {"action": "YOUTUBE_PLAY", "data": "gangnam style"}

User: open vs code
Response: {"action": "OPEN_APP", "data": "code"}

User: what is my battery level
Response: {"action": "BATTERY_STATUS", "data": null}
"""


def ask(command: str) -> dict:
    """
    Send command to local Ollama LLM and get a structured intent back.
    Falls back to UNKNOWN if Ollama is unreachable.
    """
    cfg = _load_llm_config()
    payload = {
        "model": cfg.get("model", "qwen2.5:1.5b"),
        "prompt": f"{SYSTEM_PROMPT}\nUser: {command}\nResponse:",
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 100}
    }

    try:
        response = requests.post(
            cfg.get("endpoint", "http://localhost:11434/api/generate"),
            json=payload,
            timeout=cfg.get("timeout", 30)
        )
        raw = response.json().get("response", "").strip()
        log.info(f"LLM raw response: {raw}")

        # Extract JSON from response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            intent = json.loads(raw[start:end])
            intent["mode"] = "llm"
            return intent

    except requests.exceptions.ConnectionError:
        log.error("Ollama not running. Start it with: ollama serve")
        from core.voice import speak
        speak("LLM mode is on but Ollama is not running. Please start it.")
    except Exception as e:
        log.error(f"LLM bridge error: {e}")

    return {"action": "UNKNOWN", "data": command, "mode": "llm"}
