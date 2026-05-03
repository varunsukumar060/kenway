#!/usr/bin/env python3
"""
debug/spotify_debug.py v2
Tests the NEW Ctrl+K + click fallback approach.
Run: python3 debug/spotify_debug.py
"""

import subprocess, time, sys

QUERY = "raavana mavanda"

def xdo(*args):
    r = subprocess.run(["xdotool"] + list(args), capture_output=True, text=True)
    return r.stdout.strip(), r.returncode

def pause(msg):
    input(f"\n>>> {msg}\n    Press ENTER to continue...")

print("=" * 60)
print("KENWAY Spotify Debugger v2 — Ctrl+K + click fallback")
print("=" * 60)

# Launch
is_running = subprocess.run(["pgrep","-x","spotify"], capture_output=True).returncode == 0
if not is_running:
    print("Launching Spotify...")
    subprocess.Popen(["spotify"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(9)
else:
    print("Spotify already running.")
    time.sleep(0.5)

# Get WID
wid = None
for i in range(12):
    out, _ = xdo("search", "--name", "Spotify")
    ids = out.splitlines()
    if ids:
        wid = ids[-1]  # last = main window
        print(f"Window IDs: {ids}")
        print(f"Using WID : {wid}")
        break
    time.sleep(0.5)

if not wid:
    print("ERROR: Spotify window not found")
    sys.exit(1)

# Geometry
geo_out, _ = xdo("getwindowgeometry", wid)
print(f"Geometry:\n{geo_out}")
pause("Spotify window found. Is it visible on screen?")

# Activate
xdo("windowactivate", "--sync", wid)
xdo("windowraise", wid)
time.sleep(0.8)
pause("Window activated. Is Spotify in foreground?")

# Ctrl+K
print("\nSending Ctrl+K (search shortcut)...")
xdo("key", "--window", wid, "--clearmodifiers", "ctrl+k")
time.sleep(1.0)
pause("After Ctrl+K — is the search bar active/highlighted? (yes/no)")

# Click search bar
print("\nNow clicking search bar by coordinate (50% width, 6% height)...")
# Parse geometry
width, height = 1280, 800
for line in geo_out.splitlines():
    line = line.strip()
    if "Geometry" in line:
        size = line.split(":")[1].strip()
        width, height = map(int, size.split("x"))
sx = int(width * 0.50)
sy = int(height * 0.06)
print(f"Clicking at ({sx}, {sy}) inside window")
xdo("mousemove", "--window", wid, str(sx), str(sy))
time.sleep(0.1)
xdo("click", "--window", wid, "1")
time.sleep(0.6)
pause("After mouse click — is the search bar now active? (yes/no)")

# Clear + type
xdo("key", "--window", wid, "--clearmodifiers", "ctrl+a")
time.sleep(0.2)
xdo("type", "--window", wid, "--clearmodifiers", "--delay", "60", QUERY)
time.sleep(0.5)
pause(f'Does search bar show "{QUERY}"? (yes/no)')

# Enter
xdo("key", "--window", wid, "--clearmodifiers", "Return")
time.sleep(3.5)
xdo("windowactivate", "--sync", wid)
xdo("windowraise", wid)
time.sleep(0.5)
pause("After Enter — do you see SEARCH RESULTS in Spotify? (yes/no)")

# Tab steps
for n in range(1, 6):
    xdo("key", "--window", wid, "--clearmodifiers", "Tab")
    time.sleep(0.4)
    ans = input(f"\n>>> Tab {n}: What is highlighted/focused in Spotify? ")
    print(f"    Recorded: Tab {n} → {ans}")
    if "song" in ans.lower() or "track" in ans.lower():
        print(f"    FIRST SONG FOUND at Tab {n}!")
        confirm = input("    Press ENTER to play it (sends Enter key)...")
        xdo("key", "--window", wid, "--clearmodifiers", "Return")
        time.sleep(1)
        print("    Enter sent. Is the song playing now? (check Spotify)")
        break
else:
    print("\nSong row not found in 5 tabs. Need to investigate Spotify layout further.")

print("\n=" * 60)
print("Debug complete. Report back Tab count where song was highlighted.")
print("=" * 60)
