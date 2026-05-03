#!/usr/bin/env python3
"""
core/voice.py — KENWAY Voice Output Engine
Uses pyttsx3 with espeak-ng backend (fully offline).
"""

import pyttsx3
import logging
import threading
import subprocess
import yaml
import os

log = logging.getLogger("kenway.voice")


def _load_voice_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f).get("voice", {})
    except Exception:
        return {"rate": 165, "volume": 0.9, "voice_index": 0}


_engine = None
_lock = threading.Lock()


def _get_engine() -> pyttsx3.Engine:
    global _engine
    if _engine is None:
        cfg = _load_voice_config()

        # Try pyttsx3 first, fallback to espeak-ng direct CLI
        try:
            _engine = pyttsx3.init()
            _engine.setProperty("rate", cfg.get("rate", 165))
            _engine.setProperty("volume", cfg.get("volume", 0.9))
            voices = _engine.getProperty("voices")
            idx = cfg.get("voice_index", 0)
            if voices and idx < len(voices):
                _engine.setProperty("voice", voices[idx].id)
            log.info("pyttsx3 engine initialized.")
        except Exception as e:
            log.warning(f"pyttsx3 init failed: {e}. Will use espeak-ng CLI fallback.")
            _engine = "espeak_fallback"

    return _engine


def _espeak_fallback(text: str):
    """Directly call espeak-ng binary — works even if libespeak.so.1 is missing."""
    try:
        subprocess.run(
            ["espeak-ng", "-s", "165", "-a", "90", text],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log.info(f"espeak-ng spoke: {text}")
    except FileNotFoundError:
        log.error("espeak-ng not found. Run: sudo apt install espeak-ng -y")
    except Exception as e:
        log.error(f"espeak-ng error: {e}")


def speak(text: str):
    """Speak text — non-blocking, runs in background thread."""
    def _speak():
        with _lock:
            try:
                engine = _get_engine()
                if engine == "espeak_fallback":
                    _espeak_fallback(text)
                else:
                    engine.say(text)
                    engine.runAndWait()
                log.info(f"Spoke: {text}")
            except Exception as e:
                log.warning(f"pyttsx3 error, trying espeak fallback: {e}")
                _espeak_fallback(text)

    threading.Thread(target=_speak, daemon=True).start()


def speak_blocking(text: str):
    """Speak and block until done."""
    with _lock:
        try:
            engine = _get_engine()
            if engine == "espeak_fallback":
                _espeak_fallback(text)
            else:
                engine.say(text)
                engine.runAndWait()
        except Exception as e:
            log.warning(f"pyttsx3 error, trying espeak fallback: {e}")
            _espeak_fallback(text)
