#!/usr/bin/env python3
"""
debug/spotify_debug.py
Runs Spotify xdotool step by step with PAUSES so you can see exactly
what each step does. Reports window ID, focus state, and key delivery.

Run from kenway root:
    python3 debug/spotify_debug.py
"""

import subprocess
import time
import sys

QUERY = "raavana mavanda"

def xdo(*args):
    result = subprocess.run(["xdotool"] + list(args), capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

def pause(msg):
    input(f"\n>>> {msg}\n    Press ENTER to continue...")

print("=" * 60)
print("KENWAY Spotify Debugger")
print("=" * 60)

# Step 1: Find window
print("\n[1] Searching for Spotify window...")
is_running = subprocess.run(["pgrep", "-x", "spotify"], capture_output=True).returncode == 0
if not is_running:
    print("    Spotify not running. Launching...")
    subprocess.Popen(["spotify"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("    Waiting 8s for Spotify to load...")
    time.sleep(8)
else:
    print("    Spotify already running.")

# Retry window ID up to 10 times
wid = None
for i in range(10):
    out, rc = xdo("search", "--name", "Spotify")
    ids = out.splitlines()
    if ids:
        wid = ids[0]
        print(f"    Window IDs found: {ids}")
        print(f"    Using WID: {wid}")
        break
    print(f"    Attempt {i+1}: no window yet...")
    time.sleep(0.5)

if not wid:
    print("ERROR: Could not find Spotify window. Is Spotify installed?")
    sys.exit(1)

pause("Step 1 done. Spotify window found. Look at your screen — is Spotify visible?")

# Step 2: Focus
print("\n[2] Focusing Spotify window...")
xdo("windowfocus", "--sync", wid)
xdo("windowraise", wid)
time.sleep(0.5)
pause("Step 2 done. Is Spotify now in the FOREGROUND and focused?")

# Step 3: Ctrl+L
print("\n[3] Sending Ctrl+L (open search bar)...")
xdo("key", "--window", wid, "--clearmodifiers", "ctrl+l")
time.sleep(1.0)
pause("Step 3 done. Is the Spotify SEARCH BAR now active/highlighted?")

# Step 4: Clear + type
print(f'\n[4] Typing search query: "{QUERY}"...')
xdo("key", "--window", wid, "--clearmodifiers", "ctrl+a")
time.sleep(0.3)
xdo("type", "--window", wid, "--clearmodifiers", "--delay", "60", QUERY)
time.sleep(0.5)
pause(f'Step 4 done. Does the search bar show "{QUERY}"?')

# Step 5: Enter to search
print("\n[5] Pressing Enter to search...")
xdo("key", "--window", wid, "--clearmodifiers", "Return")
time.sleep(3.5)
pause("Step 5 done. Do you see SEARCH RESULTS for the query in Spotify?")

# Step 6: Re-focus
print("\n[6] Re-focusing Spotify after search...")
xdo("windowfocus", "--sync", wid)
xdo("windowraise", wid)
time.sleep(0.4)

# Step 7: Tab x1
print("\n[7] Sending Tab x1 (move to first result)...")
xdo("key", "--window", wid, "--clearmodifiers", "Tab")
time.sleep(0.5)
pause("Step 7 done. What is highlighted/focused in Spotify right now?\n    (e.g. filter pill 'Songs', first song row, artist name, etc.)")

# Step 8: Tab x2
print("\n[8] Sending one more Tab (Tab x2 total)...")
xdo("key", "--window", wid, "--clearmodifiers", "Tab")
time.sleep(0.5)
pause("Step 8 done. What is highlighted now?")

# Step 9: Tab x3
print("\n[9] Sending one more Tab (Tab x3 total)...")
xdo("key", "--window", wid, "--clearmodifiers", "Tab")
time.sleep(0.5)
pause("Step 9 done. What is highlighted now?")

# Step 10: Tab x4
print("\n[10] Sending one more Tab (Tab x4 total)...")
xdo("key", "--window", wid, "--clearmodifiers", "Tab")
time.sleep(0.5)
pause("Step 10 done. What is highlighted now?")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("Tell Perplexity:")
print("  - After which Tab number the FIRST SONG ROW was highlighted")
print("  - Whether pressing Enter at that Tab plays the song")
print("=" * 60)
