#!/usr/bin/env python3
"""
debug/spotify_debug.py v5
Key fix: NO pause between Ctrl+K and typing.
After each terminal input() the script re-focuses Spotify before sending keys.
Run: python3 debug/spotify_debug.py
"""

import subprocess, time, sys

QUERY = "raavana mavanda"

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

def refocus(wid):
    """Re-grab Spotify focus after terminal input() steals it."""
    subprocess.run(["xdotool", "windowactivate", "--sync", wid], capture_output=True)
    subprocess.run(["xdotool", "windowraise", wid], capture_output=True)
    time.sleep(0.5)

print("=" * 60)
print("Spotify Debugger v5 — no pause between focus and type")
print("=" * 60)

# Launch
if subprocess.run(["pgrep","-x","spotify"], capture_output=True).returncode != 0:
    print("Launching Spotify...")
    subprocess.Popen(["spotify"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Waiting 9s...")
    time.sleep(9)
else:
    print("Spotify already running.")
    time.sleep(0.5)

# WID
wid = None
for _ in range(12):
    ids = run(["xdotool","search","--name","Spotify"]).splitlines()
    if ids:
        wid = ids[-1]
        print(f"WID: {wid}")
        break
    time.sleep(0.5)
if not wid: sys.exit("No Spotify window found")

# -----------------------------------------------------------------------
# PHASE 1: Do the FULL search sequence without ANY pause in between.
# Pausing gives terminal focus back, then xdotool types into terminal.
# -----------------------------------------------------------------------
print("\n[PHASE 1] Running full search sequence uninterrupted...")
print(f"  Searching for: {QUERY}")
print("  Watch Spotify — it should search and show results.")
print("  (This runs automatically, no keypresses needed)")
time.sleep(1)  # give you 1s to look at Spotify

# Activate Spotify
subprocess.run(["xdotool","windowactivate","--sync",wid], capture_output=True)
subprocess.run(["xdotool","windowraise",wid], capture_output=True)
time.sleep(0.8)

# Ctrl+K — focus search
subprocess.run(["xdotool","key","--clearmodifiers","ctrl+k"], capture_output=True)
time.sleep(0.8)   # wait for search bar to animate open

# Clear + type — NO pause before this, Spotify still has focus
subprocess.run(["xdotool","key","--clearmodifiers","ctrl+a"], capture_output=True)
time.sleep(0.2)
subprocess.run(["xdotool","type","--clearmodifiers","--delay","80", QUERY],
               capture_output=True)
time.sleep(0.5)

# Enter to search
subprocess.run(["xdotool","key","--clearmodifiers","Return"], capture_output=True)
time.sleep(3.5)   # wait for results to load

# Re-activate Spotify after results load
subprocess.run(["xdotool","windowactivate","--sync",wid], capture_output=True)
subprocess.run(["xdotool","windowraise",wid], capture_output=True)
time.sleep(0.5)

print("  Search sequence complete.")

# -----------------------------------------------------------------------
# PHASE 2: Now pause and ask — terminal has focus here, that's fine
# because we'll refocus Spotify before each Tab
# -----------------------------------------------------------------------
ans = input("\n>>> Do you see search results in Spotify? (yes/no): ")
if "no" in ans.lower():
    print("Search failed. Does the search bar show the query text?")
    print("Check: did Spotify show the typed text before Enter?")
    sys.exit(1)

# Tab to find first song — refocus Spotify before EACH tab
print("\n[PHASE 2] Finding correct Tab count...")
for n in range(1, 8):
    # Re-grab Spotify focus before sending Tab
    refocus(wid)
    subprocess.run(["xdotool","key","--clearmodifiers","Tab"], capture_output=True)
    time.sleep(0.5)
    # Now terminal gets focus back for input()
    ans = input(f"Tab {n}: What is highlighted in Spotify? ")
    print(f"  Tab {n} -> {ans}")
    if any(w in ans.lower() for w in ["song","track","play","mavanda","row","first","music"]):
        print(f"\n  SONG ROW at Tab {n}! Pressing Enter to play...")
        refocus(wid)
        subprocess.run(["xdotool","key","--clearmodifiers","Return"], capture_output=True)
        print(f"\n  >>> SET SPOTIFY_TAB_COUNT = {n} in skills/browser_skill.py <<<")
        break
else:
    print("\nNot found in 7 tabs.")
    print("Open Spotify manually, do a search, then press Tab and count")
    print("how many presses reach the first song row. Tell that number.")

print("\n" + "="*60)
print("Debug complete.")
