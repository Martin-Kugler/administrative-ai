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

6. Frontend
- `streamlit_app.py` provides an interactive UI for uploads, ingestion sync, audit generation, citations, and evaluation metrics.

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

6. Launch Streamlit frontend.

```bash
streamlit run streamlit_app.py
```

The frontend includes these tabs:

- `Ingestion`: upload files and trigger sync/reindex.
- `Audit`: run structured or plain responses with citations and JSON export.
- `Evaluation`: execute dataset benchmarks and visualize KPIs.
- `System`: inspect vector count, source files, and runtime config.
- `Feedback`: collect user feedback (rating + comments) and store it as JSONL.
- `Admin Review`: inspect feedback metrics and recent application logs from the UI (requires auth enabled).

## Beta Hardening Features

- Optional login gate for closed beta access.
- Structured app logging with rotating log files.
- In-app feedback capture for rapid iteration.

### Enable Closed Beta Auth

Set these variables in `.env`:

```bash
ADMIN_AI_AUTH_ENABLED=true
ADMIN_AI_AUTH_USERNAME=admin
ADMIN_AI_AUTH_PASSWORD=change_me_now
```

When enabled, users must sign in before using the app.

### Feedback and Logs

```bash
ADMIN_AI_FEEDBACK_PATH=./results/feedback.jsonl
ADMIN_AI_LOG_PATH=./logs/app.log
```

- Feedback is appended as one JSON object per line.
- Logs rotate automatically to keep file size bounded.

### What Is Admin Review?

`Admin Review` is an internal QA/operations panel designed for beta rollout.

- Shows feedback KPIs (count, average rating, unique sessions).
- Lets you filter feedback by category.
- Displays recent feedback entries in a table.
- Shows recent log lines to quickly spot runtime issues.

This helps close the loop between user feedback and technical errors without leaving the app.

## Benchmark Pack and Example Documents

The repository includes a synthetic benchmark pack for safe, repeatable validation:

- Example docs in `documents/example_pack/`
	- `contrato_servicios_alpha.txt`
	- `politica_compras_beta.md`
	- `acuerdo_confidencialidad_gamma.md`
	- `protocolo_incidentes_delta.txt`
	- `anexo_mantenimiento_epsilon.pdf`
	- `contrato_licencia_zeta.pdf`
- Benchmark dataset in `evaluation/benchmark_suite_v1.json` (12 cases).

If you want to regenerate the synthetic PDFs:

```bash
python scripts/generate_example_pdfs.py
```

Run benchmark:

```bash
python evaluation.py --dataset evaluation/benchmark_suite_v1.json --top-k 5 --output results/benchmark_v1_report.json
```

Recommended flow:

1. Run `streamlit run streamlit_app.py`.
2. In `Ingestion`, click `Force reindex` to ingest `documents/example_pack/`.
3. In `Evaluation`, set dataset path to `evaluation/benchmark_suite_v1.json` and run evaluation.
4. Review KPIs and per-case outputs.

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
- `ADMIN_AI_AUTH_ENABLED`
- `ADMIN_AI_AUTH_USERNAME`
- `ADMIN_AI_AUTH_PASSWORD`
- `ADMIN_AI_FEEDBACK_PATH`
- `ADMIN_AI_LOG_PATH`

## Notes

- This system provides legal-assistant support and is not legal advice.
- For scanned PDFs, OCR support should be added in a subsequent iteration.
- Retrieval quality depends on embeddings, chunking, and document quality.

## Next Step

With the Streamlit MVP in place, the next milestone is product hardening:

- Add authentication and per-client workspace isolation.
- Add stronger regression evaluation with a larger benchmark set.
- Improve extraction for scanned PDFs with OCR.
- Add production logging and monitoring for audit traceability.