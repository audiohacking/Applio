# PyInstaller hook for webrtcvad on macOS
# This ensures webrtcvad libraries are properly included in the bundle

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Collect all dynamic libraries from webrtcvad
binaries = collect_dynamic_libs('webrtcvad')

# Collect data files if any
datas = collect_data_files('webrtcvad')
