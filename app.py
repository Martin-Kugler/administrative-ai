"""Backward-compatible facade for CLI entrypoint.

Canonical location: presentation.cli.app_cli
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from presentation.cli.app_cli import main


if __name__ == "__main__":
    main()
