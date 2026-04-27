"""Backward-compatible facade for configuration.

Canonical location: infrastructure.config
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from infrastructure.config import AppConfig

__all__ = ["AppConfig"]
