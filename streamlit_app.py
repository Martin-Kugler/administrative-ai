"""Backward-compatible Streamlit entrypoint.

Canonical location: presentation.web.streamlit_ui
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from presentation.web.streamlit_ui import *  # noqa: F401,F403
