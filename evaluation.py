"""Backward-compatible facade for evaluation entrypoint.

Canonical location: presentation.cli.evaluation_cli
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from presentation.cli.evaluation_cli import main, run_evaluation

__all__ = ["main", "run_evaluation"]


if __name__ == "__main__":
    main()
