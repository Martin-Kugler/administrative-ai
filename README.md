# Administrative AI

Administrative AI is a local-first legal-document assistant for SMEs.
It ingests contracts and administrative documents, stores embeddings in a persistent vector database, and answers audit-oriented questions through a local LLM served by LM Studio.

## Phase 2 Backend Status (Implemented)

Current backend capabilities:

- Canonical RAG pipeline with persistent local Chroma storage.
- Incremental ingestion based on file hashing and manifest tracking.
- Ingestion backend abstraction with support for PyMuPDF and optional Unstructured.
- Structured audit output mode with citations and uncertainty notes.
- Environment-variable based configuration.
- Baseline evaluation script and sample dataset.

## Core Architecture

1. Configuration
- `config.py` centralizes runtime configuration from environment variables.

2. Ingestion
- `document_ingestion.py` loads documents with backend fallback strategy:
	- PyMuPDF for PDF page extraction.
	- Unstructured (optional) for richer parsing.
	- LlamaIndex simple reader as safe fallback.

3. RAG engine
- `rag_pipeline.py` orchestrates embedding, vector persistence, ingestion sync, retrieval, and structured audit generation.

4. CLI entrypoint
- `app.py` runs sync + query and can emit plain or structured output.

5. Evaluation
- `evaluation.py` runs a baseline benchmark and writes a JSON report.

## Quick Start

1. Create and activate environment.

```bash
conda env create -f environment.yml
conda activate administrative_ai
```

2. Configure runtime variables.

```bash
cp .env.example .env
```

3. Run standard structured audit mode.

```bash
python app.py
```

4. Useful CLI variants.

```bash
python app.py --reindex
python app.py --plain-text
python app.py --query "List critical deadlines and required actions." --top-k 8
python app.py --output-file results/latest_audit.json
```

5. Run evaluation.

```bash
python evaluation.py
python evaluation.py --dataset evaluation/sample_eval_dataset.json --top-k 8 --output results/eval_report.json
```

## Incremental Ingestion Behavior

- Computes SHA-256 per source document.
- Stores hashes in `chroma_db/ingestion_manifest.json`.
- Re-indexes only new/changed files.
- Removes vectors for files no longer present.
- Supports manifest bootstrapping when vectors already exist.

## Supported Extensions

- `.pdf`
- `.txt`
- `.md`
- `.docx`
- `.odt`
- `.rtf`

## Environment Variables

See `.env.example` for full list.

Most relevant:

- `ADMIN_AI_LMSTUDIO_BASE_URL`
- `ADMIN_AI_LLM_MODEL_NAME`
- `ADMIN_AI_EMBEDDING_MODEL_NAME`
- `ADMIN_AI_DOCUMENTS_DIR`
- `ADMIN_AI_CHROMA_PATH`
- `ADMIN_AI_CHROMA_COLLECTION_NAME`
- `ADMIN_AI_INGESTION_BACKEND` (`auto`, `pymupdf`, `unstructured`)
- `ADMIN_AI_UNSTRUCTURED_CHUNK_CHARS`
- `ADMIN_AI_MAX_CITATIONS`

## Notes

- This system provides legal-assistant support and is not legal advice.
- For scanned PDFs, OCR support should be added in a subsequent iteration.
- Retrieval quality depends on embeddings, chunking, and document quality.

## Next Step

After backend hardening and test coverage, proceed with a Streamlit frontend for:

- Multi-file upload and ingestion status.
- Structured audit visualization.
- Citation browsing and export.
- Evaluation dashboard.