#!/usr/bin/env python3
"""
core/llm_bridge.py - KENWAY LLM Brain

Uses qwen2.5:0.5b via Ollama (local, offline, AMD GPU accelerated).
OLLAMA_KEEP_ALIVE=0 so model unloads from RAM immediately after response.

The model ONLY does JSON intent extraction - it never chats.
System prompt is strict: output JSON or nothing.

Supported actions (must match executor.py dispatch table):
  YOUTUBE_PLAY    data: search query string
  SPOTIFY_PLAY    data: search query string
  GOOGLE_SEARCH   data: search query string
  OPEN_URL        data: url string
  OPEN_APP        data: app name string
  CLOSE_APP       data: app name string
  VOLUME_SET      data: "up" | "down" | 0-100
  BATTERY_STATUS  data: null
  SHUTDOWN        data: null
  UNKNOWN         data: original command string
"""

import json
import logging
import requests

log = logging.getLogger("kenway.llm_bridge")

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL      = "qwen2.5:0.5b"

SYSTEM_PROMPT = """You are KENWAY's intent parser. Your ONLY job is to convert a user command into a JSON object.

Output ONLY valid JSON. No explanation. No markdown. No extra text. Just JSON.

JSON format:
{"action": "ACTION_NAME", "data": "value or null"}

Available actions:
- YOUTUBE_PLAY   : play a video on YouTube. data = search query
- SPOTIFY_PLAY   : play a song on Spotify. data = song/artist name
- GOOGLE_SEARCH  : search Google. data = search query
- OPEN_URL       : open a website. data = full URL
- OPEN_APP       : open an application. data = app name
- CLOSE_APP      : close an application. data = app name
- VOLUME_SET     : change volume. data = "up", "down", or number 0-100
- BATTERY_STATUS : check battery. data = null
- SHUTDOWN       : shutdown the computer. data = null
- UNKNOWN        : cannot determine intent. data = original command

Examples:
Command: play that korean horse dance song
{"action": "YOUTUBE_PLAY", "data": "gangnam style"}

Command: open my code editor
{"action": "OPEN_APP", "data": "code"}

Command: how much battery do I have
{"action": "BATTERY_STATUS", "data": null}

Command: turn up the volume
{"action": "VOLUME_SET", "data": "up"}

Command: search how to fix a segfault in c
{"action": "GOOGLE_SEARCH", "data": "how to fix segfault in c"}"""


def parse(command: str) -> dict:
    """
    Send command to qwen2.5:0.5b and return parsed intent dict.
    Falls back to UNKNOWN if model returns invalid JSON or times out.
    Model unloads from RAM after response (keep_alive=0).
    """
    log.info(f"LLM parsing: '{command}'")

    payload = {
        "model":      MODEL,
        "prompt":     f"Command: {command}",
        "system":     SYSTEM_PROMPT,
        "stream":     False,
        "keep_alive": 0,       # unload model from RAM immediately after response
        "options": {
            "temperature": 0,  # deterministic output
            "num_predict": 64, # JSON never needs more than 64 tokens
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=15          # max 15s on slow CPU
        )
        response.raise_for_status()

        raw = response.json().get("response", "").strip()
        log.info(f"LLM raw response: {raw}")

        # Strip markdown code fences if model added them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        intent = json.loads(raw)

        # Validate required fields
        if "action" not in intent:
            raise ValueError("No 'action' field in response")

        intent["mode"] = "llm"
        log.info(f"LLM intent: {intent}")
        return intent

    except requests.exceptions.ConnectionError:
        log.error("Ollama not running. Start with: ollama serve")
        return {"action": "UNKNOWN", "data": command, "mode": "llm",
                "error": "Ollama not running"}

    except requests.exceptions.Timeout:
        log.error("LLM timed out after 15s")
        return {"action": "UNKNOWN", "data": command, "mode": "llm",
                "error": "LLM timeout"}

    except (json.JSONDecodeError, ValueError) as e:
        log.error(f"LLM returned invalid JSON: {e} | raw: {raw}")
        return {"action": "UNKNOWN", "data": command, "mode": "llm",
                "error": f"Invalid JSON: {e}"}

    except Exception as e:
        log.error(f"LLM bridge unexpected error: {e}")
        return {"action": "UNKNOWN", "data": command, "mode": "llm",
                "error": str(e)}


def is_ollama_running() -> bool:
    """Quick health check before attempting LLM parse."""
    try:
        r = requests.get("http://127.0.0.1:11434/", timeout=2)
        return r.status_code == 200
    except Exception:
        return False
