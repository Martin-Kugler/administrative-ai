from __future__ import annotations

from typing import Any, Dict, List, Protocol

from application.models import IngestionReport


class RAGPipelinePort(Protocol):
    """Contract used by application services for RAG operations."""

    def sync_index(self, force_reindex: bool = False) -> IngestionReport:
        ...

    def query_with_sources(
        self,
        prompt: str,
        similarity_top_k: int = 5,
        response_language: str = "auto",
    ) -> Dict[str, Any]:
        ...

    def generate_structured_audit(
        self,
        prompt: str,
        similarity_top_k: int = 5,
        response_language: str = "auto",
    ) -> Dict[str, Any]:
        ...

    def query(self, prompt: str, similarity_top_k: int = 5, response_language: str = "auto") -> str:
        ...


EvaluationCase = Dict[str, Any]
EvaluationReport = Dict[str, Any]
EvaluationDataset = List[EvaluationCase]
