# PyInstaller hook for faiss-cpu on macOS
# This ensures faiss libraries are properly included in the bundle

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Collect all dynamic libraries from faiss
binaries = collect_dynamic_libs('faiss')

# Collect data files
datas = collect_data_files('faiss')
