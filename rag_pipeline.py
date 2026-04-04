from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Dict, List

import chromadb
from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

from config import AppConfig


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".odt", ".rtf"}


@dataclass
class IngestionReport:
    indexed_files: List[str] = field(default_factory=list)
    removed_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    failed_files: Dict[str, str] = field(default_factory=dict)
    manifest_bootstrapped: bool = False


class AuditRAGPipeline:
    def __init__(self, config: AppConfig):
        self.config = config
        self.config.chroma_path.mkdir(parents=True, exist_ok=True)
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
        self.db_client = chromadb.PersistentClient(path=str(self.config.chroma_path))
        self.collection = self.db_client.get_or_create_collection(self.config.collection_name)
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = self._build_index_from_vector_store()

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
                documents = SimpleDirectoryReader(input_files=[str(absolute_path)]).load_data()
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

    def query(self, prompt: str, similarity_top_k: int = 5) -> str:
        if self.collection.count() == 0:
            raise RuntimeError("Index is empty. Add documents before querying.")

        query_engine = self.index.as_query_engine(similarity_top_k=similarity_top_k)
        response = query_engine.query(prompt)
        return str(response)