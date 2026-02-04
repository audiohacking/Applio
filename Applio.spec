# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Applio macOS App

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the current directory
block_cipher = None
app_name = 'Applio'

# Collect data files from various packages
datas = []
datas += collect_data_files('gradio')
datas += collect_data_files('gradio_client')
datas += collect_data_files('safehttpx')
datas += collect_data_files('transformers')
datas += collect_data_files('fairseq')
datas += collect_data_files('librosa')

# Include essential directories
datas += [('assets', 'assets')]
datas += [('rvc', 'rvc')]
datas += [('tabs', 'tabs')]
datas += [('logs', 'logs')]

# Include the core.py and other essential Python files
datas += [('core.py', '.')]
datas += [('app.py', '.')]

# Collect all submodules
hiddenimports = []
hiddenimports += collect_submodules('gradio')
hiddenimports += collect_submodules('gradio_client')
hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('fairseq')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('torchaudio')
hiddenimports += collect_submodules('torchvision')
hiddenimports += collect_submodules('librosa')
hiddenimports += collect_submodules('webview')  # pywebview
hiddenimports += collect_submodules('soundfile')
hiddenimports += collect_submodules('faiss')
hiddenimports += collect_submodules('tensorboard')
hiddenimports += collect_submodules('webrtcvad')

# Additional hidden imports
hiddenimports += [
    'uvicorn.logging', 
    'uvicorn.loops', 
    'uvicorn.loops.auto', 
    'uvicorn.protocols', 
    'uvicorn.protocols.http', 
    'uvicorn.protocols.http.auto', 
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto', 
    'uvicorn.lifespan', 
    'uvicorn.lifespan.on',
    'rvc.lib.platform',
    'rvc.lib.zluda',
    'assets.i18n.i18n',
    'assets.themes.loadThemes',
    'assets.installation_checker',
    'assets.discord_presence',
    'webrtcvad',
    'rvc.realtime.utils.vad',
]

# Add all tab modules
tab_modules = [
    'tabs.inference.inference',
    'tabs.train.train',
    'tabs.extra.extra',
    'tabs.report.report',
    'tabs.download.download',
    'tabs.tts.tts',
    'tabs.voice_blender.voice_blender',
    'tabs.plugins.plugins',
    'tabs.settings.settings',
    'tabs.realtime.realtime',
    'tabs.console.console',
]
hiddenimports += tab_modules

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['build/macos/hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib.tests', 'numpy.tests'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=f'{app_name}_bin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disabled for macOS - UPX can cause issues with code signing
    console=False,  # No console window for cleaner UI experience
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disabled for macOS - UPX (Ultimate Packer for eXecutables) can cause issues with code signing
    upx_exclude=[],
    name=app_name,
)

app = BUNDLE(
    coll,
    name=f'{app_name}.app',
    icon='build/macos/Applio.icns',
    bundle_identifier='com.audiohacking.applio',
    version='0.1.0',
    info_plist={
        'CFBundleName': 'Applio',
        'CFBundleDisplayName': 'Applio',
        'CFBundleExecutable': app_name,
        'CFBundleIdentifier': 'com.audiohacking.applio',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'NSRequiresAquaSystemAppearance': False,
        'NSAppTransportSecurity': {
            'NSAllowsArbitraryLoads': True
        },
        'NSMicrophoneUsageDescription': 'Applio needs access to the microphone for voice conversion and real-time features.',
        'LSApplicationCategoryType': 'public.app-category.music',
        # Note: Camera permission removed as Applio does not require camera access
    },
)
