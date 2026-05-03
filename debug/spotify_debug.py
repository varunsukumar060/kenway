#!/usr/bin/env python3
"""
debug/spotify_debug.py v4
Confirmed approach: Ctrl+K to focus search, type to active focus.
Now finding correct Tab count to reach first song row.
Run: python3 debug/spotify_debug.py
"""

import subprocess, time, sys

QUERY = "raavana mavanda"

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()

def pause(msg):
    return input(f"\n>>> {msg}\n    Answer: ")

print("=" * 60)
print("Spotify Debugger v4 — Ctrl+K confirmed, finding Tab count")
print("=" * 60)

# Launch
if subprocess.run(["pgrep","-x","spotify"], capture_output=True).returncode != 0:
    print("Launching Spotify...")
    subprocess.Popen(["spotify"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

# Activate
subprocess.run(["xdotool","windowactivate","--sync",wid], capture_output=True)
subprocess.run(["xdotool","windowraise",wid], capture_output=True)
time.sleep(0.8)

# Ctrl+K
print("Sending Ctrl+K...")
subprocess.run(["xdotool","key","--clearmodifiers","ctrl+k"], capture_output=True)
time.sleep(0.8)
ans = pause("Is the search bar focused/highlighted? (yes/no)")
if "no" in ans.lower():
    sys.exit("Ctrl+K still not working. Need different approach.")

# Clear + type
subprocess.run(["xdotool","key","--clearmodifiers","ctrl+a"], capture_output=True)
time.sleep(0.2)
subprocess.run(["xdotool","type","--clearmodifiers","--delay","60", QUERY],
               capture_output=True)
time.sleep(0.5)
ans = pause(f'Does search bar show "{QUERY}"? (yes/no)')
if "no" in ans.lower():
    sys.exit("Typing to active focus failed too. Need xclip approach.")

# Enter + wait
print("Submitting search...")
subprocess.run(["xdotool","key","--clearmodifiers","Return"], capture_output=True)
time.sleep(3.5)

# Re-activate
subprocess.run(["xdotool","windowactivate","--sync",wid], capture_output=True)
subprocess.run(["xdotool","windowraise",wid], capture_output=True)
time.sleep(0.5)

ans = pause("Do you see search results in Spotify? (yes/no)")
if "no" in ans.lower():
    sys.exit("No search results. Check Spotify is on search results page.")

# Tab to find first song
print("\nTabbing to find first song row...")
for n in range(1, 8):
    subprocess.run(["xdotool","key","--clearmodifiers","Tab"], capture_output=True)
    time.sleep(0.4)
    ans = pause(f"Tab {n}: What is highlighted? ")
    print(f"  Tab {n} -> {ans}")
    if any(w in ans.lower() for w in ["song","track","play","mavanda","first","row","result"]):
        print(f"  First song at Tab {n}! Playing...")
        subprocess.run(["xdotool","key","--clearmodifiers","Return"], capture_output=True)
        print(f"\n  SET SPOTIFY_TAB_COUNT = {n} in skills/browser_skill.py")
        break
else:
    print("Song not found in 7 tabs.")
    print("Try pressing Tab manually in Spotify and count to the first song row.")

print("\n" + "="*60)
