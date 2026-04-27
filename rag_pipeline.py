"""Backward-compatible facade for RAG pipeline.

Canonical location: infrastructure.rag_pipeline
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from application.models import IngestionReport
from infrastructure.rag_pipeline import AuditRAGPipeline

__all__ = ["AuditRAGPipeline", "IngestionReport"]
