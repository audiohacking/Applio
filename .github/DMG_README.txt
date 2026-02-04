====================================
  Applio for macOS - Installation
====================================

Thank you for downloading Applio!

INSTALLATION
------------
1. Drag Applio.app to the Applications folder (or anywhere you prefer)
2. Double-click Applio.app to launch

FIRST RUN
---------
If macOS shows "Applio can't be opened" or "damaged" warning:

Option 1 (Recommended):
  • Right-click (or Control+click) on Applio.app
  • Select "Open" from the menu
  • Click "Open" in the dialog

Option 2 (If Option 1 doesn't work):
  • Open Terminal
  • Run: xattr -cr /path/to/Applio.app
  • Replace /path/to/Applio.app with actual path
  • Then launch normally

ALTERNATIVE LAUNCH
------------------
You can also use the Applio.command file:
  • Double-click Applio.command to launch in Terminal mode
  • This shows console output for debugging

DATA LOCATION
-------------
All user data is stored in:
  ~/Library/Application Support/Applio/
  
Logs are stored in:
  ~/Library/Logs/Applio/

SYSTEM REQUIREMENTS
-------------------
  • macOS 11.0 (Big Sur) or later
  • Apple Silicon (M1/M2/M3) or Intel processor
  • 8GB RAM minimum (16GB+ recommended)
  • Metal GPU support for optimal performance

OPTIMIZATIONS
-------------
Applio is optimized for Apple Metal Performance Shaders (MPS):
  • Leverages unified memory architecture
  • Optimized for Apple Silicon processors
  • No CUDA support needed

SUPPORT
-------
For issues and support:
  • Discord: https://discord.gg/urxFjYmYYh
  • GitHub: https://github.com/audiohacking/Applio

Enjoy using Applio!
