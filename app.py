"""Backward-compatible facade for CLI entrypoint.

The canonical implementation now lives in administrative_ai.adapters.cli.app_cli.
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from administrative_ai.adapters.cli.app_cli import main


if __name__ == "__main__":
    main()