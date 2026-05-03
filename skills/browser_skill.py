#!/usr/bin/env python3
"""
skills/browser_skill.py — KENWAY Browser Skill
Uses google-chrome (147) + snap chromedriver (147) — exact version match.
Spotify: Tab navigation to first song result.
"""

import subprocess
import logging
import urllib.parse
import time
import os

log = logging.getLogger("kenway.browser_skill")

# ── Exact version-matched pair on Varun's system ────────────────────────────────
CHROME_BINARY     = "/usr/bin/google-chrome"
CHROMEDRIVER_PATH = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _xdg_open(url: str):
    subprocess.Popen(["xdg-open", url],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    log.info(f"xdg-open fallback: {url}")


def _make_driver():
    """
    Build a Chrome WebDriver using:
      - Binary : /usr/bin/google-chrome  (Chrome 147)
      - Driver : snap chromedriver 147   (exact match)
    Both paths are verified on Varun's system.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.binary_location = CHROME_BINARY
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1280,800")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ──────────────────────────────────────────────────────────────────────────────
# YOUTUBE
# ──────────────────────────────────────────────────────────────────────────────

def play_on_youtube(query: str) -> str:
    """
    Search YouTube and auto-click the first non-ad video.
    Falls back to xdg-open (Firefox) if Selenium fails.
    """
    encoded   = urllib.parse.quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"

    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        log.info(f"YouTube Selenium: {query}")
        driver = _make_driver()
        driver.get(search_url)

        wait = WebDriverWait(driver, 12)
        video_links = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "ytd-video-renderer a#video-title")
            )
        )

        if video_links:
            first = video_links[0]
            title = first.get_attribute("title") or query
            driver.execute_script("arguments[0].click();", first)
            log.info(f"YouTube clicked: {title}")
            # Don't quit — video is playing in this window
            return f"Now playing {title} on YouTube."
        else:
            driver.quit()
            raise Exception("No video elements found on page")

    except Exception as e:
        log.warning(f"Selenium YouTube failed: {e} — falling back to xdg-open")
        _xdg_open(search_url)
        return f"Opened YouTube search for {query}. Click a result to play."


# ──────────────────────────────────────────────────────────────────────────────
# SPOTIFY
# ──────────────────────────────────────────────────────────────────────────────

def _xdo(args: list, delay: float = 0.3):
    subprocess.run(["xdotool"] + args, capture_output=True)
    time.sleep(delay)


def _focus_spotify() -> bool:
    result = subprocess.run(
        ["xdotool", "search", "--name", "Spotify",
         "windowfocus", "--sync", "windowraise"],
        capture_output=True, timeout=6
    )
    return result.returncode == 0


def play_on_spotify(query: str) -> str:
    """
    Launch Spotify, search, Tab to first song row, Enter to play.
    Tab count explanation:
      Tab 1-2 : skip past top nav (Home / Search / Library)
      Tab 3   : skip filter pills row (All / Songs / Artists...)
      Tab 4   : land on FIRST song result row
      Enter   : play it
    If Spotify layout varies, increase tabs to 5.
    """
    try:
        # 1. Launch if not running
        is_running = subprocess.run(
            ["pgrep", "-x", "spotify"], capture_output=True
        ).returncode == 0

        if not is_running:
            subprocess.Popen(["spotify"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            log.info("Spotify launched — waiting 7s")
            time.sleep(7)
        else:
            time.sleep(0.5)

        # 2. Focus window
        if not _focus_spotify():
            time.sleep(2)
            _focus_spotify()
        time.sleep(0.5)

        # 3. Focus search bar
        _xdo(["key", "ctrl+l"], delay=0.6)

        # 4. Clear + type query (50ms per char = reliable even for Tamil text)
        _xdo(["key", "ctrl+a"], delay=0.2)
        _xdo(["type", "--clearmodifiers", "--delay", "50", query], delay=0.4)

        # 5. Submit search, wait for results
        _xdo(["key", "Return"], delay=2.5)

        # 6. Tab to first song result (4 tabs skips nav + filter pills)
        for _ in range(4):
            _xdo(["key", "Tab"], delay=0.15)

        # 7. Play
        _xdo(["key", "Return"], delay=0.5)

        log.info(f"Spotify search+play: {query}")
        return f"Playing {query} on Spotify."

    except Exception as e:
        log.error(f"Spotify xdotool error: {e}")
        encoded = urllib.parse.quote_plus(query)
        _xdg_open(f"spotify:search:{encoded}")
        return f"Opened Spotify search for {query}."


# ──────────────────────────────────────────────────────────────────────────────
# GOOGLE / URL
# ──────────────────────────────────────────────────────────────────────────────

def search_google(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    _xdg_open(f"https://www.google.com/search?q={encoded}")
    return f"Searching Google for {query}."


def open_url_direct(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    _xdg_open(url)
    return f"Opening {url}."
