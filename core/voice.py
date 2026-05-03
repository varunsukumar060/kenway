#!/usr/bin/env python3
"""
core/voice.py — KENWAY Voice Output Engine
Uses pyttsx3 with espeak-ng backend (fully offline).
"""

import pyttsx3
import logging
import threading
import yaml
import os

log = logging.getLogger("kenway.voice")

# ── Load config ────────────────────────────────────────────────────────────────
def _load_voice_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f).get("voice", {})
    except Exception:
        return {"rate": 165, "volume": 0.9, "voice_index": 0}


# ── Engine init ────────────────────────────────────────────────────────────────
_engine = None
_lock = threading.Lock()


def _get_engine() -> pyttsx3.Engine:
    global _engine
    if _engine is None:
        cfg = _load_voice_config()
        _engine = pyttsx3.init()
        _engine.setProperty("rate", cfg.get("rate", 165))
        _engine.setProperty("volume", cfg.get("volume", 0.9))

        voices = _engine.getProperty("voices")
        idx = cfg.get("voice_index", 0)
        if voices and idx < len(voices):
            _engine.setProperty("voice", voices[idx].id)

        log.info(f"Voice engine initialized | rate={cfg.get('rate')} volume={cfg.get('volume')}")
    return _engine


# ── Public API ─────────────────────────────────────────────────────────────────
def speak(text: str):
    """
    Speak the given text aloud using offline TTS.
    Thread-safe — can be called from any thread.
    """
    def _speak():
        with _lock:
            try:
                engine = _get_engine()
                engine.say(text)
                engine.runAndWait()
                log.info(f"Spoke: {text}")
            except Exception as e:
                log.error(f"Voice engine error: {e}")

    threading.Thread(target=_speak, daemon=True).start()


def speak_blocking(text: str):
    """
    Speak and block until done. Use for critical messages.
    """
    with _lock:
        try:
            engine = _get_engine()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            log.error(f"Voice engine error: {e}")
