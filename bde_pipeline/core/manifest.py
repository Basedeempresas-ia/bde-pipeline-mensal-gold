from __future__ import annotations

import json
from pathlib import Path

from bde_pipeline.core.paths import monthly_directory_paths
from bde_pipeline.core.runtime import RunContext

STAGE_00_NAME = "stage_00_admin_ambiente"


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def write_initial_manifest(context: RunContext) -> Path:
    manifest_path = (
        context.local_month_root / "outputs" / "manifests" / "stage_00_admin_manifest.json"
    )
    payload = {
        "run_id": context.run_id,
        "competencia": context.competencia,
        "competencia_slug": context.competencia_slug,
        "stage": STAGE_00_NAME,
        "status": "ok",
        "data_processamento": context.data_processamento,
        "local_month_root": str(context.local_month_root),
        "gdrive_month_root": str(context.gdrive_month_root),
        "dry_run": context.dry_run,
        "directories_created": [str(path) for path in monthly_directory_paths(context)],
    }
    return write_json(manifest_path, payload)


def write_initial_qa(context: RunContext, created_dirs: list[Path]) -> Path:
    required_directories = monthly_directory_paths(context)
    missing_directories = [path for path in required_directories if not path.is_dir()]
    local_root_exists = context.local_month_root.is_dir()
    required_directories_present = not missing_directories
    checkpoint_ok = (
        local_root_exists
        and required_directories_present
        and missing_directories == []
    )
    payload = {
        "run_id": context.run_id,
        "competencia": context.competencia,
        "stage": STAGE_00_NAME,
        "status": "ok" if checkpoint_ok else "error",
        "local_root_exists": local_root_exists,
        "directory_count": len(created_dirs),
        "required_directories_present": required_directories_present,
        "missing_directories": [str(path) for path in missing_directories],
        "linhas_entrada": 0,
        "linhas_saida": 0,
        "chaves_nulas": {},
        "duplicidade_de_chave": 0,
        "cardinalidade_preservada": True,
        "top_erros": [],
        "checkpoint_ok": checkpoint_ok,
        "checkpoint_allowed": checkpoint_ok,
    }
    qa_path = context.local_month_root / "outputs" / "qa" / "stage_00_admin_qa.json"
    return write_json(qa_path, payload)
