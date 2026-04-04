from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
import time
from typing import Any, Dict, List

from dotenv import load_dotenv

from config import AppConfig
from rag_pipeline import AuditRAGPipeline


def _source_recall(expected_sources: List[str], predicted_sources: List[str]) -> float:
    expected = {item.strip() for item in expected_sources if item.strip()}
    if not expected:
        return 1.0

    predicted = {item.strip() for item in predicted_sources if item.strip()}
    if not predicted:
        return 0.0

    hits = len(expected.intersection(predicted))
    return hits / len(expected)


def _keyword_coverage(expected_keywords: List[str], answer: str) -> float:
    expected = [item.strip().lower() for item in expected_keywords if item.strip()]
    if not expected:
        return 1.0

    answer_lc = answer.lower()
    matched = sum(1 for keyword in expected if keyword in answer_lc)
    return matched / len(expected)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 2 baseline evaluation.")
    parser.add_argument(
        "--dataset",
        type=str,
        default="evaluation/sample_eval_dataset.json",
        help="Path to evaluation dataset JSON file.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Retriever top-k used for each evaluation query.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/eval_report.json",
        help="Path to save the evaluation report.",
    )
    return parser


def _load_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    with dataset_path.open("r", encoding="utf-8") as stream:
        dataset = json.load(stream)

    if not isinstance(dataset, list):
        raise ValueError("Dataset must be a list of test cases.")

    return dataset


def run_evaluation(dataset: List[Dict[str, Any]], top_k: int) -> Dict[str, Any]:
    config = AppConfig.from_env()
    pipeline = AuditRAGPipeline(config)
    pipeline.sync_index(force_reindex=False)

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
        response_payload = pipeline.query_with_sources(question, similarity_top_k=top_k)
        latency_seconds = time.perf_counter() - start

        answer = str(response_payload.get("answer", ""))
        citations = response_payload.get("citations", [])
        predicted_sources = [str(citation.get("source_file", "")) for citation in citations]

        source_recall = _source_recall(expected_sources, predicted_sources)
        keyword_coverage = _keyword_coverage(expected_keywords, answer)

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


def main() -> None:
    load_dotenv()
    args = _build_parser().parse_args()

    dataset_path = Path(args.dataset).resolve()
    output_path = Path(args.output).resolve()

    dataset = _load_dataset(dataset_path)
    report = run_evaluation(dataset=dataset, top_k=args.top_k)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)

    print(json.dumps(report["overall"], indent=2, ensure_ascii=False))
    print(f"Saved report to: {output_path}")


if __name__ == "__main__":
    main()