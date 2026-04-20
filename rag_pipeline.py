"""Backward-compatible facade for RAG pipeline imports.

The canonical implementation now lives in administrative_ai.infrastructure.rag_pipeline.
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from administrative_ai.domain.entities import IngestionReport
from administrative_ai.infrastructure.rag_pipeline import AuditRAGPipeline

__all__ = ["AuditRAGPipeline", "IngestionReport"]