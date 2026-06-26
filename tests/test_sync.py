from __future__ import annotations

import json
from pathlib import Path

from bde_pipeline.core.runtime import RunContext
from bde_pipeline.core.sync import (
    collect_files_to_sync,
    copy_paths,
    restore_month_from_gdrive,
    sync_stage_to_gdrive,
)

PROHIBITED_SUFFIXES = (
    ".zip",
    ".csv",
    ".csv.gz",
    ".parquet",
    ".duckdb",
    ".db",
    ".sqlite",
    ".xlsx",
)


def make_context(tmp_path: Path, dry_run: bool = True) -> RunContext:
    return RunContext(
        competencia="2026-06",
        competencia_slug="2026_06",
        ano_referencia=2026,
        mes_referencia=6,
        run_id="test_run",
        dry_run=dry_run,
        local_month_root=tmp_path / "local" / "2026_06",
        gdrive_month_root=tmp_path / "drive" / "2026_06",
        data_processamento="2026-06-26T00:00:00",
    )


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_collect_files_to_sync_collects_recursively(tmp_path: Path) -> None:
    root = tmp_path / "root"
    first = write_text(root / "a.txt", "a")
    second = write_text(root / "nested" / "b.txt", "b")
    write_text(root / "__pycache__" / "ignored.pyc", "x")
    write_text(root / ".pytest_cache" / "ignored", "x")
    write_text(root / ".git" / "ignored", "x")

    assert collect_files_to_sync([root]) == [first, second]


def test_dry_run_does_not_copy_files_to_destination(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination_root = tmp_path / "destination"
    source_file = write_text(source_root / "outputs" / "a.txt", "a")

    copied, skipped = copy_paths([source_file], source_root, destination_root, dry_run=True)

    assert copied == ["outputs/a.txt"]
    assert skipped == []
    assert not (destination_root / "outputs" / "a.txt").exists()


def test_sync_stage_to_gdrive_copies_file_when_not_dry_run(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=False)
    source_file = write_text(context.local_month_root / "outputs" / "a.txt", "a")

    result = sync_stage_to_gdrive(context, "stage_00_admin_ambiente", [source_file])

    assert result.files_copied == ["outputs/a.txt"]
    assert (context.gdrive_month_root / "outputs" / "a.txt").read_text(encoding="utf-8") == "a"


def test_sync_preserves_relative_path(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=False)
    source_file = write_text(context.local_month_root / "outputs" / "qa" / "qa.json", "{}")

    sync_stage_to_gdrive(context, "stage_qa", [source_file])

    assert (context.gdrive_month_root / "outputs" / "qa" / "qa.json").exists()


def test_sync_does_not_overwrite_existing_file_without_overwrite(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=False)
    source_file = write_text(context.local_month_root / "outputs" / "a.txt", "new")
    destination_file = write_text(context.gdrive_month_root / "outputs" / "a.txt", "old")

    result = sync_stage_to_gdrive(context, "stage_skip", [source_file], overwrite=False)

    assert result.files_copied == []
    assert result.files_skipped == ["outputs/a.txt"]
    assert destination_file.read_text(encoding="utf-8") == "old"


def test_sync_overwrites_existing_file_with_overwrite(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=False)
    source_file = write_text(context.local_month_root / "outputs" / "a.txt", "new")
    destination_file = write_text(context.gdrive_month_root / "outputs" / "a.txt", "old")

    result = sync_stage_to_gdrive(context, "stage_overwrite", [source_file], overwrite=True)

    assert result.files_copied == ["outputs/a.txt"]
    assert result.files_skipped == []
    assert destination_file.read_text(encoding="utf-8") == "new"


def test_sync_manifest_is_written_with_minimum_fields(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=True)
    source_file = write_text(context.local_month_root / "outputs" / "a.txt", "a")

    result = sync_stage_to_gdrive(context, "stage_manifest", [source_file])

    assert result.manifest_path is not None
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    for field in (
        "run_id",
        "competencia",
        "competencia_slug",
        "stage",
        "direction",
        "source_root",
        "destination_root",
        "files_copied",
        "files_skipped",
        "missing_paths",
        "dry_run",
        "status",
        "data_processamento",
    ):
        assert field in manifest
    assert manifest["direction"] == "local_to_gdrive"
    assert manifest["dry_run"] is True
    assert manifest["missing_paths"] == []


def test_sync_checkpoint_only_when_not_dry_run_and_status_ok(tmp_path: Path) -> None:
    dry_context = make_context(tmp_path / "dry", dry_run=True)
    dry_file = write_text(dry_context.local_month_root / "outputs" / "a.txt", "a")

    dry_result = sync_stage_to_gdrive(dry_context, "stage_checkpoint", [dry_file])

    assert dry_result.checkpoint_path is None

    context = make_context(tmp_path / "real", dry_run=False)
    source_file = write_text(context.local_month_root / "outputs" / "a.txt", "a")

    result = sync_stage_to_gdrive(context, "stage_checkpoint", [source_file])

    assert result.checkpoint_path is not None
    assert result.checkpoint_path.exists()
    checkpoint = result.checkpoint_path.read_text(encoding="utf-8")
    assert "status=ok" in checkpoint
    assert "direction=local_to_gdrive" in checkpoint


def test_sync_missing_path_returns_error_and_manifest_missing_paths(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=False)
    source_file = write_text(context.local_month_root / "outputs" / "a.txt", "a")
    missing_file = context.local_month_root / "outputs" / "missing.txt"

    result = sync_stage_to_gdrive(
        context,
        "stage_missing",
        [source_file, missing_file],
    )

    assert result.status == "error"
    assert result.files_copied == []
    assert result.missing_paths == [str(missing_file)]
    assert result.checkpoint_path is None
    assert not (context.gdrive_month_root / "outputs" / "a.txt").exists()

    assert result.manifest_path is not None
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "error"
    assert manifest["missing_paths"] == [str(missing_file)]
    assert not (
        context.local_month_root / "outputs" / "checkpoints" / "stage_missing_sync.ok"
    ).exists()


def test_sync_persists_audit_artifacts_to_gdrive_when_not_dry_run(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=False)
    source_file = write_text(context.local_month_root / "outputs" / "a.txt", "a")

    result = sync_stage_to_gdrive(context, "stage_audit", [source_file])

    assert result.status == "ok"
    assert result.manifest_path is not None
    assert result.checkpoint_path is not None
    assert (context.gdrive_month_root / "outputs" / "manifests" / "stage_audit_sync_manifest.json").exists()
    assert (context.gdrive_month_root / "outputs" / "checkpoints" / "stage_audit_sync.ok").exists()


def test_sync_dry_run_does_not_persist_audit_artifacts_to_gdrive(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=True)
    source_file = write_text(context.local_month_root / "outputs" / "a.txt", "a")

    result = sync_stage_to_gdrive(context, "stage_audit_dry", [source_file])

    assert result.status == "ok"
    assert result.manifest_path is not None
    assert result.checkpoint_path is None
    assert not (
        context.gdrive_month_root
        / "outputs"
        / "manifests"
        / "stage_audit_dry_sync_manifest.json"
    ).exists()
    assert not (
        context.gdrive_month_root / "outputs" / "checkpoints" / "stage_audit_dry_sync.ok"
    ).exists()


def test_restore_month_from_gdrive_copies_to_local(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=False)
    drive_file = write_text(context.gdrive_month_root / "outputs" / "a.txt", "a")

    result = restore_month_from_gdrive(context, [drive_file])

    assert result.files_copied == ["outputs/a.txt"]
    assert (context.local_month_root / "outputs" / "a.txt").read_text(encoding="utf-8") == "a"


def test_restore_does_not_overwrite_without_overwrite(tmp_path: Path) -> None:
    context = make_context(tmp_path, dry_run=False)
    drive_file = write_text(context.gdrive_month_root / "outputs" / "a.txt", "drive")
    local_file = write_text(context.local_month_root / "outputs" / "a.txt", "local")

    result = restore_month_from_gdrive(context, [drive_file], overwrite=False)

    assert result.files_copied == []
    assert result.files_skipped == ["outputs/a.txt"]
    assert local_file.read_text(encoding="utf-8") == "local"


def test_no_prohibited_files_are_versioned() -> None:
    prohibited = [
        path
        for path in Path.cwd().rglob("*")
        if ".git" not in path.parts and path.is_file() and path.name.endswith(PROHIBITED_SUFFIXES)
    ]

    assert prohibited == []
