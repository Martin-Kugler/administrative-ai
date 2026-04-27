from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from application.services import EvaluationApplicationService


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
    from infrastructure.config import AppConfig
    from infrastructure.rag_pipeline import AuditRAGPipeline

    config = AppConfig.from_env()
    pipeline = AuditRAGPipeline(config)
    service = EvaluationApplicationService(pipeline)
    return service.run(dataset=dataset, top_k=top_k)


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