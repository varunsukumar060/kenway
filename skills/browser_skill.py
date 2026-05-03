#!/usr/bin/env python3
"""
skills/browser_skill.py — Browser Automation Skill
YouTube play, Google search, open URLs.
Uses Selenium with Chrome.
"""

import time
import logging
import subprocess
import yaml
import os
from core.voice import speak

log = logging.getLogger("kenway.browser_skill")


def _get_browser_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f).get("browser", {})
    except Exception:
        return {}


def _get_driver():
    """Initialize Selenium Chrome driver."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    cfg = _get_browser_config()
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    if cfg.get("headless", False):
        opts.add_argument("--headless=new")

    # Use system chromium-chromedriver
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=opts)
    driver.implicitly_wait(8)
    return driver


def play_on_youtube(query: str):
    """Search YouTube and auto-click the first video result."""
    speak(f"Searching YouTube for {query}.")
    log.info(f"YouTube play: {query}")

    try:
        from selenium.webdriver.common.by import By
        driver = _get_driver()
        cfg = _get_browser_config()
        search_url = cfg.get("youtube_base", "https://www.youtube.com/results?search_query=")
        driver.get(search_url + query.replace(" ", "+"))
        time.sleep(3)

        # Click first video result
        first_video = driver.find_element(
            By.CSS_SELECTOR, "ytd-video-renderer a#video-title"
        )
        title = first_video.get_attribute("title") or query
        first_video.click()
        speak(f"Now playing {title}.")
        log.info(f"Playing YouTube video: {title}")

    except Exception as e:
        speak(f"Could not play {query} on YouTube.")
        log.error(f"YouTube play error: {e}")
        # Fallback: open search page in default browser
        fallback_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        subprocess.Popen(["xdg-open", fallback_url])
        speak("Opened YouTube search as fallback.")


def search_youtube(query: str):
    """Open YouTube search results (without auto-clicking)."""
    speak(f"Opening YouTube search for {query}.")
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    subprocess.Popen(["xdg-open", url])
    log.info(f"YouTube search: {query}")


def search_google(query: str):
    """Open Google search."""
    speak(f"Searching Google for {query}.")
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    subprocess.Popen(["xdg-open", url])
    log.info(f"Google search: {query}")


def open_url(url: str):
    """Open a URL in the default browser."""
    if not url.startswith("http"):
        url = "https://" + url
    speak(f"Opening {url}.")
    subprocess.Popen(["xdg-open", url])
    log.info(f"Opened URL: {url}")
