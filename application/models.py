from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class IngestionReport:
    indexed_files: List[str] = field(default_factory=list)
    removed_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    failed_files: Dict[str, str] = field(default_factory=dict)
    manifest_bootstrapped: bool = False


@dataclass(frozen=True)
class AuditRequest:
    prompt: str
    similarity_top_k: int = 5
    response_language: str = "auto"
    structured: bool = True
