# Applio macOS Build Guide

This guide explains how to build a standalone macOS application for Applio using PyInstaller and pywebview.

## Overview

The macOS build creates a native `.app` bundle that:
- Runs natively on Apple Silicon (M1/M2/M3) and Intel Macs
- Uses Apple Metal Performance Shaders (MPS) for GPU acceleration
- Optimizes for unified memory architecture
- Includes a native UI via pywebview (no browser required)
- Packages all dependencies in a single distributable app

## Architecture Optimizations

### Apple MPS Support
The build is specifically optimized for Apple's Metal Performance Shaders:
- `PYTORCH_ENABLE_MPS_FALLBACK=1` - Enables MPS with CPU fallback
- `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` - Prevents OOM errors
- `OMP_NUM_THREADS=1` - Optimizes for Apple Silicon
- No CUDA support (not needed on macOS)

### Unified Memory
Takes advantage of Apple's unified memory architecture where GPU and CPU share memory, reducing memory copies and improving performance.

## Build Files

### Core Files
- `launcher.py` - Entry point that sets up environment and launches Applio
- `Applio.spec` - PyInstaller specification for building the app bundle
- `local_build.sh` - Local build script for testing
- `.github/workflows/build-macos-release.yml` - GitHub Actions workflow

### Build Assets
- `build/macos/generate_icon.sh` - Converts ICO to ICNS icon format
- `build/macos/codesign.sh` - Code signs the app bundle
- `build/macos/hooks/` - PyInstaller hooks for proper packaging

### Distribution
- `Applio.command` - Terminal launcher included in DMG
- `.github/DMG_README.txt` - User instructions for DMG

## Requirements

### System Requirements
- macOS 11.0 (Big Sur) or later
- Python 3.11
- Xcode Command Line Tools (`xcode-select --install`)
- ImageMagick (`brew install imagemagick`)

### Python Dependencies
Install from `requirements_macos.txt`:
```bash
pip install -r requirements_macos.txt
```

Key dependencies:
- PyInstaller 6.x - For creating app bundle
- pywebview 4.x - For native UI
- torch 2.7.1 - With MPS support
- gradio 6.4.0 - Web UI framework

## Local Build Process

### Quick Build
```bash
chmod +x local_build.sh
./local_build.sh
```

### Manual Build Steps

1. **Install Dependencies**
   ```bash
   python3.11 -m pip install --upgrade pip
   pip install -r requirements_macos.txt
   ```

2. **Generate App Icon**
   ```bash
   chmod +x build/macos/generate_icon.sh
   ./build/macos/generate_icon.sh
   ```

3. **Build with PyInstaller**
   ```bash
   python3.11 -m PyInstaller Applio.spec --clean --noconfirm
   ```

4. **Set Up Executable**
   ```bash
   cp dist/Applio.app/Contents/MacOS/Applio_bin dist/Applio.app/Contents/MacOS/Applio
   chmod +x dist/Applio.app/Contents/MacOS/Applio
   ```

5. **Code Sign**
   ```bash
   chmod +x build/macos/codesign.sh
   MACOS_SIGNING_IDENTITY="-" ./build/macos/codesign.sh dist/Applio.app
   ```

6. **Test**
   ```bash
   open dist/Applio.app
   ```

### If Gatekeeper Blocks
```bash
xattr -cr dist/Applio.app
# Then right-click → Open
```

## GitHub Actions Build

The workflow `.github/workflows/build-macos-release.yml` automatically builds on:
- New releases (tagged)
- Manual trigger via workflow_dispatch

### Manual Trigger
1. Go to Actions tab in GitHub
2. Select "Build macOS Release"
3. Click "Run workflow"
4. Enter version tag (e.g., `v0.1.0-macos`)

### Outputs
- `Applio-macOS.dmg` - Disk image for distribution
- `Applio-macOS.zip` - ZIP archive alternative
- `checksums.txt` - SHA256 checksums

## Distribution

### DMG Contents
- `Applio.app` - The main application
- `Applio.command` - Terminal launcher for debugging
- `Applications` symlink - For easy drag-to-install
- `README.txt` - User instructions

### Installation Instructions
Users should:
1. Download the DMG
2. Drag Applio.app to Applications
3. Right-click → Open on first launch
4. Grant microphone permissions if prompted

## Data Storage

All user data is stored in standard macOS locations:
- App data: `~/Library/Application Support/Applio/`
- Logs: `~/Library/Logs/Applio/`

This keeps the app bundle clean and follows macOS conventions.

## Code Signing

### Ad-hoc Signing (Default)
Uses `-` identity for local builds and CI:
```bash
codesign --force --deep --sign "-" Applio.app
```

### Developer ID Signing (Production)
For distribution outside the Mac App Store, set the `MACOS_SIGNING_IDENTITY` secret:
```bash
export MACOS_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
```

The script will automatically use this for notarization-compatible signing.

## Troubleshooting

### Build Fails
- Ensure Python 3.11 is installed
- Check all dependencies are installed
- Verify icon generation worked
- Check PyInstaller output for errors

### App Won't Open
- Run `xattr -cr Applio.app` to remove quarantine
- Check Console.app for crash logs
- Try launching via Applio.command to see errors

### Missing Dependencies
- Check `~/Library/Logs/Applio/console.log`
- Verify all hiddenimports in Applio.spec
- Add missing modules to PyInstaller hooks

### Performance Issues
- Verify MPS is available: `torch.backends.mps.is_available()`
- Check Activity Monitor for memory usage
- Review Metal GPU usage in Activity Monitor

## Development

### Testing Changes
1. Make changes to source code
2. Run `./local_build.sh`
3. Test `dist/Applio.app`
4. Iterate

### Adding Dependencies
1. Update `requirements_macos.txt`
2. If needed, update `Applio.spec` hiddenimports
3. Add PyInstaller hooks in `build/macos/hooks/` if required
4. Test build

### PyInstaller Hooks
Located in `build/macos/hooks/`:
- `hook-faiss.py` - Ensures faiss libraries are included
- `hook-torch.py` - Includes MPS backend and torch modules

Add new hooks as `hook-<package>.py` for any package requiring special handling.

## References

This implementation is based on:
- [CTFN-Studio build workflow](https://github.com/audiohacking/CTFN-Studio/blob/main/.github/workflows/build-macos-release.yml)
- [CTFN-Studio local build](https://github.com/audiohacking/CTFN-Studio/blob/main/local_build.sh)

## Support

For issues:
- Discord: https://discord.gg/urxFjYmYYh
- GitHub Issues: https://github.com/audiohacking/Applio/issues
