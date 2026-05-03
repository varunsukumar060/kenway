#!/usr/bin/env python3
"""
skills/media_skill.py — Media Controls (VLC, Spotify)
"""

import subprocess
import logging
from core.voice import speak

log = logging.getLogger("kenway.media_skill")


def play_on_spotify(query: str):
    """Open Spotify (if installed) — deep search link."""
    speak(f"Opening Spotify for {query}.")
    uri = f"spotify:search:{query.replace(' ', '%20')}"
    try:
        subprocess.Popen(["xdg-open", uri])
        log.info(f"Spotify opened for: {query}")
    except Exception as e:
        speak("Could not open Spotify.")
        log.error(f"Spotify error: {e}")


def vlc_play(path: str):
    """Play a file in VLC."""
    speak(f"Playing {path} in VLC.")
    try:
        subprocess.Popen(["vlc", path])
        log.info(f"VLC playing: {path}")
    except Exception as e:
        speak("VLC is not available.")
        log.error(f"VLC error: {e}")


def media_pause_play():
    """Toggle pause/play using playerctl (works with most media players)."""
    try:
        subprocess.run(["playerctl", "play-pause"])
        speak("Toggled media playback.")
        log.info("Media toggled.")
    except FileNotFoundError:
        # Fallback: XF86 key
        subprocess.run(["xdotool", "key", "XF86AudioPlay"])
    except Exception as e:
        log.error(f"Media toggle error: {e}")


def media_next():
    try:
        subprocess.run(["playerctl", "next"])
        speak("Next track.")
    except Exception as e:
        log.error(f"Media next error: {e}")


def media_previous():
    try:
        subprocess.run(["playerctl", "previous"])
        speak("Previous track.")
    except Exception as e:
        log.error(f"Media previous error: {e}")
