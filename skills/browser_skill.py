#!/usr/bin/env python3
"""
skills/browser_skill.py — KENWAY Browser Skill

Fixes:
  YouTube : Chrome stays alive after click (detach=True + no driver.quit())
  Spotify : Longer delays, window-ID locking, robust focus before each xdotool step
"""

import subprocess
import logging
import urllib.parse
import time

log = logging.getLogger("kenway.browser_skill")

CHROME_BINARY     = "/usr/bin/google-chrome"
CHROMEDRIVER_PATH = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _xdg_open(url: str):
    subprocess.Popen(["xdg-open", url],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    log.info(f"xdg-open fallback: {url}")


def _make_driver():
    """
    Build Chrome WebDriver with detach=True so the browser window
    STAYS OPEN after Python exits / driver object is garbage collected.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.binary_location = CHROME_BINARY

    # ✔ KEY FIX: detach keeps Chrome alive even after driver reference is lost
    opts.add_experimental_option("detach", True)

    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1280,800")
    opts.add_argument("--start-maximized")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ──────────────────────────────────────────────────────────────
# YOUTUBE
# ──────────────────────────────────────────────────────────────

def play_on_youtube(query: str) -> str:
    """
    Open YouTube search, click first non-ad video.
    Chrome stays open (detach=True) — video keeps playing.
    Falls back to xdg-open (Firefox) if Selenium fails.
    """
    encoded    = urllib.parse.quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"

    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        log.info(f"YouTube Selenium: {query}")
        driver = _make_driver()
        driver.get(search_url)

        wait = WebDriverWait(driver, 15)

        # Wait for at least one real video result
        video_links = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "ytd-video-renderer a#video-title")
            )
        )

        if not video_links:
            raise Exception("No video results found")

        first = video_links[0]
        title = first.get_attribute("title") or query

        # Scroll into view then JS click — more reliable than .click()
        driver.execute_script("arguments[0].scrollIntoView(true);", first)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", first)

        log.info(f"YouTube clicked: {title}")
        # ✔ Do NOT call driver.quit() — detach=True keeps Chrome alive
        return f"Now playing {title} on YouTube."

    except Exception as e:
        log.warning(f"Selenium YouTube failed: {e} — falling back to xdg-open")
        _xdg_open(search_url)
        return f"Opened YouTube search for {query}. Click a result to play."


# ──────────────────────────────────────────────────────────────
# SPOTIFY
# ──────────────────────────────────────────────────────────────

def _get_spotify_wid() -> str | None:
    """
    Get the X11 window ID of the Spotify window.
    Returns window ID string or None if not found.
    """
    result = subprocess.run(
        ["xdotool", "search", "--name", "Spotify"],
        capture_output=True, text=True, timeout=5
    )
    ids = result.stdout.strip().splitlines()
    return ids[0] if ids else None


def _focus_wid(wid: str):
    """Focus and raise a window by its X11 ID."""
    subprocess.run(["xdotool", "windowfocus", "--sync", wid], capture_output=True)
    subprocess.run(["xdotool", "windowraise", wid], capture_output=True)
    time.sleep(0.4)


def _xdo_key(wid: str, key: str, delay: float = 0.5):
    """Send a key to a specific window ID — doesn't rely on active focus."""
    subprocess.run(
        ["xdotool", "key", "--window", wid, "--clearmodifiers", key],
        capture_output=True
    )
    time.sleep(delay)


def _xdo_type(wid: str, text: str, delay: float = 0.5):
    """Type text into a specific window ID."""
    subprocess.run(
        ["xdotool", "type", "--window", wid,
         "--clearmodifiers", "--delay", "60", text],
        capture_output=True
    )
    time.sleep(delay)


def play_on_spotify(query: str) -> str:
    """
    Launch Spotify, search, and play the first song result.

    xdotool now targets a specific window ID (--window WID) so it works
    even if another window steals focus during the sequence.

    Tab navigation after search:
      Spotify Desktop (Linux) keyboard flow after pressing Enter on search:
        Focus lands on filter row (All / Songs / Artists / Albums)
        Tab x1  → skip to first result card
        Enter   → play / open it
    If it opens an artist/album instead of playing: change TAB_COUNT to 2.
    """
    TAB_COUNT = 1   # tabs needed after search results load to reach first song

    try:
        # ── 1. Launch Spotify if not running ────────────────────────────
        is_running = subprocess.run(
            ["pgrep", "-x", "spotify"], capture_output=True
        ).returncode == 0

        if not is_running:
            subprocess.Popen(["spotify"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            log.info("Spotify launched — waiting 8s for full load")
            time.sleep(8)   # longer wait for cold start
        else:
            time.sleep(0.5)

        # ── 2. Get window ID — retry up to 5s ─────────────────────────────
        wid = None
        for attempt in range(10):
            wid = _get_spotify_wid()
            if wid:
                break
            log.info(f"Waiting for Spotify window... attempt {attempt+1}")
            time.sleep(0.5)

        if not wid:
            raise Exception("Spotify window not found after 5s")

        log.info(f"Spotify window ID: {wid}")

        # ── 3. Focus Spotify ─────────────────────────────────────────────
        _focus_wid(wid)

        # ── 4. Open search with Ctrl+L ──────────────────────────────────
        _xdo_key(wid, "ctrl+l", delay=0.8)

        # ── 5. Select all existing text + type new query ──────────────────
        _xdo_key(wid, "ctrl+a", delay=0.3)
        _xdo_type(wid, query, delay=0.5)

        # ── 6. Submit search, wait for results UI to render ────────────────
        _xdo_key(wid, "Return", delay=3.0)   # 3s — enough for results to paint

        # Re-focus in case something stole focus during the wait
        _focus_wid(wid)

        # ── 7. Tab to first song result ────────────────────────────────
        for i in range(TAB_COUNT):
            _xdo_key(wid, "Tab", delay=0.4)
            log.info(f"Tab {i+1}/{TAB_COUNT}")

        # ── 8. Play ────────────────────────────────────────────────────
        _xdo_key(wid, "Return", delay=0.5)

        log.info(f"Spotify play dispatched: {query}")
        return f"Playing {query} on Spotify."

    except Exception as e:
        log.error(f"Spotify xdotool error: {e}")
        encoded = urllib.parse.quote_plus(query)
        _xdg_open(f"spotify:search:{encoded}")
        return f"Opened Spotify search for {query}."


# ──────────────────────────────────────────────────────────────
# GOOGLE / URL
# ──────────────────────────────────────────────────────────────

def search_google(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    _xdg_open(f"https://www.google.com/search?q={encoded}")
    return f"Searching Google for {query}."


def open_url_direct(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    _xdg_open(url)
    return f"Opening {url}."
