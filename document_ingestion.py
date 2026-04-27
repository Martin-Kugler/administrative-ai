"""Backward-compatible facade for ingestion service.

Canonical location: infrastructure.document_ingestion
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from infrastructure.document_ingestion import DocumentIngestionService, SUPPORTED_EXTENSIONS

__all__ = ["DocumentIngestionService", "SUPPORTED_EXTENSIONS"]
