#!/usr/bin/env python3
"""
skills/browser_skill.py - KENWAY Browser Skill

YouTube : Selenium + detach=True (confirmed working)
Spotify : Click search bar at (683,42) to focus,
          then xdotool type WITHOUT --window (types to active focus),
          then Enter -> wait -> Tab to result -> Enter to play
"""

import subprocess
import logging
import urllib.parse
import time

log = logging.getLogger("kenway.browser_skill")

CHROME_BINARY     = "/usr/bin/google-chrome"
CHROMEDRIVER_PATH = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"

# Confirmed from debug: search bar lives at (683, 42) in Spotify window
# Window geometry: 1366x714, position 0,82
SPOTIFY_SEARCH_X = 683
SPOTIFY_SEARCH_Y = 42


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _xdg_open(url: str):
    subprocess.Popen(["xdg-open", url],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    log.info(f"xdg-open: {url}")


def _run(cmd: list) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()


def _make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.binary_location = CHROME_BINARY
    opts.add_experimental_option("detach", True)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--start-maximized")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    )
    return driver


# ---------------------------------------------------------------------------
# Spotify xdotool helpers
# ---------------------------------------------------------------------------

def _get_spotify_wid() -> str | None:
    out = _run(["xdotool", "search", "--name", "Spotify"])
    ids = out.splitlines()
    return ids[-1] if ids else None  # last ID = main UI window


def _activate_wid(wid: str, delay: float = 0.6):
    subprocess.run(["xdotool", "windowactivate", "--sync", wid], capture_output=True)
    subprocess.run(["xdotool", "windowraise", wid], capture_output=True)
    time.sleep(delay)


def _click_abs(screen_x: int, screen_y: int, delay: float = 0.4):
    """Click at absolute SCREEN coordinates (not window-relative)."""
    subprocess.run(["xdotool", "mousemove", str(screen_x), str(screen_y)],
                   capture_output=True)
    time.sleep(0.1)
    subprocess.run(["xdotool", "click", "1"], capture_output=True)
    time.sleep(delay)


def _type_active(text: str, delay: float = 0.5):
    """
    Type into whichever window currently has keyboard focus.
    Do NOT pass --window here — that's what broke typing before.
    """
    subprocess.run(
        ["xdotool", "type", "--clearmodifiers", "--delay", "60", text],
        capture_output=True
    )
    time.sleep(delay)


def _key_active(key: str, delay: float = 0.4):
    """Send key to currently focused window."""
    subprocess.run(["xdotool", "key", "--clearmodifiers", key],
                   capture_output=True)
    time.sleep(delay)


def _get_window_pos(wid: str) -> tuple[int, int]:
    """Get absolute screen position (x, y) of window top-left."""
    out = _run(["xdotool", "getwindowgeometry", wid])
    wx, wy = 0, 82  # fallback from debug: Position 0,82
    for line in out.splitlines():
        if "Position" in line:
            pos = line.split(":")[1].split("(")[0].strip()
            wx, wy = map(int, pos.split(","))
    return wx, wy


# ---------------------------------------------------------------------------
# YOUTUBE  (confirmed working - unchanged)
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
            raise Exception("No video results")

        first = videos[0]
        title = first.get_attribute("title") or query
        driver.execute_script("arguments[0].scrollIntoView(true);", first)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", first)
        log.info(f"YouTube clicked: {title}")
        return f"Now playing {title} on YouTube."

    except Exception as e:
        log.warning(f"Selenium YouTube failed: {e}")
        _xdg_open(search_url)
        return f"Opened YouTube search for {query}."


# ---------------------------------------------------------------------------
# SPOTIFY
#
# Confirmed working approach from debug session:
#   - Click at absolute screen coords (win_x + 683, win_y + 42) to focus search
#   - xdotool type WITHOUT --window (types to active focused element)
#   - Enter to search, wait 3.5s
#   - Tab x1 to reach first result, Enter to play
#
# SPOTIFY_TAB_COUNT: start at 1. If it opens artist/album instead of
# playing a song, increase by 1 and retry.
# ---------------------------------------------------------------------------

SPOTIFY_TAB_COUNT = 1


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
            log.info("Spotify launched, waiting 9s")
            time.sleep(9)
        else:
            time.sleep(0.5)

        # 2. Get main window ID
        wid = None
        for _ in range(12):
            wid = _get_spotify_wid()
            if wid:
                break
            time.sleep(0.5)

        if not wid:
            raise Exception("Spotify window not found")

        log.info(f"Spotify WID: {wid}")

        # 3. Bring Spotify to foreground
        _activate_wid(wid, delay=0.8)

        # 4. Get absolute screen position of Spotify window
        win_x, win_y = _get_window_pos(wid)
        abs_x = win_x + SPOTIFY_SEARCH_X
        abs_y = win_y + SPOTIFY_SEARCH_Y
        log.info(f"Clicking search bar at screen coords ({abs_x}, {abs_y})")

        # 5. Click the search bar (absolute screen coords)
        _click_abs(abs_x, abs_y, delay=0.6)

        # 6. Select all + type query (no --window flag!)
        _key_active("ctrl+a", delay=0.2)
        _type_active(query, delay=0.5)
        log.info(f"Typed: {query}")

        # 7. Submit and wait for results
        _key_active("Return", delay=3.5)

        # 8. Re-activate Spotify (results load may shift focus)
        _activate_wid(wid, delay=0.5)

        # 9. Tab to first song row
        for i in range(SPOTIFY_TAB_COUNT):
            _key_active("Tab", delay=0.4)
            log.info(f"Tab {i+1}/{SPOTIFY_TAB_COUNT}")

        # 10. Play
        _key_active("Return", delay=0.5)

        log.info(f"Spotify play dispatched: {query}")
        return f"Playing {query} on Spotify."

    except Exception as e:
        log.error(f"Spotify error: {e}")
        # Nuclear fallback: open Spotify search URI in default handler
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
