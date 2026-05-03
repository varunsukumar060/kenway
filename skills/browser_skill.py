#!/usr/bin/env python3
"""
skills/browser_skill.py - KENWAY Browser Skill

YouTube : Selenium + detach=True (confirmed working)
Spotify : Ctrl+K -> type (no pause, no --window) -> Enter -> Tab -> play
"""

import subprocess
import logging
import urllib.parse
import time

log = logging.getLogger("kenway.browser_skill")

CHROME_BINARY     = "/usr/bin/google-chrome"
CHROMEDRIVER_PATH = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"

# Confirmed Tab count to reach first song row after search results load.
# Will be set after debug v5 reports the correct number.
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
# Spotify helpers
# ---------------------------------------------------------------------------

def _get_spotify_wid() -> str | None:
    out = _run(["xdotool", "search", "--name", "Spotify"])
    ids = out.splitlines()
    return ids[-1] if ids else None


def _activate_spotify(wid: str, delay: float = 0.6):
    subprocess.run(["xdotool", "windowactivate", "--sync", wid], capture_output=True)
    subprocess.run(["xdotool", "windowraise", wid], capture_output=True)
    time.sleep(delay)


def _key(key: str, delay: float = 0.4):
    subprocess.run(["xdotool", "key", "--clearmodifiers", key], capture_output=True)
    time.sleep(delay)


def _type(text: str, delay: float = 0.5):
    subprocess.run(
        ["xdotool", "type", "--clearmodifiers", "--delay", "80", text],
        capture_output=True
    )
    time.sleep(delay)


# ---------------------------------------------------------------------------
# YOUTUBE  (confirmed working — unchanged)
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
# CRITICAL: No sleep/pause between windowactivate -> Ctrl+K -> type.
# Any pause gives terminal/other window a chance to steal focus,
# causing xdotool type to fire into the wrong window.
# ---------------------------------------------------------------------------

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
            time.sleep(0.3)

        # 2. Get window ID
        wid = None
        for _ in range(12):
            wid = _get_spotify_wid()
            if wid: break
            time.sleep(0.5)

        if not wid:
            raise Exception("Spotify window not found")

        log.info(f"Spotify WID: {wid}")

        # 3. Activate Spotify
        _activate_spotify(wid, delay=0.8)

        # 4-6. Ctrl+K -> clear -> type  (NO sleep between these steps)
        #      Spotify must keep focus the entire time
        subprocess.run(["xdotool","key","--clearmodifiers","ctrl+k"], capture_output=True)
        time.sleep(0.8)   # wait for search bar animation only
        subprocess.run(["xdotool","key","--clearmodifiers","ctrl+a"], capture_output=True)
        time.sleep(0.2)
        subprocess.run(["xdotool","type","--clearmodifiers","--delay","80", query],
                       capture_output=True)
        time.sleep(0.4)

        # 7. Submit
        subprocess.run(["xdotool","key","--clearmodifiers","Return"], capture_output=True)
        time.sleep(3.5)   # wait for search results to load

        # 8. Re-activate after results load
        _activate_spotify(wid, delay=0.5)

        # 9. Tab to first song row
        for i in range(SPOTIFY_TAB_COUNT):
            subprocess.run(["xdotool","key","--clearmodifiers","Tab"], capture_output=True)
            time.sleep(0.4)
            log.info(f"Tab {i+1}/{SPOTIFY_TAB_COUNT}")

        # 10. Play
        subprocess.run(["xdotool","key","--clearmodifiers","Return"], capture_output=True)

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
