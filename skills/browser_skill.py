#!/usr/bin/env python3
"""
skills/browser_skill.py — KENWAY Browser Skill (Phase 3 upgrade)
YouTube: Selenium auto-clicks first video result.
Spotify: Opens app and uses xdotool to trigger search + play.
Fallback: xdg-open if Selenium fails for any reason.
"""

import subprocess
import logging
import urllib.parse
import time
import os

log = logging.getLogger("kenway.browser_skill")


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _xdg_open(url: str):
    """Simple fallback — open URL in default browser."""
    subprocess.Popen(["xdg-open", url],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    log.info(f"xdg-open: {url}")


def _make_driver():
    """
    Create a Chrome WebDriver using Selenium Manager (built into Selenium 4.21).
    Selenium Manager auto-downloads the correct chromedriver for Chrome 147.
    No manual chromedriver installation needed.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1280,800")

    # Let Selenium Manager pick the right driver automatically
    driver = webdriver.Chrome(options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ──────────────────────────────────────────────────────────────
# YOUTUBE
# ──────────────────────────────────────────────────────────────

def play_on_youtube(query: str) -> str:
    """
    Open YouTube, search for query, auto-click the first non-ad video.
    Falls back to xdg-open if Selenium fails.
    """
    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"

    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        log.info(f"YouTube Selenium: {query}")
        driver = _make_driver()
        driver.get(search_url)

        # Wait for video results to load (up to 10s)
        wait = WebDriverWait(driver, 10)

        # Find all video title links — skip ads (they have different structure)
        video_links = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "ytd-video-renderer a#video-title")
            )
        )

        # Click the first real video result
        if video_links:
            first = video_links[0]
            title = first.get_attribute("title") or query
            driver.execute_script("arguments[0].click();", first)
            log.info(f"YouTube clicked: {title}")
            # Keep browser open — don't quit driver, video is playing
            return f"Now playing {title} on YouTube."
        else:
            driver.quit()
            raise Exception("No video elements found")

    except Exception as e:
        log.warning(f"Selenium YouTube failed: {e} — falling back to xdg-open")
        _xdg_open(search_url)
        return f"Opened YouTube search for {query}. Click a result to play."


# ──────────────────────────────────────────────────────────────
# SPOTIFY
# ──────────────────────────────────────────────────────────────

def play_on_spotify(query: str) -> str:
    """
    Launch Spotify, wait for it to load, then use xdotool to:
    1. Focus the Spotify window
    2. Press Ctrl+L to open search
    3. Type the query
    4. Press Enter to search
    5. Wait and press Enter again to play first result
    """
    try:
        # Launch Spotify if not running
        is_running = subprocess.run(
            ["pgrep", "-x", "spotify"],
            capture_output=True
        ).returncode == 0

        if not is_running:
            subprocess.Popen(["spotify"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            log.info("Spotify launched, waiting for it to load...")
            time.sleep(6)  # Give Spotify time to fully start
        else:
            time.sleep(1)

        # Focus Spotify window
        subprocess.run(
            ["xdotool", "search", "--name", "Spotify", "windowfocus", "--sync"],
            capture_output=True, timeout=5
        )
        time.sleep(0.5)

        # Ctrl+L = focus search bar in Spotify
        subprocess.run(["xdotool", "key", "ctrl+l"], capture_output=True)
        time.sleep(0.5)

        # Type the search query
        subprocess.run(["xdotool", "type", "--clearmodifiers", query],
                       capture_output=True)
        time.sleep(0.3)

        # Press Enter to search
        subprocess.run(["xdotool", "key", "Return"], capture_output=True)
        time.sleep(2)

        # Press Enter again to play first result
        subprocess.run(["xdotool", "key", "Return"], capture_output=True)

        log.info(f"Spotify search+play: {query}")
        return f"Searching Spotify for {query} and playing."

    except Exception as e:
        log.error(f"Spotify xdotool error: {e}")
        # Fallback: open Spotify search via URI
        encoded = urllib.parse.quote_plus(query)
        _xdg_open(f"spotify:search:{encoded}")
        return f"Opened Spotify search for {query}."


# ──────────────────────────────────────────────────────────────
# GOOGLE / URL
# ──────────────────────────────────────────────────────────────

def search_google(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    _xdg_open(url)
    log.info(f"Google search: {query}")
    return f"Searching Google for {query}."


def open_url_direct(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    _xdg_open(url)
    log.info(f"Opening URL: {url}")
    return f"Opening {url}."
