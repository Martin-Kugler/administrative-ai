from __future__ import annotations

from statistics import mean
import time
from typing import Any, Dict, List

from domain.entities import AuditRequest, IngestionReport
from domain.ports import EvaluationDataset, EvaluationReport, RAGPipelinePort


class AuditApplicationService:
    """Application service orchestrating document sync and audit queries."""

    def __init__(self, pipeline: RAGPipelinePort):
        self._pipeline = pipeline

    def sync_index(self, force_reindex: bool = False) -> IngestionReport:
        return self._pipeline.sync_index(force_reindex=force_reindex)

    def run_audit(self, request: AuditRequest) -> Dict[str, Any]:
        if request.structured:
            return self._pipeline.generate_structured_audit(
                prompt=request.prompt,
                similarity_top_k=request.similarity_top_k,
                response_language=request.response_language,
            )
        return self._pipeline.query_with_sources(
            prompt=request.prompt,
            similarity_top_k=request.similarity_top_k,
            response_language=request.response_language,
        )


class EvaluationApplicationService:
    """Application service for running retrieval and answer-quality benchmarks."""

    def __init__(self, pipeline: RAGPipelinePort):
        self._pipeline = pipeline

    @staticmethod
    def _source_recall(expected_sources: List[str], predicted_sources: List[str]) -> float:
        expected = {item.strip() for item in expected_sources if item.strip()}
        if not expected:
            return 1.0

        predicted = {item.strip() for item in predicted_sources if item.strip()}
        if not predicted:
            return 0.0

        hits = len(expected.intersection(predicted))
        return hits / len(expected)

    @staticmethod
    def _keyword_coverage(expected_keywords: List[str], answer: str) -> float:
        expected = [item.strip().lower() for item in expected_keywords if item.strip()]
        if not expected:
            return 1.0

        answer_lc = answer.lower()
        matched = sum(1 for keyword in expected if keyword in answer_lc)
        return matched / len(expected)

    def run(self, dataset: EvaluationDataset, top_k: int) -> EvaluationReport:
        self._pipeline.sync_index(force_reindex=False)

        per_case_results: List[Dict[str, Any]] = []
        source_recalls: List[float] = []
        keyword_coverages: List[float] = []
        latencies: List[float] = []

        for case in dataset:
            case_id = str(case.get("id", "unknown_case"))
            question = str(case.get("question", "")).strip()
            expected_sources = [str(item) for item in case.get("expected_sources", [])]
            expected_keywords = [str(item) for item in case.get("expected_keywords", [])]

            if not question:
                continue

            start = time.perf_counter()
            response_payload = self._pipeline.query_with_sources(
                question,
                similarity_top_k=top_k,
            )
            latency_seconds = time.perf_counter() - start

            answer = str(response_payload.get("answer", ""))
            citations = response_payload.get("citations", [])
            predicted_sources = [str(citation.get("source_file", "")) for citation in citations]

            source_recall = self._source_recall(expected_sources, predicted_sources)
            keyword_coverage = self._keyword_coverage(expected_keywords, answer)

            source_recalls.append(source_recall)
            keyword_coverages.append(keyword_coverage)
            latencies.append(latency_seconds)

            per_case_results.append(
                {
                    "id": case_id,
                    "question": question,
                    "source_recall": source_recall,
                    "keyword_coverage": keyword_coverage,
                    "latency_seconds": latency_seconds,
                    "predicted_sources": predicted_sources,
                    "expected_sources": expected_sources,
                    "expected_keywords": expected_keywords,
                    "answer_preview": answer[:500],
                }
            )

        overall = {
            "cases": len(per_case_results),
            "avg_source_recall": mean(source_recalls) if source_recalls else 0.0,
            "avg_keyword_coverage": mean(keyword_coverages) if keyword_coverages else 0.0,
            "avg_latency_seconds": mean(latencies) if latencies else 0.0,
        }

        return {
            "overall": overall,
            "per_case": per_case_results,
        }
