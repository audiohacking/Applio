"""
Central definition of user data root for Applio.
All downloaded models, trained models, and reusable data should live under
this directory so they persist across app updates and rebuilds.

- macOS (bundled): ~/Library/Application Support/Applio
- Otherwise: APPLIO_APP_SUPPORT env var, or current working directory (dev/script)
"""

import os


def get_app_support_dir():
    """
    Return the root directory for user data (models, downloads, logs, etc.).
    When running as the macOS app, the launcher sets APPLIO_APP_SUPPORT to
    ~/Library/Application Support/Applio so data is reused across builds/versions.
    """
    return os.environ.get("APPLIO_APP_SUPPORT", os.getcwd())


def get_models_dir():
    """Trained models (RVC .pth, etc.) - e.g. AppSupport/logs."""
    return os.path.join(get_app_support_dir(), "logs")


def get_rvc_models_dir():
    """Pretraineds, embedders, predictors - e.g. AppSupport/rvc/models."""
    return os.path.join(get_app_support_dir(), "rvc", "models")
