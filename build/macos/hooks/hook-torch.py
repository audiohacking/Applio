# PyInstaller hook for torch with Apple MPS support
# This ensures torch MPS backend and necessary libraries are included

import os
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

# torch.__init__ looks for torch/bin/torch_shm_manager at runtime; include it
_torch_dir = os.path.dirname(__import__('torch').__file__)
_torch_bin = os.path.join(_torch_dir, 'bin')
if os.path.isdir(_torch_bin):
    for name in os.listdir(_torch_bin):
        path = os.path.join(_torch_bin, name)
        if os.path.isfile(path):
            binaries.append((path, 'torch/bin'))
