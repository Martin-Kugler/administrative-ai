"""Backward-compatible facade for configuration imports.

The canonical implementation now lives in administrative_ai.infrastructure.config.
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from administrative_ai.infrastructure.config import AppConfig

__all__ = ["AppConfig"]