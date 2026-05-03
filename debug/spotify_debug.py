#!/usr/bin/env python3
"""
debug/spotify_debug.py v3
Tests confirmed approach:
  - Click at absolute screen coords to focus search bar
  - Type WITHOUT --window flag
Run: python3 debug/spotify_debug.py
"""

import subprocess, time, sys

QUERY            = "raavana mavanda"
SEARCH_X_OFFSET  = 683   # confirmed from v2 debug
SEARCH_Y_OFFSET  = 42

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

def pause(msg):
    return input(f"\n>>> {msg}\n    Press ENTER (or type answer): ")

print("=" * 60)
print("Spotify Debugger v3 — click + type-to-active-focus")
print("=" * 60)

# Launch
if subprocess.run(["pgrep","-x","spotify"], capture_output=True).returncode != 0:
    print("Launching Spotify...")
    subprocess.Popen(["spotify"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(9)
else:
    print("Spotify running.")
    time.sleep(0.5)

# WID
wid = None
for _ in range(12):
    ids = run(["xdotool","search","--name","Spotify"]).splitlines()
    if ids:
        wid = ids[-1]
        print(f"WIDs: {ids}  Using: {wid}")
        break
    time.sleep(0.5)

if not wid: sys.exit("No Spotify window found")

# Window position
geo = run(["xdotool","getwindowgeometry", wid])
print(f"Geometry: {geo}")
wx, wy = 0, 82
for line in geo.splitlines():
    if "Position" in line:
        pos = line.split(":")[1].split("(")[0].strip()
        wx, wy = map(int, pos.split(","))
abs_x = wx + SEARCH_X_OFFSET
abs_y = wy + SEARCH_Y_OFFSET
print(f"Absolute screen click target: ({abs_x}, {abs_y})")

# Activate
subprocess.run(["xdotool","windowactivate","--sync",wid], capture_output=True)
subprocess.run(["xdotool","windowraise",wid], capture_output=True)
time.sleep(0.8)
pause("Spotify in foreground?")

# Click search bar
print(f"\nClicking at absolute ({abs_x}, {abs_y})...")
subprocess.run(["xdotool","mousemove", str(abs_x), str(abs_y)], capture_output=True)
time.sleep(0.1)
subprocess.run(["xdotool","click","1"], capture_output=True)
time.sleep(0.6)
ans = pause("Is search bar active/focused now? (yes/no)")
if "no" in ans.lower():
    print("PROBLEM: Click did not focus search bar.")
    print("Try moving your mouse to the search bar manually and tell me the screen coordinates.")
    sys.exit(1)

# Clear + type WITHOUT --window
print(f'\nTyping "{QUERY}" (no --window flag)...')
subprocess.run(["xdotool","key","--clearmodifiers","ctrl+a"], capture_output=True)
time.sleep(0.2)
subprocess.run(["xdotool","type","--clearmodifiers","--delay","60", QUERY],
               capture_output=True)
time.sleep(0.5)
ans = pause(f'Does search bar show "{QUERY}"? (yes/no)')
if "no" in ans.lower():
    print("PROBLEM: Text not appearing. xdotool type to active focus also failed.")
    print("Will need xclip clipboard paste approach instead.")
    sys.exit(1)

# Enter
print("\nPress Enter to search...")
subprocess.run(["xdotool","key","--clearmodifiers","Return"], capture_output=True)
time.sleep(3.5)
subprocess.run(["xdotool","windowactivate","--sync",wid], capture_output=True)
subprocess.run(["xdotool","windowraise",wid], capture_output=True)
time.sleep(0.5)
ans = pause("Do you see SEARCH RESULTS in Spotify? (yes/no)")
if "no" in ans.lower():
    sys.exit("Search results not showing. Something still wrong with typing.")

# Tab steps
print("\nNow tabbing to first result...")
for n in range(1, 7):
    subprocess.run(["xdotool","key","--clearmodifiers","Tab"], capture_output=True)
    time.sleep(0.4)
    ans = pause(f"Tab {n}: What is highlighted? (describe what you see)")
    print(f"  Tab {n} -> {ans}")
    if any(w in ans.lower() for w in ["song","track","play","mavanda","row"]):
        print(f"  SONG FOUND at Tab {n}! Pressing Enter to play...")
        subprocess.run(["xdotool","key","--clearmodifiers","Return"], capture_output=True)
        time.sleep(1)
        print("  Enter sent. Is it playing?")
        break

print("\n" + "="*60)
print("Done. Report the Tab number where the song was highlighted.")
