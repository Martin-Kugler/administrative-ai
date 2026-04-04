from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _to_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _to_int(value: str | None, default: int) -> int:
    if value is None:
        return default


def _to_str(value: str | None, default: str) -> str:
    if value is None:
        return default

    cleaned = value.strip()
    return cleaned or default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    lmstudio_base_url: str
    lmstudio_api_key: str
    llm_model_name: str
    llm_temperature: float
    embedding_model_name: str
    documents_dir: Path
    chroma_path: Path
    collection_name: str
    manifest_path: Path
    default_query: str
    chunk_size: int
    chunk_overlap: int
    ingestion_backend: str
    unstructured_chunk_chars: int
    max_citations: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        documents_dir = Path(
            os.getenv("ADMIN_AI_DOCUMENTS_DIR", "./documents")
        ).resolve()
        chroma_path = Path(
            os.getenv("ADMIN_AI_CHROMA_PATH", "./chroma_db")
        ).resolve()
        manifest_path = Path(
            os.getenv(
                "ADMIN_AI_MANIFEST_PATH",
                str(chroma_path / "ingestion_manifest.json"),
            )
        ).resolve()

        return cls(
            lmstudio_base_url=os.getenv(
                "ADMIN_AI_LMSTUDIO_BASE_URL",
                "http://172.26.224.1:1234/v1",
            ),
            lmstudio_api_key=os.getenv("ADMIN_AI_LMSTUDIO_API_KEY", "lm-studio"),
            llm_model_name=os.getenv(
                "ADMIN_AI_LLM_MODEL_NAME",
                "llama-3.1-8b-instruct",
            ),
            llm_temperature=_to_float(os.getenv("ADMIN_AI_LLM_TEMPERATURE"), 0.1),
            embedding_model_name=os.getenv(
                "ADMIN_AI_EMBEDDING_MODEL_NAME",
                "intfloat/multilingual-e5-base",
            ),
            documents_dir=documents_dir,
            chroma_path=chroma_path,
            collection_name=os.getenv(
                "ADMIN_AI_CHROMA_COLLECTION_NAME",
                "auditoria_pymes",
            ),
            manifest_path=manifest_path,
            default_query=os.getenv(
                "ADMIN_AI_DEFAULT_QUERY",
                (
                    "Provide an executive summary of this contract and list critical "
                    "termination clauses and penalties."
                ),
            ),
            chunk_size=_to_int(os.getenv("ADMIN_AI_CHUNK_SIZE"), 1024),
            chunk_overlap=_to_int(os.getenv("ADMIN_AI_CHUNK_OVERLAP"), 100),
            ingestion_backend=_to_str(
                os.getenv("ADMIN_AI_INGESTION_BACKEND"),
                "auto",
            ).lower(),
            unstructured_chunk_chars=_to_int(
                os.getenv("ADMIN_AI_UNSTRUCTURED_CHUNK_CHARS"),
                1800,
            ),
            max_citations=_to_int(os.getenv("ADMIN_AI_MAX_CITATIONS"), 6),
        )