#!/usr/bin/env python3
"""
skills/browser_skill.py - KENWAY Browser Skill

YouTube : Selenium + detach=True (confirmed working)
Spotify : Ctrl+K to open search (Linux Spotify shortcut)
          Falls back to clicking search bar by coords if Ctrl+K fails
"""

import subprocess
import logging
import urllib.parse
import time

log = logging.getLogger("kenway.browser_skill")

CHROME_BINARY     = "/usr/bin/google-chrome"
CHROMEDRIVER_PATH = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _xdg_open(url: str):
    subprocess.Popen(["xdg-open", url],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    log.info(f"xdg-open: {url}")


def _make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.binary_location = CHROME_BINARY
    opts.add_experimental_option("detach", True)   # Chrome stays alive after script
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
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    )
    return driver


# ---------------------------------------------------------------------------
# xdotool helpers — all target explicit window ID
# ---------------------------------------------------------------------------

def _xdo_key(wid: str, key: str, delay: float = 0.5):
    subprocess.run(
        ["xdotool", "key", "--window", wid, "--clearmodifiers", key],
        capture_output=True
    )
    time.sleep(delay)


def _xdo_type(wid: str, text: str, delay: float = 0.5):
    subprocess.run(
        ["xdotool", "type", "--window", wid,
         "--clearmodifiers", "--delay", "60", text],
        capture_output=True
    )
    time.sleep(delay)


def _xdo_click(wid: str, x: int, y: int, delay: float = 0.5):
    """Mouse click at (x,y) relative to window top-left."""
    subprocess.run(
        ["xdotool", "mousemove", "--window", wid, str(x), str(y)],
        capture_output=True
    )
    time.sleep(0.1)
    subprocess.run(
        ["xdotool", "click", "--window", wid, "1"],
        capture_output=True
    )
    time.sleep(delay)


def _get_spotify_wid() -> str | None:
    result = subprocess.run(
        ["xdotool", "search", "--name", "Spotify"],
        capture_output=True, text=True, timeout=5
    )
    ids = result.stdout.strip().splitlines()
    # Prefer the larger window ID — Spotify's main window is usually last
    return ids[-1] if ids else None


def _focus_wid(wid: str, delay: float = 0.5):
    subprocess.run(["xdotool", "windowactivate", "--sync", wid], capture_output=True)
    subprocess.run(["xdotool", "windowraise", wid], capture_output=True)
    time.sleep(delay)


def _get_window_geometry(wid: str) -> dict:
    """Returns {'x','y','width','height'} of the window."""
    result = subprocess.run(
        ["xdotool", "getwindowgeometry", wid],
        capture_output=True, text=True
    )
    geo = {"x": 0, "y": 0, "width": 1280, "height": 800}
    for line in result.stdout.splitlines():
        line = line.strip()
        if "Position" in line:
            # Position: 0,27 (screen: 0,27)
            pos = line.split(":")[1].split("(")[0].strip()
            geo["x"], geo["y"] = map(int, pos.split(","))
        if "Geometry" in line:
            # Geometry: 1280x800
            size = line.split(":")[1].strip()
            geo["width"], geo["height"] = map(int, size.split("x"))
    return geo


# ---------------------------------------------------------------------------
# YOUTUBE  (confirmed working — do not change)
# ---------------------------------------------------------------------------

def play_on_youtube(query: str) -> str:
    encoded    = urllib.parse.quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"

    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        log.info(f"YouTube Selenium: {query}")
        driver = _make_driver()
        driver.get(search_url)

        wait   = WebDriverWait(driver, 15)
        videos = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "ytd-video-renderer a#video-title")
            )
        )

        if not videos:
            raise Exception("No video results found")

        first = videos[0]
        title = first.get_attribute("title") or query
        driver.execute_script("arguments[0].scrollIntoView(true);", first)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", first)
        log.info(f"YouTube clicked: {title}")
        # detach=True — Chrome stays alive, no driver.quit()
        return f"Now playing {title} on YouTube."

    except Exception as e:
        log.warning(f"Selenium YouTube failed: {e} — falling back to xdg-open")
        _xdg_open(search_url)
        return f"Opened YouTube search for {query}."


# ---------------------------------------------------------------------------
# SPOTIFY
# Strategy:
#   1. Launch Spotify if needed, wait for window
#   2. windowactivate (more reliable than windowfocus on some WMs)
#   3. Try Ctrl+K  (native Spotify Linux search shortcut)
#   4. If that doesn't work, click the search bar by position
#   5. Type query, Enter, wait 3.5s for results
#   6. Tab x2 to reach first song row, Enter to play
# ---------------------------------------------------------------------------

# How many Tabs after search results load to reach the first playable song row.
# Confirmed value from debug: adjust if Spotify opens wrong item.
SPOTIFY_TAB_COUNT = 2

# Approximate X position of search bar as fraction of window width.
# Spotify search bar sits roughly at 50% width, 6% from top.
SEARCH_BAR_X_FRAC = 0.50
SEARCH_BAR_Y_FRAC = 0.06


def play_on_spotify(query: str) -> str:
    try:
        # 1. Launch if not running
        is_running = subprocess.run(
            ["pgrep", "-x", "spotify"], capture_output=True
        ).returncode == 0

        if not is_running:
            subprocess.Popen(["spotify"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            log.info("Spotify launched — waiting 9s")
            time.sleep(9)
        else:
            time.sleep(0.5)

        # 2. Get window ID (last ID = main window)
        wid = None
        for _ in range(12):
            wid = _get_spotify_wid()
            if wid:
                break
            time.sleep(0.5)

        if not wid:
            raise Exception("Spotify window not found")

        log.info(f"Spotify WID: {wid}")

        # 3. Activate + raise window
        _focus_wid(wid, delay=0.8)

        # 4. Open search — try Ctrl+K first (Linux Spotify shortcut)
        #    windowactivate ensures it's the active window before the keypress
        log.info("Sending Ctrl+K to open search")
        _xdo_key(wid, "ctrl+k", delay=1.0)

        # 5. Fallback: if Ctrl+K didn't open search, click the search bar by coords
        #    Search bar is at ~50% width, ~6% height of window
        geo = _get_window_geometry(wid)
        sx  = int(geo["width"]  * SEARCH_BAR_X_FRAC)
        sy  = int(geo["height"] * SEARCH_BAR_Y_FRAC)
        log.info(f"Clicking search bar at ({sx}, {sy}) as fallback")
        _xdo_click(wid, sx, sy, delay=0.6)

        # 6. Clear any existing text + type query
        _xdo_key(wid, "ctrl+a", delay=0.2)
        _xdo_type(wid, query, delay=0.5)

        # 7. Submit + wait for results to render
        _xdo_key(wid, "Return", delay=3.5)

        # 8. Re-activate window (results may have shifted focus)
        _focus_wid(wid, delay=0.5)

        # 9. Tab to first song row
        for i in range(SPOTIFY_TAB_COUNT):
            _xdo_key(wid, "Tab", delay=0.4)
            log.info(f"Tab {i+1}/{SPOTIFY_TAB_COUNT}")

        # 10. Play
        _xdo_key(wid, "Return", delay=0.5)

        log.info(f"Spotify play dispatched: {query}")
        return f"Playing {query} on Spotify."

    except Exception as e:
        log.error(f"Spotify error: {e}")
        encoded = urllib.parse.quote_plus(query)
        _xdg_open(f"spotify:search:{encoded}")
        return f"Opened Spotify search for {query}."


# ---------------------------------------------------------------------------
# GOOGLE / URL
# ---------------------------------------------------------------------------

def search_google(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    _xdg_open(f"https://www.google.com/search?q={encoded}")
    return f"Searching Google for {query}."


def open_url_direct(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    _xdg_open(url)
    return f"Opening {url}."
