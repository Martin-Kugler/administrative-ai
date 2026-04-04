import argparse

from config import AppConfig
from rag_pipeline import AuditRAGPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Administrative AI - local legal audit assistant (Phase 1)."
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Question sent to the RAG engine. If omitted, the default query is used.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to retrieve from the vector store.",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Delete existing vectors and rebuild the index from documents.",
    )
    return parser


def print_ingestion_report(report) -> None:
    print("\n--- INGESTION REPORT ---")
    if report.manifest_bootstrapped:
        print("Manifest bootstrapped from current files and existing vector store.")

    print(f"Indexed files: {len(report.indexed_files)}")
    for path in report.indexed_files:
        print(f"  + {path}")

    print(f"Removed files: {len(report.removed_files)}")
    for path in report.removed_files:
        print(f"  - {path}")

    print(f"Skipped files: {len(report.skipped_files)}")
    for path in report.skipped_files:
        print(f"  ~ {path}")

    print(f"Failed files: {len(report.failed_files)}")
    for path, error in report.failed_files.items():
        print(f"  ! {path}: {error}")


def main() -> None:
    args = build_parser().parse_args()
    config = AppConfig.from_env()

    pipeline = AuditRAGPipeline(config)
    report = pipeline.sync_index(force_reindex=args.reindex)
    print_ingestion_report(report)

    query = args.query or config.default_query
    print("\n--- QUERY ---")
    print(query)

    response = pipeline.query(prompt=query, similarity_top_k=args.top_k)
    print("\n--- AUDIT RESULT ---")
    print(response)


if __name__ == "__main__":
    main()