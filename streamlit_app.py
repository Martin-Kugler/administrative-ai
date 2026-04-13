from __future__ import annotations

from datetime import datetime
import html
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
import streamlit as st

from config import AppConfig
from evaluation import run_evaluation

from rag_pipeline import AuditRAGPipeline, IngestionReport


BASE_DIR = Path(__file__).resolve().parent


def apply_custom_theme() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@400;500;600&display=swap');

            :root {
                --bg: #0d1117;
                --ink: #c9d1d9;
                --accent: #58a6ff;
                --card: #161b22;
                --muted: #8b949e;
                --border: #30363d;
            }

            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
                color: var(--ink) !important;
            }

            /* Forzar el color de fondo en toda la app para eliminar cualquier rastro beis/claro */
            .stApp, [data-testid="stAppViewContainer"] {
                background-color: var(--bg) !important;
                background: var(--bg) !important;
            }

            /* Cabecera superior oscura y difuminada (top header) */
            [data-testid="stHeader"] {
                background-color: rgba(13, 17, 23, 0.85) !important;
                background: rgba(13, 17, 23, 0.85) !important;
                backdrop-filter: blur(12px) !important;
            }

            /* Ocultar la barrita de colores superior (decoration) */
            [data-testid="stDecoration"] {
                display: none !important;
            }

            h1, h2, h3, h4, h5, h6 {
                font-family: 'Inter', sans-serif !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                letter-spacing: 0.2px;
            }

            [data-testid="stSidebar"] {
                background-color: var(--card) !important;
                border-right: 1px solid var(--border) !important;
            }

            .hero {
                background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 1.5rem 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            }

            .hero h1 {
                font-family: 'Fira Code', monospace !important;
                color: var(--accent) !important;
                margin-bottom: 0.5rem;
            }

            .hero p {
                margin: 0;
                color: var(--muted);
                max-width: 80ch;
                line-height: 1.6;
                font-size: 1.05rem;
            }

            .card {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 10px;
                padding: 1.25rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                margin-bottom: 1rem;
            }

            .card h3 {
                margin-top: 0;
                margin-bottom: 0.75rem;
                font-size: 1.25rem !important;
                color: var(--accent) !important;
                border-bottom: 1px solid var(--border);
                padding-bottom: 0.5rem;
            }

            .card p, .card li {
                color: var(--ink);
                line-height: 1.5;
            }

            .fade-in {
                animation: fadeInUp 0.45s ease-out;
            }

            [data-testid="stMarkdownContainer"],
            [data-testid="stText"],
            label,
            p,
            span,
            li {
                color: var(--ink) !important;
            }

            /* Estilos para inputs */
            [data-testid="stTextInput"] div[data-baseweb="input"],
            [data-testid="stTextArea"] div[data-baseweb="textarea"],
            [data-testid="stNumberInput"] div[data-baseweb="input"] {
                background-color: #010409 !important;
                border: 1px solid var(--border) !important;
                border-radius: 6px !important;
            }

            [data-testid="stTextInput"] input,
            [data-testid="stTextArea"] textarea,
            [data-testid="stNumberInput"] input {
                color: #c9d1d9 !important;
                -webkit-text-fill-color: #c9d1d9 !important;
                background-color: transparent !important;
                font-family: 'Fira Code', monospace !important;
            }

            [data-testid="stTextInput"] input::placeholder,
            [data-testid="stTextArea"] textarea::placeholder {
                color: #484f58 !important;
                -webkit-text-fill-color: #484f58 !important;
            }

            /* Selectors, Popovers y Tabs */
            [data-baseweb="select"] > div {
                background-color: #010409 !important;
                border-color: var(--border) !important;
            }

            [data-baseweb="select"] * {
                color: var(--ink) !important;
            }

            [data-baseweb="popover"], div[role="listbox"] {
                background-color: var(--card) !important;
                border: 1px solid var(--border) !important;
            }

            [data-baseweb="tab-list"] {
                background-color: transparent !important;
                border-bottom: 1px solid var(--border) !important;
                gap: 1rem !important;
            }
            
            [data-baseweb="tab"] {
                background-color: transparent !important;
                color: var(--muted) !important;
                padding: 0.5rem 1rem !important;
            }
            
            [data-baseweb="tab"][aria-selected="true"] {
                color: var(--accent) !important;
                border-bottom: 2px solid var(--accent) !important;
            }

            /* Botones */
            [data-testid="stDownloadButton"] button,
            [data-testid="stButton"] button {
                color: #ffffff !important;
                background: linear-gradient(180deg, #1f6feb 0%, #1754bb 100%) !important;
                border: 1px solid rgba(240, 246, 252, 0.1) !important;
                border-radius: 6px !important;
                font-family: 'Fira Code', monospace !important;
                font-weight: 500 !important;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
                padding: 0.25rem 1rem !important;
            }

            [data-testid="stDownloadButton"] button:hover,
            [data-testid="stButton"] button:hover {
                border-color: #8b949e !important;
                background: #1f6feb !important;
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
                transition: all 0.2s ease-in-out;
            }

            /* Alertas y Mensajes (st.info, st.warning, st.success, st.error) */
            [data-testid="stAlert"] {
                background-color: var(--card) !important;
                color: #ffffff !important;
                border: 1px solid var(--border) !important;
                border-radius: 8px !important;
            }
            
            [data-testid="stAlert"] * {
                color: #ffffff !important;
            }

            /* Expandables (st.expander) */
            [data-testid="stExpander"] details {
                background-color: var(--card) !important;
                border: 1px solid var(--border) !important;
                border-radius: 8px !important;
            }
            
            [data-testid="stExpander"] summary {
                background-color: var(--card) !important;
                color: #ffffff !important;
            }
            
            [data-testid="stExpander"] summary:hover {
                color: var(--accent) !important;
            }
            
            [data-testid="stExpander"] * {
                color: var(--ink) !important;
            }

            /* Componente Dropzone (Subir archivos) */
            [data-testid="stFileUploadDropzone"] {
                background-color: #010409 !important;
                border: 1px dashed var(--muted) !important;
            }
            
            [data-testid="stFileUploadDropzone"] * {
                color: #ffffff !important;
            }

            /* Dataframes (Tablas de resultados) y Métricas */
            [data-testid="stDataFrame"] div[data-baseweb="table"] {
                background-color: var(--card) !important;
            }
            
            [data-testid="stDataFrame"] * {
                color: var(--ink) !important;
                border-color: var(--border) !important;
            }
            
            [data-testid="stMetricValue"] {
                color: #ffffff !important;
            }

            /* Código fuente y bloques de texto preformateados */
            code, pre {
                background-color: #010409 !important;
                color: var(--accent) !important;
                border: 1px solid var(--border) !important;
                border-radius: 6px !important;
            }

            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @media (max-width: 900px) {
                .hero {
                    padding: 1rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_config_signature(config: AppConfig) -> str:
    return json.dumps(
        {
            "lmstudio_base_url": config.lmstudio_base_url,
            "llm_model_name": config.llm_model_name,
            "embedding_model_name": config.embedding_model_name,
            "documents_dir": str(config.documents_dir),
            "chroma_path": str(config.chroma_path),
            "collection_name": config.collection_name,
            "manifest_path": str(config.manifest_path),
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "ingestion_backend": config.ingestion_backend,
            "unstructured_chunk_chars": config.unstructured_chunk_chars,
            "max_citations": config.max_citations,
        },
        sort_keys=True,
    )


def get_pipeline() -> tuple[AppConfig, AuditRAGPipeline]:
    config = AppConfig.from_env()
    signature = get_config_signature(config)

    if st.session_state.get("pipeline_signature") != signature:
        st.session_state["pipeline"] = AuditRAGPipeline(config)
        st.session_state["pipeline_signature"] = signature

    return config, st.session_state["pipeline"]


def save_uploaded_files(files: List[Any], target_dir: Path) -> List[str]:
    target_dir.mkdir(parents=True, exist_ok=True)
    saved_files: List[str] = []

    for uploaded_file in files:
        safe_name = Path(uploaded_file.name).name
        output_path = target_dir / safe_name
        output_path.write_bytes(uploaded_file.getbuffer())
        saved_files.append(safe_name)

    return saved_files


def render_ingestion_report(report: IngestionReport) -> None:
    cols = st.columns(5)
    cols[0].metric("Indexed", len(report.indexed_files))
    cols[1].metric("Removed", len(report.removed_files))
    cols[2].metric("Skipped", len(report.skipped_files))
    cols[3].metric("Failed", len(report.failed_files))
    cols[4].metric("Bootstrapped", "Yes" if report.manifest_bootstrapped else "No")

    with st.expander("Indexed files", expanded=bool(report.indexed_files)):
        for item in report.indexed_files:
            st.write(f"+ {item}")

    with st.expander("Removed files", expanded=False):
        for item in report.removed_files:
            st.write(f"- {item}")

    with st.expander("Skipped files", expanded=False):
        for item in report.skipped_files:
            st.write(f"~ {item}")

    with st.expander("Failed files", expanded=bool(report.failed_files)):
        for path, error in report.failed_files.items():
            st.write(f"{path}: {error}")


def render_structured_output(result: Dict[str, Any]) -> None:
    summary = html.escape(str(result.get("executive_summary", "")).strip())
    uncertainty = html.escape(str(result.get("uncertainty_notes", "")).strip())

    key_risks = [html.escape(str(item)) for item in result.get("key_risks", [])]
    deadlines = [html.escape(str(item)) for item in result.get("critical_deadlines", [])]
    actions = [html.escape(str(item)) for item in result.get("recommended_actions", [])]

    def _to_list(items: List[str]) -> str:
        if not items:
            return "<li>No items detected.</li>"
        return "".join(f"<li>{item}</li>" for item in items)

    st.markdown(
        f"""
        <div class="card fade-in">
            <h3>Executive Summary</h3>
            <p>{summary or 'No summary generated.'}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""
            <div class="card fade-in">
                <h3>Key Risks</h3>
                <ul>{_to_list(key_risks)}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="card fade-in">
                <h3>Critical Deadlines</h3>
                <ul>{_to_list(deadlines)}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(
            f"""
            <div class="card fade-in">
                <h3>Recommended Actions</h3>
                <ul>{_to_list(actions)}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="card fade-in">
                <h3>Uncertainty Notes</h3>
                <p>{uncertainty or 'No uncertainty notes provided.'}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_citations(citations: List[Dict[str, Any]]) -> None:
    st.subheader("Citations")
    if not citations:
        st.info("No citations were returned by the retriever.")
        return

    st.dataframe(citations, use_container_width=True, hide_index=True)


def load_eval_dataset(dataset_path_text: str) -> List[Dict[str, Any]]:
    dataset_path = Path(dataset_path_text)
    if not dataset_path.is_absolute():
        dataset_path = (BASE_DIR / dataset_path).resolve()

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Evaluation dataset must be a list of cases.")
    return data


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Administrative AI Studio", layout="wide")
    apply_custom_theme()

    st.markdown(
        """
        <div class="hero fade-in">
            <h1>Administrative AI Studio</h1>
            <p>
                Upload legal documents, sync the vector index, generate grounded audits with citations,
                and track quality metrics in one workspace.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    config, pipeline = get_pipeline()
    config.documents_dir.mkdir(parents=True, exist_ok=True)

    if (
        pipeline.recovered_from_schema_mismatch
        and not st.session_state.get("schema_mismatch_notice_shown")
    ):
        st.warning(
            "Detected an incompatible local Chroma schema. "
            f"A backup was created at: {pipeline.schema_backup_path}. "
            "The vector store was reinitialized; run a reindex to repopulate embeddings."
        )
        st.session_state["schema_mismatch_notice_shown"] = True

    with st.sidebar:
        st.header("Control Center")
        st.write(f"Documents dir: {config.documents_dir}")
        st.write(f"Collection: {config.collection_name}")
        st.write(f"Ingestion backend: {config.ingestion_backend}")
        top_k = st.slider("Retriever top-k", min_value=1, max_value=15, value=5)
        output_mode = st.radio(
            "Answer mode",
            options=["Structured audit", "Plain answer"],
            index=0,
        )

    tabs = st.tabs(["Ingestion", "Audit", "Evaluation", "System"])

    with tabs[0]:
        st.subheader("Ingestion Workspace")
        uploads = st.file_uploader(
            "Upload one or more legal documents",
            type=["pdf", "txt", "md", "docx", "odt", "rtf"],
            accept_multiple_files=True,
        )

        save_col, sync_col, reindex_col = st.columns(3)
        with save_col:
            if st.button("Save uploads", type="primary"):
                if not uploads:
                    st.warning("No files selected.")
                else:
                    saved = save_uploaded_files(uploads, config.documents_dir)
                    st.success(f"Saved {len(saved)} file(s): {', '.join(saved)}")

        with sync_col:
            if st.button("Sync index"):
                try:
                    report = pipeline.sync_index(force_reindex=False)
                    st.session_state["last_ingestion_report"] = report
                    st.success("Incremental sync completed.")
                except Exception as error:
                    st.error(f"Sync failed: {error}")

        with reindex_col:
            if st.button("Force reindex"):
                try:
                    report = pipeline.sync_index(force_reindex=True)
                    st.session_state["last_ingestion_report"] = report
                    st.success("Full reindex completed.")
                except Exception as error:
                    st.error(f"Reindex failed: {error}")

        report = st.session_state.get("last_ingestion_report")
        if report is not None:
            render_ingestion_report(report)

    with tabs[1]:
        st.subheader("Audit Generator")
        prompt = st.text_area("Prompt", value=config.default_query, height=130)
        run_audit = st.button("Run audit", type="primary")

        if run_audit:
            if not prompt.strip():
                st.warning("Please provide a prompt.")
            else:
                try:
                    if output_mode == "Structured audit":
                        result = pipeline.generate_structured_audit(prompt, similarity_top_k=top_k)
                        st.session_state["last_audit_mode"] = "structured"
                        st.session_state["last_audit_result"] = result
                    else:
                        result = pipeline.query_with_sources(prompt, similarity_top_k=top_k)
                        st.session_state["last_audit_mode"] = "plain"
                        st.session_state["last_audit_result"] = result
                except Exception as error:
                    st.error(f"Audit failed: {error}")

        mode = st.session_state.get("last_audit_mode")
        result = st.session_state.get("last_audit_result")
        if mode and result:
            if mode == "structured":
                render_structured_output(result)
                render_citations(result.get("citations", []))

                output_json = json.dumps(result, indent=2, ensure_ascii=False)
                download_name = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                st.download_button(
                    "Download audit JSON",
                    data=output_json,
                    file_name=download_name,
                    mime="application/json",
                )
            else:
                st.markdown("### Model Answer")
                st.write(result.get("answer", ""))
                render_citations(result.get("citations", []))

    with tabs[2]:
        st.subheader("Evaluation Dashboard")
        dataset_path_text = st.text_input(
            "Dataset path",
            value="evaluation/sample_eval_dataset.json",
        )
        eval_top_k = st.slider("Evaluation top-k", min_value=1, max_value=15, value=5)

        if st.button("Run evaluation", type="primary"):
            try:
                dataset = load_eval_dataset(dataset_path_text)
                report = run_evaluation(dataset=dataset, top_k=eval_top_k)
                st.session_state["last_eval_report"] = report

                report_path = BASE_DIR / "results" / "eval_report.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    json.dumps(report, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                st.success(f"Evaluation finished. Report saved to: {report_path}")
            except Exception as error:
                st.error(f"Evaluation failed: {error}")

        eval_report = st.session_state.get("last_eval_report")
        if eval_report is None:
            default_report_path = BASE_DIR / "results" / "eval_report.json"
            if default_report_path.exists():
                try:
                    eval_report = json.loads(default_report_path.read_text(encoding="utf-8"))
                except Exception:
                    eval_report = None

        if eval_report:
            overall = eval_report.get("overall", {})
            kpi_cols = st.columns(4)
            kpi_cols[0].metric("Cases", overall.get("cases", 0))
            kpi_cols[1].metric("Avg source recall", f"{overall.get('avg_source_recall', 0.0):.2f}")
            kpi_cols[2].metric("Avg keyword coverage", f"{overall.get('avg_keyword_coverage', 0.0):.2f}")
            kpi_cols[3].metric("Avg latency (s)", f"{overall.get('avg_latency_seconds', 0.0):.2f}")

            st.markdown("### Per-case results")
            st.dataframe(eval_report.get("per_case", []), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader("System Status")
        source_files = [
            path
            for path in config.documents_dir.rglob("*")
            if path.is_file()
        ] if config.documents_dir.exists() else []

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Source files", len(source_files))
        col_b.metric("Vector entries", pipeline.collection.count())
        col_c.metric("Max citations", config.max_citations)

        st.markdown("### Runtime configuration")
        st.json(
            {
                "lmstudio_base_url": config.lmstudio_base_url,
                "llm_model_name": config.llm_model_name,
                "embedding_model_name": config.embedding_model_name,
                "documents_dir": str(config.documents_dir),
                "chroma_path": str(config.chroma_path),
                "collection_name": config.collection_name,
                "ingestion_backend": config.ingestion_backend,
                "chunk_size": config.chunk_size,
                "chunk_overlap": config.chunk_overlap,
            }
        )


if __name__ == "__main__":
    main()