#!/usr/bin/env python3
"""
skills/system_skill.py — System Controls
Volume, brightness, battery, shutdown, reboot, sleep.
"""

import subprocess
import logging
from core.voice import speak

log = logging.getLogger("kenway.system_skill")


def set_volume(value: str):
    """Set volume: 'up', 'down', or a numeric percentage."""
    try:
        if value == "up":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"])
            speak("Volume increased.")
        elif value == "down":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"])
            speak("Volume decreased.")
        elif value.isdigit():
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"])
            speak(f"Volume set to {value} percent.")
        log.info(f"Volume set: {value}")
    except Exception as e:
        speak("Failed to change volume.")
        log.error(f"Volume error: {e}")


def get_battery():
    """Read battery status and speak it."""
    try:
        result = subprocess.run(
            ["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT1"],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if "percentage" in line:
                pct = line.split(":")[-1].strip()
                speak(f"Battery is at {pct}.")
                log.info(f"Battery: {pct}")
                return
        speak("Could not read battery level.")
    except Exception as e:
        speak("Battery status unavailable.")
        log.error(f"Battery error: {e}")


def set_brightness(value: str):
    """Set brightness: 'up', 'down', or 0-100."""
    try:
        if value == "up":
            subprocess.run(["xbacklight", "-inc", "10"])
            speak("Brightness increased.")
        elif value == "down":
            subprocess.run(["xbacklight", "-dec", "10"])
            speak("Brightness decreased.")
        elif value.isdigit():
            subprocess.run(["xbacklight", "-set", value])
            speak(f"Brightness set to {value} percent.")
        log.info(f"Brightness set: {value}")
    except Exception as e:
        speak("Failed to change brightness. xbacklight may not be installed.")
        log.error(f"Brightness error: {e}")


def shutdown():
    speak("Shutting down the system. Goodbye, Varun.")
    log.info("System shutdown initiated.")
    subprocess.run(["systemctl", "poweroff"])


def reboot():
    speak("Rebooting the system. See you in a moment.")
    log.info("System reboot initiated.")
    subprocess.run(["systemctl", "reboot"])


def sleep_system():
    speak("Suspending system. Sleep well.")
    log.info("System sleep initiated.")
    subprocess.run(["systemctl", "suspend"])
