from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".odt", ".rtf"}


@dataclass
class DocumentIngestionService:
    backend: str = "auto"
    unstructured_chunk_chars: int = 1800

    def load_documents(self, file_path: Path, relative_path: str) -> List[Document]:
        suffix = file_path.suffix.lower()

        if suffix == ".pdf" and self.backend in {"auto", "pymupdf"}:
            documents = self._load_pdf_with_pymupdf(file_path, relative_path)
            if documents:
                return documents

        if self.backend in {"auto", "unstructured"}:
            documents = self._load_with_unstructured(file_path, relative_path)
            if documents:
                return documents

        return self._load_with_simple_reader(file_path, relative_path)

    def _load_pdf_with_pymupdf(self, file_path: Path, relative_path: str) -> List[Document]:
        try:
            import fitz
        except Exception:
            return []

        documents: List[Document] = []
        pdf = fitz.open(str(file_path))
        try:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()
                if not text:
                    continue

                documents.append(
                    Document(
                        text=text,
                        metadata={
                            "source_file": relative_path,
                            "source_page": page_number,
                            "parser": "pymupdf",
                        },
                    )
                )
        finally:
            pdf.close()

        return documents

    def _load_with_unstructured(self, file_path: Path, relative_path: str) -> List[Document]:
        try:
            from unstructured.partition.auto import partition
        except Exception:
            return []

        try:
            elements = partition(filename=str(file_path))
        except Exception:
            return []

        chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for element in elements:
            text = str(element).strip()
            if not text:
                continue

            line_len = len(text) + 1
            if current_chunk and (current_len + line_len > self.unstructured_chunk_chars):
                chunks.append("\n".join(current_chunk))
                current_chunk = [text]
                current_len = line_len
            else:
                current_chunk.append(text)
                current_len += line_len

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        documents: List[Document] = []
        for chunk_index, chunk_text in enumerate(chunks, start=1):
            documents.append(
                Document(
                    text=chunk_text,
                    metadata={
                        "source_file": relative_path,
                        "chunk_index": chunk_index,
                        "parser": "unstructured",
                    },
                )
            )

        return documents

    def _load_with_simple_reader(self, file_path: Path, relative_path: str) -> List[Document]:
        documents = SimpleDirectoryReader(input_files=[str(file_path)]).load_data()

        for document in documents:
            document.metadata.setdefault("source_file", relative_path)
            document.metadata.setdefault("parser", "llama_simple_reader")

        return documents