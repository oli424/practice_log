#!/usr/bin/env bash
cd "$(dirname "$0")"

# Log stdout/stderr so you can debug when lauched from the desktop
exec python3 practice_gui.py >> "$HOME/.practice_log_launcher.log" 2>&1