#!/usr/bin/env python3
"""
skills/system_skill.py — KENWAY System Skill
Handles volume, brightness, battery, and power actions.
Brightness uses direct sysfs write for AMD GPU (amdgpu_bl1).
Volume uses pactl (confirmed available on this system).
"""

import subprocess
import logging
import os
import yaml

log = logging.getLogger("kenway.system_skill")


def _cfg():
    path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


# ──────────────────────────────────────────────────────────────
# VOLUME  (pactl)
# ──────────────────────────────────────────────────────────────
def set_volume(data: str) -> str:
    cfg   = _cfg()["audio"]
    step  = cfg.get("step_percent", 10)
    data  = str(data).strip().lower()

    try:
        if data == "up":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{step}%"], check=True)
            return f"Volume increased by {step} percent."

        elif data == "down":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{step}%"], check=True)
            return f"Volume decreased by {step} percent."

        elif data == "mute":
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], check=True)
            return "Audio muted."

        elif data == "unmute":
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=True)
            return "Audio unmuted."

        elif data.isdigit():
            val = max(0, min(150, int(data)))
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"], check=True)
            return f"Volume set to {val} percent."

        else:
            return "I didn't understand the volume command."

    except Exception as e:
        log.error(f"Volume error: {e}")
        return "Volume command failed."


# ──────────────────────────────────────────────────────────────
# BRIGHTNESS  (direct sysfs — amdgpu_bl1)
# ──────────────────────────────────────────────────────────────
def _read_brightness() -> tuple[int, int]:
    """Returns (current, max) brightness values."""
    cfg = _cfg()["brightness"]
    cur = int(open(cfg["sysfs_path"]).read().strip())
    mx  = int(open(cfg["sysfs_max"]).read().strip())
    return cur, mx


def _write_brightness(value: int):
    """Write brightness via pkexec (requires polkit) or tee with sudo."""
    cfg  = _cfg()["brightness"]
    path = cfg["sysfs_path"]
    try:
        # Try direct write first (works if user is in video group)
        with open(path, "w") as f:
            f.write(str(value))
    except PermissionError:
        # Fallback: use tee via subprocess with pkexec
        subprocess.run(
            f"echo {value} | pkexec tee {path} > /dev/null",
            shell=True, check=True
        )


def set_brightness(data: str) -> str:
    cfg  = _cfg()["brightness"]
    step = cfg.get("step_percent", 10)
    data = str(data).strip().lower()

    try:
        cur, mx = _read_brightness()
        cur_pct = round((cur / mx) * 100)

        if data == "up":
            new_pct = min(100, cur_pct + step)
            new_val = round((new_pct / 100) * mx)
            _write_brightness(new_val)
            return f"Brightness increased to {new_pct} percent."

        elif data == "down":
            new_pct = max(5, cur_pct - step)   # floor at 5% so screen never goes black
            new_val = round((new_pct / 100) * mx)
            _write_brightness(new_val)
            return f"Brightness decreased to {new_pct} percent."

        elif data.isdigit():
            new_pct = max(5, min(100, int(data)))
            new_val = round((new_pct / 100) * mx)
            _write_brightness(new_val)
            return f"Brightness set to {new_pct} percent."

        else:
            return "I didn't understand the brightness command."

    except Exception as e:
        log.error(f"Brightness error: {e}")
        return f"Brightness control failed: {e}. Try: sudo usermod -aG video {os.environ.get('USER','varun_sukumar')}"


def get_brightness() -> str:
    try:
        cur, mx = _read_brightness()
        pct = round((cur / mx) * 100)
        return f"Screen brightness is at {pct} percent."
    except Exception as e:
        return f"Could not read brightness: {e}"


# ──────────────────────────────────────────────────────────────
# BATTERY
# ──────────────────────────────────────────────────────────────
def get_battery() -> str:
    try:
        # Try upower first for detailed info
        r = subprocess.run(["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            percentage, state = "", ""
            for line in r.stdout.splitlines():
                if "percentage" in line:
                    percentage = line.split(":")[1].strip().rstrip("%")
                if "state" in line and "state" == line.strip().split(":")[0].strip():
                    state = line.split(":")[1].strip()
            if percentage:
                charging = " and charging" if state == "charging" else ""
                return f"Battery is at {percentage} percent{charging}."

        # Fallback: read sysfs directly
        cap  = int(open("/sys/class/power_supply/BAT0/capacity").read().strip())
        stat = open("/sys/class/power_supply/BAT0/status").read().strip()
        charging = " and charging" if stat.lower() == "charging" else ""
        return f"Battery is at {cap} percent{charging}."

    except Exception as e:
        log.error(f"Battery error: {e}")
        return "Could not read battery status."
