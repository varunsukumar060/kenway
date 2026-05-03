#!/usr/bin/env python3
"""
skills/browser_skill.py - KENWAY Browser Skill

Status (confirmed working on Varun's system - 2026-05-03):
  YouTube : Selenium + detach=True. Chrome stays alive, video plays. ✅
  Spotify : Ctrl+K -> type (no pause, no --window) -> Enter -> Tab x1 -> play ✅

Chrome/Driver:
  Binary  : /usr/bin/google-chrome  (Chrome 147)
  Driver  : /snap/chromium/current/usr/lib/chromium-browser/chromedriver (147)

Spotify xdotool sequence:
  windowactivate -> Ctrl+K (0.8s) -> ctrl+a -> type -> Return -> wait 3.5s
  -> windowactivate -> Tab x1 -> Return
  CRITICAL: Zero input() pauses between activate and type.
            Terminal input() steals focus and breaks typing.
"""

import subprocess
import logging
import urllib.parse
import time

log = logging.getLogger("kenway.browser_skill")

CHROME_BINARY     = "/usr/bin/google-chrome"
CHROMEDRIVER_PATH = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"

# Confirmed from debug v5 on Varun's system: Tab x1 reaches first song row.
SPOTIFY_TAB_COUNT = 1


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _xdg_open(url: str):
    subprocess.Popen(["xdg-open", url],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    log.info(f"xdg-open: {url}")


def _run(cmd: list) -> str:
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


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
    opts.add_argument("--start-maximized")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    )
    return driver


# ---------------------------------------------------------------------------
# Spotify helpers
# ---------------------------------------------------------------------------

def _get_spotify_wid() -> str | None:
    out = _run(["xdotool", "search", "--name", "Spotify"])
    ids = out.splitlines()
    return ids[-1] if ids else None   # last ID = Spotify main UI window


def _activate_spotify(wid: str, delay: float = 0.6):
    subprocess.run(["xdotool", "windowactivate", "--sync", wid], capture_output=True)
    subprocess.run(["xdotool", "windowraise", wid], capture_output=True)
    time.sleep(delay)


# ---------------------------------------------------------------------------
# YOUTUBE
# ---------------------------------------------------------------------------

def play_on_youtube(query: str) -> str:
    """
    Search YouTube and auto-click first video result.
    Chrome stays open (detach=True) so video keeps playing.
    Falls back to xdg-open if Selenium fails.
    """
    encoded    = urllib.parse.quote_plus(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"

    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        log.info(f"YouTube: searching for '{query}'")
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

        log.info(f"YouTube: playing '{title}'")
        # detach=True — do NOT call driver.quit(), Chrome stays alive
        return f"Now playing {title} on YouTube."

    except Exception as e:
        log.warning(f"YouTube Selenium failed ({e}), falling back to xdg-open")
        _xdg_open(search_url)
        return f"Opened YouTube search for {query}."


# ---------------------------------------------------------------------------
# SPOTIFY
# ---------------------------------------------------------------------------

def play_on_spotify(query: str) -> str:
    """
    Search and play on Spotify Desktop (Linux).

    Sequence (confirmed working, do not reorder):
      1. Launch Spotify if not running, wait 9s for cold start
      2. Get main window ID (last ID from xdotool search)
      3. windowactivate --sync + windowraise  (bring to foreground)
      4. Ctrl+K  (open/focus search bar) + 0.8s wait
      5. Ctrl+A  (clear existing text)
      6. xdotool type (no --window!) — types to active focus = search bar
      7. Return  (submit search)
      8. 3.5s wait for results to load
      9. windowactivate again (re-grab focus after results render)
      10. Tab x1  (move to first song row)
      11. Return  (play)
    """
    try:
        # 1. Launch if needed
        is_running = subprocess.run(
            ["pgrep", "-x", "spotify"], capture_output=True
        ).returncode == 0

        if not is_running:
            subprocess.Popen(["spotify"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            log.info("Spotify cold start, waiting 9s")
            time.sleep(9)
        else:
            time.sleep(0.3)

        # 2. Get window ID
        wid = None
        for _ in range(12):
            wid = _get_spotify_wid()
            if wid:
                break
            time.sleep(0.5)

        if not wid:
            raise Exception("Spotify window not found after 6s")

        log.info(f"Spotify WID: {wid}")

        # 3. Bring Spotify to foreground
        _activate_spotify(wid, delay=0.8)

        # 4-6. Ctrl+K -> clear -> type (NO pauses, NO --window on type)
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+k"],
                       capture_output=True)
        time.sleep(0.8)   # search bar open animation
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+a"],
                       capture_output=True)
        time.sleep(0.2)
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", "80", query],
            capture_output=True
        )
        time.sleep(0.4)

        # 7. Submit
        subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"],
                       capture_output=True)
        time.sleep(3.5)   # results load

        # 8. Re-activate (results render can shift focus)
        _activate_spotify(wid, delay=0.5)

        # 9. Tab x1 to first song row (confirmed: Tab=1 on Varun's system)
        for i in range(SPOTIFY_TAB_COUNT):
            subprocess.run(["xdotool", "key", "--clearmodifiers", "Tab"],
                           capture_output=True)
            time.sleep(0.4)

        # 10. Play
        subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"],
                       capture_output=True)

        log.info(f"Spotify: playing '{query}'")
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
