#!/usr/bin/env python3
"""
skills/browser_skill.py — KENWAY Browser Skill
Handles YouTube playback, Google search, and direct URL opens.
Uses subprocess to open URLs in the default browser — no Selenium needed for Phase 2.
"""

import subprocess
import logging
import urllib.parse
import yaml
import os

log = logging.getLogger("kenway.browser_skill")


def _cfg() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        with open(path) as f:
            return yaml.safe_load(f).get("browser", {})
    except Exception:
        return {}


def _open_url(url: str):
    """Open URL in default browser using xdg-open."""
    try:
        subprocess.Popen(["xdg-open", url],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        log.info(f"Opened URL: {url}")
    except Exception as e:
        log.error(f"Failed to open URL {url}: {e}")


def play_on_youtube(query: str):
    """
    Open YouTube search for the query in default browser.
    The browser opens the search results page — first result is at top.
    """
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    log.info(f"YouTube search: {query}")
    _open_url(url)
    return f"Searching YouTube for {query}."


def search_google(query: str):
    """Open Google search for the query."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    log.info(f"Google search: {query}")
    _open_url(url)
    return f"Searching Google for {query}."


def open_url_direct(url: str):
    """Open a raw URL directly."""
    if not url.startswith("http"):
        url = "https://" + url
    log.info(f"Opening URL: {url}")
    _open_url(url)
    return f"Opening {url}."
