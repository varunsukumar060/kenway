#!/bin/bash
# KENWAY trigger script
# Bind this to a key in XFCE keyboard settings:
#   xfce4-keyboard-settings -> Application Shortcuts
#   Command : bash /home/varun_sukumar/kenway/scripts/trigger.sh
#   Key     : Ctrl+F12
#
# This sends a signal to KENWAY's socket, which shows the input bar.
# Works globally over any application with zero terminal interference.

echo '' | nc -U /tmp/kenway.sock 2>/dev/null || \
    notify-send "KENWAY" "Not running. Start with: python3 ~/kenway/main.py"
