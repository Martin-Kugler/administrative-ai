from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List

import numpy as np

# Work around protobuf/opentelemetry incompatibilities in some local environments.
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import chromadb
from chromadb.config import Settings as ChromaClientSettings
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

from domain.entities import IngestionReport
from infrastructure.config import AppConfig
from infrastructure.ingestion import (
    DocumentIngestionService,
    SUPPORTED_EXTENSIONS,
)


# NumPy 2 removed legacy aliases that some transitive dependencies may still reference.
if not hasattr(np, "float_"):
    setattr(np, "float_", np.float64)


class AuditRAGPipeline:
    def __init__(self, config: AppConfig):
        self.config = config
        self.config.chroma_path.mkdir(parents=True, exist_ok=True)
        self.recovered_from_schema_mismatch = False
        self.schema_backup_path: str | None = None
        self.ingestion_service = DocumentIngestionService(
            backend=self.config.ingestion_backend,
            unstructured_chunk_chars=self.config.unstructured_chunk_chars,
        )
        self._configure_settings()
        self._initialize_vector_store()

    def _configure_settings(self) -> None:
        Settings.llm = OpenAI(
            api_base=self.config.lmstudio_base_url,
            api_key=self.config.lmstudio_api_key,
            model_name=self.config.llm_model_name,
            temperature=self.config.llm_temperature,
        )
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=self.config.embedding_model_name
        )
        Settings.chunk_size = self.config.chunk_size
        Settings.chunk_overlap = self.config.chunk_overlap

    def _initialize_vector_store(self) -> None:
        db_path = str(self.config.chroma_path)
        try:
            self.db_client = self._build_db_client(db_path)
            self.collection = self.db_client.get_or_create_collection(self.config.collection_name)
        except Exception as error:
            message = str(error).lower()
            incompatible_schema = (
                "collections.topic" in message and "no such column" in message
            )

            if not incompatible_schema:
                raise

            backup_path = self._backup_incompatible_chroma_db()
            self.recovered_from_schema_mismatch = True
            self.schema_backup_path = str(backup_path)

            self._clear_chroma_shared_cache(db_path)

            self.db_client = self._build_db_client(db_path)
            self.collection = self.db_client.get_or_create_collection(self.config.collection_name)

        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = self._build_index_from_vector_store()

    def _backup_incompatible_chroma_db(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config.chroma_path.with_name(
            f"{self.config.chroma_path.name}_backup_{timestamp}"
        )

        if self.config.chroma_path.exists():
            shutil.move(str(self.config.chroma_path), str(backup_path))

        self.config.chroma_path.mkdir(parents=True, exist_ok=True)
        return backup_path

    @staticmethod
    def _build_db_client(db_path: str):
        settings = ChromaClientSettings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True,
            persist_directory=db_path,
        )
        return chromadb.PersistentClient(path=db_path, settings=settings)

    @staticmethod
    def _clear_chroma_shared_cache(identifier: str) -> None:
        try:
            import importlib

            module = None
            try:
                module = importlib.import_module("chromadb.api.shared_system_client")
            except Exception:
                module = importlib.import_module("chromadb.api.client")

            SharedSystemClient = getattr(module, "SharedSystemClient", None)
            if SharedSystemClient is None:
                return

            cache = getattr(SharedSystemClient, "_identifier_to_system", None)
            if isinstance(cache, dict):
                cache.pop(identifier, None)
        except Exception:
            pass

    def _build_index_from_vector_store(self) -> VectorStoreIndex:
        try:
            return VectorStoreIndex.from_vector_store(vector_store=self.vector_store)
        except Exception:
            return VectorStoreIndex(nodes=[], storage_context=self.storage_context)

    def _reset_collection(self) -> None:
        try:
            self.db_client.delete_collection(self.config.collection_name)
        except Exception:
            pass

        self.collection = self.db_client.get_or_create_collection(self.config.collection_name)
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = self._build_index_from_vector_store()

    def _list_source_files(self) -> List[Path]:
        if not self.config.documents_dir.exists():
            return []

        files: List[Path] = []
        for path in self.config.documents_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)
        return sorted(files)

    @staticmethod
    def _hash_file(file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _compute_current_hashes(self) -> Dict[str, str]:
        hashes: Dict[str, str] = {}
        for absolute_path in self._list_source_files():
            relative_path = str(absolute_path.relative_to(self.config.documents_dir))
            hashes[relative_path] = self._hash_file(absolute_path)
        return hashes

    def _load_manifest(self) -> Dict[str, str]:
        if not self.config.manifest_path.exists():
            return {}

        try:
            with self.config.manifest_path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        except (OSError, json.JSONDecodeError):
            return {}

        if not isinstance(data, dict):
            return {}

        return {str(key): str(value) for key, value in data.items()}

    def _save_manifest(self, manifest: Dict[str, str]) -> None:
        self.config.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config.manifest_path.open("w", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True)

    def sync_index(self, force_reindex: bool = False) -> IngestionReport:
        if force_reindex:
            self._reset_collection()

        report = IngestionReport()
        previous_manifest = {} if force_reindex else self._load_manifest()
        current_hashes = self._compute_current_hashes()

        if not current_hashes and self.collection.count() == 0:
            raise RuntimeError(
                f"No supported documents found in '{self.config.documents_dir}'. "
                f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
            )

        if not previous_manifest and self.collection.count() > 0 and not force_reindex:
            self._save_manifest(current_hashes)
            report.manifest_bootstrapped = True
            return report

        changed_files = sorted(
            path
            for path, file_hash in current_hashes.items()
            if previous_manifest.get(path) != file_hash
        )
        removed_files = sorted(
            path for path in previous_manifest.keys() if path not in current_hashes
        )

        next_manifest = {
            path: file_hash
            for path, file_hash in previous_manifest.items()
            if path not in removed_files
        }

        for relative_path in removed_files:
            self.collection.delete(where={"source_file": relative_path})
            report.removed_files.append(relative_path)

        for relative_path in changed_files:
            absolute_path = self.config.documents_dir / relative_path

            try:
                documents = self.ingestion_service.load_documents(
                    file_path=absolute_path,
                    relative_path=relative_path,
                )
                if not documents:
                    report.skipped_files.append(relative_path)
                    next_manifest.pop(relative_path, None)
                    continue

                for document in documents:
                    document.metadata["source_file"] = relative_path
                    document.metadata["source_hash"] = current_hashes[relative_path]

                self.collection.delete(where={"source_file": relative_path})
                for document in documents:
                    self.index.insert(document)

                next_manifest[relative_path] = current_hashes[relative_path]
                report.indexed_files.append(relative_path)
            except Exception as error:
                report.failed_files[relative_path] = str(error)
                next_manifest.pop(relative_path, None)

        unchanged_files = {
            path: file_hash
            for path, file_hash in current_hashes.items()
            if path not in changed_files
        }
        next_manifest.update(unchanged_files)
        self._save_manifest(next_manifest)

        self.index = self._build_index_from_vector_store()
        return report

    def count_vectors(self) -> int:
        return int(self.collection.count())

    def _extract_citations(self, response: Any) -> List[Dict[str, Any]]:
        source_nodes = getattr(response, "source_nodes", []) or []
        citations: List[Dict[str, Any]] = []
        seen_sources = set()

        for node_with_score in source_nodes:
            if len(citations) >= self.config.max_citations:
                break

            node = getattr(node_with_score, "node", None)
            metadata = dict(getattr(node, "metadata", {}) or {})

            source_file = str(metadata.get("source_file", "unknown"))
            source_page = metadata.get("source_page") or metadata.get("page_label") or metadata.get("page")
            source_key = (source_file, str(source_page))

            if source_key in seen_sources:
                continue
            seen_sources.add(source_key)

            score_value = getattr(node_with_score, "score", None)
            try:
                score = float(score_value) if score_value is not None else None
            except (TypeError, ValueError):
                score = None

            snippet = ""
            if node is not None:
                try:
                    snippet = node.get_content()
                except Exception:
                    snippet = ""

            snippet = " ".join(snippet.split())
            if len(snippet) > 300:
                snippet = f"{snippet[:297]}..."

            citations.append(
                {
                    "source_file": source_file,
                    "source_page": source_page,
                    "score": score,
                    "snippet": snippet,
                }
            )

        return citations

    @staticmethod
    def _safe_parse_structured_json(response_text: str) -> Dict[str, Any] | None:
        candidate = response_text.strip()
        if candidate.startswith("```"):
            lines = candidate.splitlines()
            if len(lines) >= 3 and lines[0].startswith("```"):
                candidate = "\n".join(lines[1:-1]).strip()

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None

            try:
                parsed = json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                return None

        if not isinstance(parsed, dict):
            return None
        return parsed

    @staticmethod
    def _coerce_list_of_strings(value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if value is None:
            return []

        text = str(value).strip()
        return [text] if text else []

    def _normalize_structured_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {
            "executive_summary": str(payload.get("executive_summary", "")).strip(),
            "key_risks": self._coerce_list_of_strings(payload.get("key_risks", [])),
            "critical_deadlines": self._coerce_list_of_strings(payload.get("critical_deadlines", [])),
            "recommended_actions": self._coerce_list_of_strings(payload.get("recommended_actions", [])),
            "uncertainty_notes": str(payload.get("uncertainty_notes", "")).strip(),
        }
        return normalized

    @staticmethod
    def _detect_prompt_language(prompt: str) -> str:
        text = prompt.lower()
        spanish_markers = re.findall(
            r"\b(el|la|los|las|de|del|que|con|para|como|contrato|clausula|riesgo|plazo|auditoria|documento)\b",
            text,
        )
        english_markers = re.findall(
            r"\b(the|and|for|with|that|contract|clause|risk|deadline|audit|document)\b",
            text,
        )

        has_spanish_symbols = any(char in text for char in "\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00bf\u00a1")
        if has_spanish_symbols or (len(spanish_markers) >= 2 and len(spanish_markers) >= len(english_markers)):
            return "es"
        return "en"

    def _resolve_response_language(self, prompt: str, response_language: str) -> str:
        normalized = (response_language or "auto").strip().lower()
        if normalized in {"es", "en"}:
            return normalized
        return self._detect_prompt_language(prompt)

    @staticmethod
    def _get_language_instruction(language: str) -> str:
        if language == "es":
            return "Respond in Spanish. Keep legal terms and proper names exactly as they appear in source documents."
        return "Respond in English. Keep legal terms and proper names exactly as they appear in source documents."

    def query_with_sources(
        self,
        prompt: str,
        similarity_top_k: int = 5,
        response_language: str = "auto",
    ) -> Dict[str, Any]:
        if self.collection.count() == 0:
            raise RuntimeError("Index is empty. Add documents before querying.")

        effective_language = self._resolve_response_language(prompt, response_language)
        language_instruction = self._get_language_instruction(effective_language)
        query_prompt = f"{language_instruction}\n\nUser request:\n{prompt.strip()}"

        query_engine = self.index.as_query_engine(similarity_top_k=similarity_top_k)
        response = query_engine.query(query_prompt)

        return {
            "answer": str(response),
            "citations": self._extract_citations(response),
            "response_language": effective_language,
        }

    def generate_structured_audit(
        self,
        prompt: str,
        similarity_top_k: int = 5,
        response_language: str = "auto",
    ) -> Dict[str, Any]:
        effective_language = self._resolve_response_language(prompt, response_language)
        language_schema_instruction = (
            "All string values must be in Spanish." if effective_language == "es" else "All string values must be in English."
        )
        schema_instruction = (
            "Return strict JSON with these keys only: "
            "executive_summary (string), "
            "key_risks (array of strings), "
            "critical_deadlines (array of strings), "
            "recommended_actions (array of strings), "
            "uncertainty_notes (string). "
            "Use only retrieved evidence. If evidence is weak or missing, explain it in uncertainty_notes. "
            "Do not include markdown code fences."
        )
        combined_prompt = (
            "You are an assistant for SME legal-document audits. "
            f"{schema_instruction} {language_schema_instruction}\n\n"
            f"User request: {prompt}"
        )

        payload = self.query_with_sources(
            combined_prompt,
            similarity_top_k=similarity_top_k,
            response_language=effective_language,
        )
        parsed_payload = self._safe_parse_structured_json(payload["answer"]) or {}
        normalized = self._normalize_structured_payload(parsed_payload)

        if not normalized["executive_summary"]:
            normalized["executive_summary"] = payload["answer"].strip()

        if not normalized["uncertainty_notes"]:
            if effective_language == "es":
                normalized[
                    "uncertainty_notes"
                ] = "Generado solo con fragmentos recuperados; si faltan evidencias o son de baja calidad, la respuesta puede ser incompleta."
            else:
                normalized[
                    "uncertainty_notes"
                ] = "Generated from retrieved chunks only; missing or low-quality source text may reduce completeness."

        normalized["citations"] = payload["citations"]
        normalized["response_language"] = effective_language
        return normalized

    def query(self, prompt: str, similarity_top_k: int = 5, response_language: str = "auto") -> str:
        return str(
            self.query_with_sources(
                prompt,
                similarity_top_k=similarity_top_k,
                response_language=response_language,
            )["answer"]
        )