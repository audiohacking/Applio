#!/bin/bash
# Applio.command - Launcher script for easy access from DMG
# Double-click this file to launch Applio in Terminal mode (shows console output)

cd "$(dirname "$0")"

if [ -d "Applio.app" ]; then
    echo "Launching Applio..."
    open "Applio.app"
else
    echo "Error: Applio.app not found in the same directory"
    echo "Make sure Applio.app is in the same folder as this launcher"
    read -p "Press Enter to exit..."
fi
