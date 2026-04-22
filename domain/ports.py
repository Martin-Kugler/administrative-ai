from __future__ import annotations

from typing import Any, Dict, List, Protocol

from domain.entities import IngestionReport


class RAGPipelinePort(Protocol):
    """Port that defines RAG capabilities required by application services."""

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

    def query(
        self,
        prompt: str,
        similarity_top_k: int = 5,
        response_language: str = "auto",
    ) -> str:
        ...

    def count_vectors(self) -> int:
        ...


EvaluationCase = Dict[str, Any]
EvaluationReport = Dict[str, Any]
EvaluationDataset = List[EvaluationCase]
