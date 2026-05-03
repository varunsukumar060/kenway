#!/usr/bin/env python3
"""
debug/youtube_debug.py
Tests Selenium + Chrome step by step for YouTube auto-click.
Shows exactly where it fails or succeeds.

Run from kenway root (with venv active):
    python3 debug/youtube_debug.py
"""

import time
import sys

CHROME_BINARY     = "/usr/bin/google-chrome"
CHROMEDRIVER_PATH = "/snap/chromium/current/usr/lib/chromium-browser/chromedriver"
QUERY             = "raavana mavanda"

print("=" * 60)
print("KENWAY YouTube Selenium Debugger")
print("=" * 60)

# Step 1: Import Selenium
print("\n[1] Importing Selenium...")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    print("    OK")
except ImportError as e:
    print(f"    FAIL: {e}")
    print("    Run: pip install selenium")
    sys.exit(1)

# Step 2: Launch Chrome
print(f"\n[2] Launching Chrome...")
print(f"    Binary  : {CHROME_BINARY}")
print(f"    Driver  : {CHROMEDRIVER_PATH}")
try:
    opts = Options()
    opts.binary_location = CHROME_BINARY
    opts.add_experimental_option("detach", True)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,800")
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver  = webdriver.Chrome(service=service, options=opts)
    print("    OK — Chrome window should be visible now")
except Exception as e:
    print(f"    FAIL: {e}")
    sys.exit(1)

input("\n>>> Is a Chrome window open? Press ENTER...")

# Step 3: Load YouTube search
import urllib.parse
encoded    = urllib.parse.quote_plus(QUERY)
search_url = f"https://www.youtube.com/results?search_query={encoded}"
print(f"\n[3] Loading: {search_url}")
try:
    driver.get(search_url)
    print("    Page loaded")
except Exception as e:
    print(f"    FAIL: {e}")
    sys.exit(1)

input("\n>>> Do you see YouTube search results in Chrome? Press ENTER...")

# Step 4: Find video elements
print("\n[4] Looking for ytd-video-renderer a#video-title elements...")
try:
    wait   = WebDriverWait(driver, 15)
    videos = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "ytd-video-renderer a#video-title")
        )
    )
    print(f"    Found {len(videos)} video(s)")
    for i, v in enumerate(videos[:3]):
        print(f"    [{i}] {v.get_attribute('title')}")
except Exception as e:
    print(f"    FAIL: {e}")
    sys.exit(1)

input("\n>>> Video titles printed above. Press ENTER to click first one...")

# Step 5: Click first video
print("\n[5] Clicking first video...")
try:
    first = videos[0]
    title = first.get_attribute("title") or QUERY
    driver.execute_script("arguments[0].scrollIntoView(true);", first)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", first)
    print(f"    Clicked: {title}")
except Exception as e:
    print(f"    FAIL: {e}")
    sys.exit(1)

time.sleep(2)
print("\n[6] Checking current URL (should be watch?v=...)")
print(f"    URL: {driver.current_url}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE. Tell Perplexity:")
print("  - Did Chrome open?")
print("  - Did YouTube search results load?")
print("  - Did it print video titles?")
print("  - Did the first video start playing?")
print("  - Does Chrome stay open after the script ends?")
print("  - The final URL shown above")
print("=" * 60)

input("Press ENTER to exit script (Chrome should stay open due to detach=True)...")
