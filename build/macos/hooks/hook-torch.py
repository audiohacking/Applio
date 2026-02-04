# PyInstaller hook for torch with Apple MPS support
# This ensures torch MPS backend and necessary libraries are included

from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs

# Collect all torch submodules including MPS backend
hiddenimports = collect_submodules('torch')
hiddenimports += [
    'torch.backends.mps',
    'torch._C',
    'torch._dynamo',
    'torch._inductor',
    'torch.distributed',
    'torch.utils.tensorboard',
]

# Collect dynamic libraries
binaries = collect_dynamic_libs('torch')
