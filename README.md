# Administrative AI

Administrative AI is a local-first legal-document assistant for SMEs.
It ingests contracts and administrative documents, stores embeddings in a persistent vector database, and answers audit-oriented questions through a local LLM served by LM Studio.

## Phase 1 Status (Implemented)

This repository now includes:

- A canonical RAG pipeline for both indexing and querying.
- Environment-variable based configuration.
- Persistent local vector storage with ChromaDB.
- Incremental ingestion using file hashing (only changed files are re-indexed).
- Bootstrap-safe manifest logic to avoid accidental duplicate ingestion.
- A multilingual embedding default better suited for Spanish legal corpora.

## Architecture

1. Configuration layer
- `config.py` loads runtime settings from environment variables.

2. RAG pipeline
- `rag_pipeline.py` initializes LM Studio LLM access, embedding model, Chroma vector store, ingestion workflow, and query logic.

3. Application entrypoint
- `app.py` runs ingestion sync, prints an ingestion report, and executes a query.

4. Data directories
- `documents/` input files to ingest.
- `chroma_db/` persistent vectors and ingestion manifest.

## Project Structure

```text
administrative_ai/
├── app.py
├── config.py
├── rag_pipeline.py
├── README.md
├── environment.yml
├── .env.example
├── documents/
└── app_test.ipynb
```

## Quick Start

1. Create and activate the environment.

```bash
conda env create -f environment.yml
conda activate administrative_ai
```

2. Configure environment variables.

```bash
cp .env.example .env
```

Then export variables from `.env` in your shell (or configure them in your IDE terminal).

3. Place files under `documents/`.

4. Run the pipeline.

```bash
python app.py
```

Optional flags:

```bash
python app.py --query "List the most critical legal risks and deadlines in this contract."
python app.py --top-k 8
python app.py --reindex
```

## Incremental Ingestion Logic

- The system computes a SHA-256 hash per supported file.
- Hashes are stored in `chroma_db/ingestion_manifest.json`.
- If a file is new or modified, its previous vectors are replaced.
- If a file was removed from `documents/`, related vectors are deleted.
- If no manifest exists but vectors already exist, the manifest is bootstrapped from current files to avoid duplicate indexing.

## Supported File Extensions (Phase 1)

- `.pdf`
- `.txt`
- `.md`
- `.docx`
- `.odt`
- `.rtf`

## Recommended Environment Variables

See `.env.example` for all options.

Key variables:

- `ADMIN_AI_LMSTUDIO_BASE_URL`
- `ADMIN_AI_LLM_MODEL_NAME`
- `ADMIN_AI_EMBEDDING_MODEL_NAME`
- `ADMIN_AI_DOCUMENTS_DIR`
- `ADMIN_AI_CHROMA_PATH`
- `ADMIN_AI_CHROMA_COLLECTION_NAME`

## Notes and Limitations

- This is not legal advice. The assistant should support legal teams, not replace professional counsel.
- Retrieval quality depends heavily on chunking strategy and embedding model.
- Complex scanned PDFs may require OCR or enhanced extraction in future phases.

## Next Step After Phase 1

Phase 2 should focus on:

- Higher-fidelity ingestion (Unstructured, PyMuPDF, OCR for scans).
- Structured outputs with citations and uncertainty markers.
- Evaluation dataset and retrieval/grounding metrics.
- Streamlit interface for document upload and audit workflow.