#!/usr/bin/env python3
"""
skills/browser_skill.py — KENWAY Browser Skill
Fixes:
  - YouTube: uses chromium-browser (not google-chrome) for Selenium
  - Spotify: Tab navigation to select + play first search result reliably
"""

import subprocess
import logging
import urllib.parse
import time
import shutil

log = logging.getLogger("kenway.browser_skill")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _xdg_open(url: str):
    subprocess.Popen(["xdg-open", url],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    log.info(f"xdg-open: {url}")


def _find_chromium() -> str:
    """
    Find the Chromium/Chrome binary on this system.
    Returns the binary path or raises FileNotFoundError.
    """
    candidates = [
        "chromium-browser",   # Ubuntu/Mint snap or apt
        "chromium",           # Arch / Fedora
        "google-chrome",      # Chrome stable
        "google-chrome-stable",
    ]
    for name in candidates:
        path = shutil.which(name)
        if path:
            log.info(f"Found browser binary: {path}")
            return path
    raise FileNotFoundError(
        "No Chromium/Chrome binary found. "
        "Install with: sudo apt install chromium-browser"
    )


def _make_driver():
    """
    Create a Selenium Chrome WebDriver pointing at Chromium.
    Uses selenium-manager to auto-download the matching chromedriver.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    binary = _find_chromium()

    opts = Options()
    opts.binary_location = binary
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1280,800")

    driver = webdriver.Chrome(options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ──────────────────────────────────────────────────────────────────────────────
# YOUTUBE
# ──────────────────────────────────────────────────────────────────────────────

def play_on_youtube(query: str) -> str:
    """
    Search YouTube and auto-click the first non-ad video result.
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

        wait = WebDriverWait(driver, 12)

        # Wait for video title links to appear
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
            return f"Now playing {title} on YouTube."
        else:
            driver.quit()
            raise Exception("No video elements found")

    except Exception as e:
        log.warning(f"Selenium YouTube failed: {e} — falling back to xdg-open")
        _xdg_open(search_url)
        return f"Opened YouTube search for {query}. Click a result to play."


# ──────────────────────────────────────────────────────────────────────────────
# SPOTIFY
# ──────────────────────────────────────────────────────────────────────────────

def _xdo(args: list, delay: float = 0.3):
    """Run an xdotool command and wait."""
    subprocess.run(["xdotool"] + args, capture_output=True)
    time.sleep(delay)


def _focus_spotify() -> bool:
    """Focus the Spotify window. Returns True if found."""
    result = subprocess.run(
        ["xdotool", "search", "--name", "Spotify",
         "windowfocus", "--sync", "windowraise"],
        capture_output=True, timeout=6
    )
    return result.returncode == 0


def play_on_spotify(query: str) -> str:
    """
    Launch Spotify (if needed), search for query, and play the first result.
    Strategy:
      1. Ctrl+L  — focus search bar
      2. Type query + Enter  — run search
      3. Wait for results
      4. Tab x2  — move focus into the results list (past filter chips)
      5. Enter   — open first result (song/album/artist)
      6. If it's a playlist/album: Space to start playback
    """
    try:
        # ── 1. Launch Spotify if not running ──────────────────────────────────
        is_running = subprocess.run(
            ["pgrep", "-x", "spotify"], capture_output=True
        ).returncode == 0

        if not is_running:
            subprocess.Popen(["spotify"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            log.info("Spotify launched — waiting 7s for load")
            time.sleep(7)
        else:
            time.sleep(0.5)

        # ── 2. Focus Spotify window ───────────────────────────────────────────
        focused = _focus_spotify()
        if not focused:
            # Try once more after a short wait
            time.sleep(2)
            _focus_spotify()
        time.sleep(0.5)

        # ── 3. Open search (Ctrl+L) ───────────────────────────────────────────
        _xdo(["key", "ctrl+l"], delay=0.6)

        # ── 4. Clear any existing text and type query ─────────────────────────
        _xdo(["key", "ctrl+a"], delay=0.2)
        _xdo(["type", "--clearmodifiers", "--delay", "50", query], delay=0.3)

        # ── 5. Submit search ──────────────────────────────────────────────────
        _xdo(["key", "Return"], delay=2.5)   # wait 2.5s for results to load

        # ── 6. Navigate to first song result ─────────────────────────────────
        # Spotify results: first few Tab presses skip past the filter pills
        # (All / Songs / Artists / Albums …) then land on the first track row.
        # Tab x4 reliably lands on the first "Songs" result in most layouts.
        for _ in range(4):
            _xdo(["key", "Tab"], delay=0.15)

        # ── 7. Press Enter to play the selected item ──────────────────────────
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
