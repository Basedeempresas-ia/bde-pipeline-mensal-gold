from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from bde_pipeline.core.config import ConfigError, load_config
from bde_pipeline.core.manifest import STAGE_00_NAME
from bde_pipeline.core.paths import MONTHLY_DIRECTORIES
from bde_pipeline.core.runtime import build_run_context, validate_competencia
from bde_pipeline.stages.stage_00_admin import run_stage_00


PROHIBITED_SUFFIXES = {
    ".zip",
    ".csv",
    ".parquet",
    ".duckdb",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".xlsx",
    ".xls",
    ".bin",
}


def write_config(tmp_path: Path, **overrides: object) -> Path:
    config = {
        "competencia": "2026-01",
        "ano_referencia": 2026,
        "mes_referencia": 1,
        "competencia_slug": "2026_01",
        "local_root": str(tmp_path / "local"),
        "gdrive_root": str(tmp_path / "gdrive"),
        "dry_run": True,
        "paths": {
            "raw": "raw",
            "staging": "staging",
            "processed": "processed",
            "outputs": "outputs",
            "exports": "exports",
            "logs": "logs",
        },
    }
    config.update(overrides)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
    return config_path


def test_load_config_reads_yaml(tmp_path: Path) -> None:
    config_path = write_config(tmp_path)

    config = load_config(config_path)

    assert config["competencia"] == "2026-01"
    assert config["paths"]["outputs"] == "outputs"


def test_load_config_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(tmp_path / "missing.yaml")


def test_load_config_rejects_invalid_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("competencia: [2026-01\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid YAML config"):
        load_config(config_path)


def test_validate_competencia_accepts_valid_config(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path))

    validate_competencia(config)


def test_validate_competencia_rejects_invalid_competencia(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path, competencia="2026/01"))

    with pytest.raises(ConfigError, match="YYYY-MM"):
        validate_competencia(config)


def test_build_run_context_uses_month_roots_and_run_id(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path))

    context = build_run_context(config, run_id="test_run")

    assert context.run_id == "test_run"
    assert context.local_month_root == tmp_path / "local" / "2026_01"
    assert context.gdrive_month_root == tmp_path / "gdrive" / "2026_01"


def test_run_stage_00_creates_expected_structure_and_artifacts(tmp_path: Path) -> None:
    config_path = write_config(tmp_path)

    context = run_stage_00(config_path, run_id="test_run")

    for directory in MONTHLY_DIRECTORIES:
        assert (context.local_month_root / directory).is_dir()

    manifest_path = (
        context.local_month_root
        / "outputs"
        / "manifests"
        / "stage_00_admin_manifest.json"
    )
    qa_path = context.local_month_root / "outputs" / "qa" / "stage_00_admin_qa.json"
    checkpoint_path = (
        context.local_month_root
        / "outputs"
        / "checkpoints"
        / "stage_00_admin_ambiente.ok"
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    checkpoint = checkpoint_path.read_text(encoding="utf-8")

    assert manifest["run_id"] == "test_run"
    assert manifest["stage"] == STAGE_00_NAME
    assert manifest["status"] == "ok"
    assert manifest["directories_created"]

    assert qa["status"] == "ok"
    assert qa["local_root_exists"] is True
    assert qa["directory_count"] == len(MONTHLY_DIRECTORIES)
    assert qa["required_directories_present"] is True
    assert qa["missing_directories"] == []
    assert qa["checkpoint_allowed"] is True

    assert "run_id=test_run" in checkpoint
    assert "status=ok" in checkpoint


def test_run_stage_00_is_idempotent(tmp_path: Path) -> None:
    config_path = write_config(tmp_path)

    first_context = run_stage_00(config_path, run_id="test_run")
    second_context = run_stage_00(config_path, run_id="test_run")

    assert first_context.local_month_root == second_context.local_month_root
    assert (second_context.local_month_root / "outputs" / "qa" / "stage_00_admin_qa.json").exists()


def test_stage_00_does_not_create_prohibited_runtime_files(tmp_path: Path) -> None:
    config_path = write_config(tmp_path)
    context = run_stage_00(config_path, run_id="test_run")

    prohibited_files = [
        path
        for path in context.local_month_root.rglob("*")
        if path.is_file() and path.suffix.lower() in PROHIBITED_SUFFIXES
    ]

    assert prohibited_files == []
