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

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "interface_language": "Interface language",
        "language_es": "Spanish",
        "language_en": "English",
        "response_language": "Response language",
        "response_language_auto": "Auto (follow prompt language)",
        "response_language_es": "Spanish",
        "response_language_en": "English",
        "response_language_effective": "Answer language: {language}",
        "hero_title": "Administrative AI Studio",
        "hero_description": "Upload legal documents, sync the vector index, generate grounded audits with citations, and track quality metrics in one workspace.",
        "schema_mismatch_warning": "Detected an incompatible local Chroma schema. A backup was created at: {backup_path}. The vector store was reinitialized; run a reindex to repopulate embeddings.",
        "control_center": "Control Center",
        "documents_dir": "Documents dir",
        "collection": "Collection",
        "ingestion_backend": "Ingestion backend",
        "retriever_top_k": "Retriever top-k",
        "answer_mode": "Answer mode",
        "structured_audit": "Structured audit",
        "plain_answer": "Plain answer",
        "tab_ingestion": "Ingestion",
        "tab_audit": "Audit",
        "tab_evaluation": "Evaluation",
        "tab_system": "System",
        "ingestion_workspace": "Ingestion Workspace",
        "upload_documents": "Upload one or more legal documents",
        "save_uploads": "Save uploads",
        "no_files_selected": "No files selected.",
        "saved_files": "Saved {count} file(s): {files}",
        "sync_index": "Sync index",
        "incremental_sync_completed": "Incremental sync completed.",
        "sync_failed": "Sync failed: {error}",
        "force_reindex": "Force reindex",
        "full_reindex_completed": "Full reindex completed.",
        "reindex_failed": "Reindex failed: {error}",
        "indexed": "Indexed",
        "removed": "Removed",
        "skipped": "Skipped",
        "failed": "Failed",
        "bootstrapped": "Bootstrapped",
        "yes": "Yes",
        "no": "No",
        "indexed_files": "Indexed files",
        "removed_files": "Removed files",
        "skipped_files": "Skipped files",
        "failed_files": "Failed files",
        "audit_generator": "Audit Generator",
        "prompt": "Prompt",
        "run_audit": "Run audit",
        "provide_prompt": "Please provide a prompt.",
        "audit_failed": "Audit failed: {error}",
        "model_answer": "Model Answer",
        "download_audit_json": "Download audit JSON",
        "citations": "Citations",
        "no_citations": "No citations were returned by the retriever.",
        "executive_summary": "Executive Summary",
        "no_summary_generated": "No summary generated.",
        "key_risks": "Key Risks",
        "critical_deadlines": "Critical Deadlines",
        "recommended_actions": "Recommended Actions",
        "uncertainty_notes": "Uncertainty Notes",
        "no_uncertainty_notes": "No uncertainty notes provided.",
        "no_items_detected": "No items detected.",
        "evaluation_dashboard": "Evaluation Dashboard",
        "dataset_path": "Dataset path",
        "evaluation_top_k": "Evaluation top-k",
        "run_evaluation": "Run evaluation",
        "evaluation_finished": "Evaluation finished. Report saved to: {report_path}",
        "evaluation_failed": "Evaluation failed: {error}",
        "cases": "Cases",
        "avg_source_recall": "Avg source recall",
        "avg_keyword_coverage": "Avg keyword coverage",
        "avg_latency_seconds": "Avg latency (s)",
        "per_case_results": "Per-case results",
        "system_status": "System Status",
        "source_files": "Source files",
        "vector_entries": "Vector entries",
        "max_citations": "Max citations",
        "runtime_configuration": "Runtime configuration",
    },
    "es": {
        "interface_language": "Idioma de la interfaz",
        "language_es": "Español",
        "language_en": "Inglés",
        "response_language": "Idioma de respuesta",
        "response_language_auto": "Automático (según el prompt)",
        "response_language_es": "Español",
        "response_language_en": "Inglés",
        "response_language_effective": "Idioma de la respuesta: {language}",
        "hero_title": "Administrative AI Studio",
        "hero_description": "Sube documentos legales, sincroniza el índice vectorial, genera auditorías con citas y revisa métricas de calidad en un solo lugar.",
        "schema_mismatch_warning": "Se detectó un esquema local de Chroma incompatible. Se creó un respaldo en: {backup_path}. El vector store fue reinicializado; ejecuta un reindex para repoblar embeddings.",
        "control_center": "Centro de control",
        "documents_dir": "Directorio de documentos",
        "collection": "Colección",
        "ingestion_backend": "Backend de ingesta",
        "retriever_top_k": "Top-k del recuperador",
        "answer_mode": "Modo de respuesta",
        "structured_audit": "Auditoría estructurada",
        "plain_answer": "Respuesta simple",
        "tab_ingestion": "Ingesta",
        "tab_audit": "Auditoría",
        "tab_evaluation": "Evaluación",
        "tab_system": "Sistema",
        "ingestion_workspace": "Espacio de Ingesta",
        "upload_documents": "Sube uno o varios documentos legales",
        "save_uploads": "Guardar subidas",
        "no_files_selected": "No has seleccionado archivos.",
        "saved_files": "Se guardaron {count} archivo(s): {files}",
        "sync_index": "Sincronizar índice",
        "incremental_sync_completed": "Sincronización incremental completada.",
        "sync_failed": "Falló la sincronización: {error}",
        "force_reindex": "Forzar reindex",
        "full_reindex_completed": "Reindexado completo finalizado.",
        "reindex_failed": "Falló el reindexado: {error}",
        "indexed": "Indexados",
        "removed": "Eliminados",
        "skipped": "Omitidos",
        "failed": "Fallidos",
        "bootstrapped": "Inicializado",
        "yes": "Sí",
        "no": "No",
        "indexed_files": "Archivos indexados",
        "removed_files": "Archivos eliminados",
        "skipped_files": "Archivos omitidos",
        "failed_files": "Archivos con error",
        "audit_generator": "Generador de auditorías",
        "prompt": "Prompt",
        "run_audit": "Ejecutar auditoría",
        "provide_prompt": "Escribe un prompt.",
        "audit_failed": "Falló la auditoría: {error}",
        "model_answer": "Respuesta del modelo",
        "download_audit_json": "Descargar auditoría JSON",
        "citations": "Citas",
        "no_citations": "No se devolvieron citas del recuperador.",
        "executive_summary": "Resumen ejecutivo",
        "no_summary_generated": "No se generó resumen.",
        "key_risks": "Riesgos clave",
        "critical_deadlines": "Fechas críticas",
        "recommended_actions": "Acciones recomendadas",
        "uncertainty_notes": "Notas de incertidumbre",
        "no_uncertainty_notes": "Sin notas de incertidumbre.",
        "no_items_detected": "No se detectaron elementos.",
        "evaluation_dashboard": "Panel de evaluación",
        "dataset_path": "Ruta del dataset",
        "evaluation_top_k": "Top-k de evaluación",
        "run_evaluation": "Ejecutar evaluación",
        "evaluation_finished": "Evaluación completada. Reporte guardado en: {report_path}",
        "evaluation_failed": "Falló la evaluación: {error}",
        "cases": "Casos",
        "avg_source_recall": "Recall promedio de fuentes",
        "avg_keyword_coverage": "Cobertura promedio de palabras clave",
        "avg_latency_seconds": "Latencia promedio (s)",
        "per_case_results": "Resultados por caso",
        "system_status": "Estado del sistema",
        "source_files": "Archivos fuente",
        "vector_entries": "Entradas vectoriales",
        "max_citations": "Máximo de citas",
        "runtime_configuration": "Configuración en tiempo de ejecución",
    },
}


def tr(ui_language: str, key: str, **kwargs: Any) -> str:
    language_pack = TRANSLATIONS.get(ui_language, TRANSLATIONS["en"])
    template = language_pack.get(key, TRANSLATIONS["en"].get(key, key))
    return template.format(**kwargs)


def apply_custom_theme() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@400;500;600&display=swap');

            :root {
                --bg: #12151b;
                --ink: #ffffff;
                --accent: #9ecbff;
                --card: #2f3642;
                --muted: #dbe2ef;
                --border: #6f7a8c;
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
                background: linear-gradient(135deg, #2b3340 0%, #3a4454 100%);
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
            [data-testid="stTextInput"],
            [data-testid="stTextArea"],
            [data-testid="stNumberInput"] {
                background-color: transparent !important;
            }

            [data-testid="stTextInput"] div[data-baseweb="input"],
            [data-testid="stTextArea"] div[data-baseweb="textarea"],
            [data-testid="stNumberInput"] div[data-baseweb="input"],
            [data-testid="stTextInput"] div[data-baseweb="base-input"],
            [data-testid="stTextArea"] div[data-baseweb="base-input"] {
                background-color: #3a4352 !important;
                border: 1px solid var(--border) !important;
                border-radius: 6px !important;
            }

            [data-testid="stTextInput"] input,
            [data-testid="stTextArea"] textarea,
            [data-testid="stNumberInput"] input {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                background-color: transparent !important;
                font-family: 'Fira Code', monospace !important;
                caret-color: #ffffff !important;
            }

            [data-testid="stTextInput"] input:focus,
            [data-testid="stTextArea"] textarea:focus,
            [data-testid="stNumberInput"] input:focus {
                outline: none !important;
                box-shadow: none !important;
            }

            [data-testid="stTextInput"] input::placeholder,
            [data-testid="stTextArea"] textarea::placeholder {
                color: #dde3ec !important;
                -webkit-text-fill-color: #dde3ec !important;
            }

            /* Selectors, Popovers y Tabs */
            [data-baseweb="select"] > div {
                background-color: #3a4352 !important;
                border-color: var(--border) !important;
            }

            [data-baseweb="select"] input {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
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
            [data-testid="stFileUploader"] section,
            [data-testid="stFileUploadDropzone"] {
                background-color: #3a4352 !important;
                border: 1px dashed var(--muted) !important;
                border-radius: 8px !important;
            }
            
            [data-testid="stFileUploader"] section *,
            [data-testid="stFileUploadDropzone"] * {
                color: #ffffff !important;
            }

            /* Dataframes (Tablas de resultados) y Métricas */
            [data-testid="stDataFrame"] div[data-baseweb="table"] {
                background-color: var(--card) !important;
            }

            [data-testid="stDataFrame"] {
                --gdg-bg-cell: #2f3642 !important;
                --gdg-bg-header: #414b5d !important;
                --gdg-bg-header-hovered: #4c5870 !important;
                --gdg-bg-even: #313a49 !important;
                --gdg-bg-odd: #2f3642 !important;
                --gdg-text-dark: #ffffff !important;
                --gdg-text-medium: #ffffff !important;
                --gdg-header-font-style: 600 13px Inter, sans-serif !important;
                border: 1px solid var(--border) !important;
                border-radius: 8px !important;
            }

            [data-testid="stDataFrame"] canvas {
                background-color: #2f3642 !important;
            }

            [data-testid="stTable"] table,
            [data-testid="stTable"] th,
            [data-testid="stTable"] td {
                background-color: #2f3642 !important;
                color: #ffffff !important;
                border-color: var(--border) !important;
            }
            
            [data-testid="stDataFrame"] * {
                color: var(--ink) !important;
                border-color: var(--border) !important;
            }
            
            [data-testid="stMetricValue"] {
                color: #ffffff !important;
            }

            [data-testid="stJson"],
            [data-testid="stJson"] * {
                background-color: #2f3642 !important;
                color: #ffffff !important;
            }

            /* Código fuente y bloques de texto preformateados */
            code, pre {
                background-color: #2f3642 !important;
                color: #ffffff !important;
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


def render_ingestion_report(report: IngestionReport, ui_language: str) -> None:
    cols = st.columns(5)
    cols[0].metric(tr(ui_language, "indexed"), len(report.indexed_files))
    cols[1].metric(tr(ui_language, "removed"), len(report.removed_files))
    cols[2].metric(tr(ui_language, "skipped"), len(report.skipped_files))
    cols[3].metric(tr(ui_language, "failed"), len(report.failed_files))
    cols[4].metric(
        tr(ui_language, "bootstrapped"),
        tr(ui_language, "yes") if report.manifest_bootstrapped else tr(ui_language, "no"),
    )

    with st.expander(tr(ui_language, "indexed_files"), expanded=bool(report.indexed_files)):
        for item in report.indexed_files:
            st.write(f"+ {item}")

    with st.expander(tr(ui_language, "removed_files"), expanded=False):
        for item in report.removed_files:
            st.write(f"- {item}")

    with st.expander(tr(ui_language, "skipped_files"), expanded=False):
        for item in report.skipped_files:
            st.write(f"~ {item}")

    with st.expander(tr(ui_language, "failed_files"), expanded=bool(report.failed_files)):
        for path, error in report.failed_files.items():
            st.write(f"{path}: {error}")


def render_structured_output(result: Dict[str, Any], ui_language: str) -> None:
    summary = html.escape(str(result.get("executive_summary", "")).strip())
    uncertainty = html.escape(str(result.get("uncertainty_notes", "")).strip())

    key_risks = [html.escape(str(item)) for item in result.get("key_risks", [])]
    deadlines = [html.escape(str(item)) for item in result.get("critical_deadlines", [])]
    actions = [html.escape(str(item)) for item in result.get("recommended_actions", [])]

    def _to_list(items: List[str]) -> str:
        if not items:
            return f"<li>{html.escape(tr(ui_language, 'no_items_detected'))}</li>"
        return "".join(f"<li>{item}</li>" for item in items)

    st.markdown(
        f"""
        <div class="card fade-in">
            <h3>{html.escape(tr(ui_language, 'executive_summary'))}</h3>
            <p>{summary or html.escape(tr(ui_language, 'no_summary_generated'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""
            <div class="card fade-in">
                <h3>{html.escape(tr(ui_language, 'key_risks'))}</h3>
                <ul>{_to_list(key_risks)}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="card fade-in">
                <h3>{html.escape(tr(ui_language, 'critical_deadlines'))}</h3>
                <ul>{_to_list(deadlines)}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(
            f"""
            <div class="card fade-in">
                <h3>{html.escape(tr(ui_language, 'recommended_actions'))}</h3>
                <ul>{_to_list(actions)}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="card fade-in">
                <h3>{html.escape(tr(ui_language, 'uncertainty_notes'))}</h3>
                <p>{uncertainty or html.escape(tr(ui_language, 'no_uncertainty_notes'))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_citations(citations: List[Dict[str, Any]], ui_language: str) -> None:
    st.subheader(tr(ui_language, "citations"))
    if not citations:
        st.info(tr(ui_language, "no_citations"))
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

    ui_language = st.session_state.get("ui_language", "es")
    if ui_language not in {"es", "en"}:
        ui_language = "es"

    selected_ui_language = st.sidebar.selectbox(
        tr(ui_language, "interface_language"),
        options=["es", "en"],
        index=0 if ui_language == "es" else 1,
        format_func=lambda code: tr(ui_language, f"language_{code}"),
    )

    if selected_ui_language != ui_language:
        st.session_state["ui_language"] = selected_ui_language
        st.rerun()

    ui_language = selected_ui_language

    st.markdown(
        f"""
        <div class="hero fade-in">
            <h1>{html.escape(tr(ui_language, 'hero_title'))}</h1>
            <p>
                {html.escape(tr(ui_language, 'hero_description'))}
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
            tr(
                ui_language,
                "schema_mismatch_warning",
                backup_path=pipeline.schema_backup_path,
            )
        )
        st.session_state["schema_mismatch_notice_shown"] = True

    response_options = ["auto", "es", "en"]
    saved_response_mode = st.session_state.get("response_language_mode", "auto")
    if saved_response_mode not in response_options:
        saved_response_mode = "auto"

    with st.sidebar:
        st.header(tr(ui_language, "control_center"))
        response_language_mode = st.selectbox(
            tr(ui_language, "response_language"),
            options=response_options,
            index=response_options.index(saved_response_mode),
            format_func=lambda option: tr(ui_language, f"response_language_{option}"),
        )
        st.session_state["response_language_mode"] = response_language_mode

        st.write(f"{tr(ui_language, 'documents_dir')}: {config.documents_dir}")
        st.write(f"{tr(ui_language, 'collection')}: {config.collection_name}")
        st.write(f"{tr(ui_language, 'ingestion_backend')}: {config.ingestion_backend}")
        top_k = st.slider(tr(ui_language, "retriever_top_k"), min_value=1, max_value=15, value=5)
        output_mode = st.radio(
            tr(ui_language, "answer_mode"),
            options=["structured", "plain"],
            format_func=lambda option: tr(
                ui_language,
                "structured_audit" if option == "structured" else "plain_answer",
            ),
            index=0,
        )

    tabs = st.tabs(
        [
            tr(ui_language, "tab_ingestion"),
            tr(ui_language, "tab_audit"),
            tr(ui_language, "tab_evaluation"),
            tr(ui_language, "tab_system"),
        ]
    )

    with tabs[0]:
        st.subheader(tr(ui_language, "ingestion_workspace"))
        uploads = st.file_uploader(
            tr(ui_language, "upload_documents"),
            type=["pdf", "txt", "md", "docx", "odt", "rtf"],
            accept_multiple_files=True,
        )

        save_col, sync_col, reindex_col = st.columns(3)
        with save_col:
            if st.button(tr(ui_language, "save_uploads"), type="primary"):
                if not uploads:
                    st.warning(tr(ui_language, "no_files_selected"))
                else:
                    saved = save_uploaded_files(uploads, config.documents_dir)
                    st.success(
                        tr(
                            ui_language,
                            "saved_files",
                            count=len(saved),
                            files=", ".join(saved),
                        )
                    )

        with sync_col:
            if st.button(tr(ui_language, "sync_index")):
                try:
                    report = pipeline.sync_index(force_reindex=False)
                    st.session_state["last_ingestion_report"] = report
                    st.success(tr(ui_language, "incremental_sync_completed"))
                except Exception as error:
                    st.error(tr(ui_language, "sync_failed", error=error))

        with reindex_col:
            if st.button(tr(ui_language, "force_reindex")):
                try:
                    report = pipeline.sync_index(force_reindex=True)
                    st.session_state["last_ingestion_report"] = report
                    st.success(tr(ui_language, "full_reindex_completed"))
                except Exception as error:
                    st.error(tr(ui_language, "reindex_failed", error=error))

        report = st.session_state.get("last_ingestion_report")
        if report is not None:
            render_ingestion_report(report, ui_language)

    with tabs[1]:
        st.subheader(tr(ui_language, "audit_generator"))
        prompt = st.text_area(tr(ui_language, "prompt"), value=config.default_query, height=130)
        run_audit = st.button(tr(ui_language, "run_audit"), type="primary")

        if run_audit:
            if not prompt.strip():
                st.warning(tr(ui_language, "provide_prompt"))
            else:
                try:
                    if output_mode == "structured":
                        result = pipeline.generate_structured_audit(
                            prompt,
                            similarity_top_k=top_k,
                            response_language=response_language_mode,
                        )
                        st.session_state["last_audit_mode"] = "structured"
                        st.session_state["last_audit_result"] = result
                    else:
                        result = pipeline.query_with_sources(
                            prompt,
                            similarity_top_k=top_k,
                            response_language=response_language_mode,
                        )
                        st.session_state["last_audit_mode"] = "plain"
                        st.session_state["last_audit_result"] = result
                except Exception as error:
                    st.error(tr(ui_language, "audit_failed", error=error))

        mode = st.session_state.get("last_audit_mode")
        result = st.session_state.get("last_audit_result")
        if mode and result:
            response_language = result.get("response_language") if isinstance(result, dict) else None
            if response_language in {"es", "en"}:
                st.caption(
                    tr(
                        ui_language,
                        "response_language_effective",
                        language=tr(ui_language, f"language_{response_language}"),
                    )
                )

            if mode == "structured":
                render_structured_output(result, ui_language)
                render_citations(result.get("citations", []), ui_language)

                output_json = json.dumps(result, indent=2, ensure_ascii=False)
                download_name = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                st.download_button(
                    tr(ui_language, "download_audit_json"),
                    data=output_json,
                    file_name=download_name,
                    mime="application/json",
                )
            else:
                st.markdown(f"### {tr(ui_language, 'model_answer')}")
                st.write(result.get("answer", ""))
                render_citations(result.get("citations", []), ui_language)

    with tabs[2]:
        st.subheader(tr(ui_language, "evaluation_dashboard"))
        dataset_path_text = st.text_input(
            tr(ui_language, "dataset_path"),
            value="evaluation/sample_eval_dataset.json",
        )
        eval_top_k = st.slider(tr(ui_language, "evaluation_top_k"), min_value=1, max_value=15, value=5)

        if st.button(tr(ui_language, "run_evaluation"), type="primary"):
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
                st.success(
                    tr(ui_language, "evaluation_finished", report_path=report_path)
                )
            except Exception as error:
                st.error(tr(ui_language, "evaluation_failed", error=error))

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
            kpi_cols[0].metric(tr(ui_language, "cases"), overall.get("cases", 0))
            kpi_cols[1].metric(
                tr(ui_language, "avg_source_recall"),
                f"{overall.get('avg_source_recall', 0.0):.2f}",
            )
            kpi_cols[2].metric(
                tr(ui_language, "avg_keyword_coverage"),
                f"{overall.get('avg_keyword_coverage', 0.0):.2f}",
            )
            kpi_cols[3].metric(
                tr(ui_language, "avg_latency_seconds"),
                f"{overall.get('avg_latency_seconds', 0.0):.2f}",
            )

            st.markdown(f"### {tr(ui_language, 'per_case_results')}")
            st.dataframe(eval_report.get("per_case", []), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader(tr(ui_language, "system_status"))
        source_files = [
            path
            for path in config.documents_dir.rglob("*")
            if path.is_file()
        ] if config.documents_dir.exists() else []

        col_a, col_b, col_c = st.columns(3)
        col_a.metric(tr(ui_language, "source_files"), len(source_files))
        col_b.metric(tr(ui_language, "vector_entries"), pipeline.collection.count())
        col_c.metric(tr(ui_language, "max_citations"), config.max_citations)

        st.markdown(f"### {tr(ui_language, 'runtime_configuration')}")
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