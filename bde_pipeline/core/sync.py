from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from bde_pipeline.core.manifest import write_json
from bde_pipeline.core.runtime import RunContext

IGNORED_SYNC_DIRS = {"__pycache__", ".pytest_cache", ".git"}


@dataclass(frozen=True)
class SyncResult:
    stage: str
    direction: str
    source_root: Path
    destination_root: Path
    files_copied: list[str]
    files_skipped: list[str]
    dry_run: bool
    status: str
    manifest_path: Path | None
    checkpoint_path: Path | None


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_SYNC_DIRS for part in path.parts)


def collect_files_to_sync(paths: list[Path]) -> list[Path]:
    collected: set[Path] = set()

    for path in paths:
        if _is_ignored(path):
            continue
        if path.is_file():
            collected.add(path)
            continue
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and not _is_ignored(child):
                    collected.add(child)

    return sorted(collected)


def copy_paths(
    source_paths: list[Path],
    source_root: Path,
    destination_root: Path,
    dry_run: bool = True,
    overwrite: bool = False,
) -> tuple[list[str], list[str]]:
    files_copied: list[str] = []
    files_skipped: list[str] = []
    source_root = source_root.resolve()

    for source_path in collect_files_to_sync(source_paths):
        source_path = source_path.resolve()
        relative_path = source_path.relative_to(source_root)
        relative_text = relative_path.as_posix()
        destination_path = destination_root / relative_path

        if destination_path.exists() and not overwrite:
            files_skipped.append(relative_text)
            continue

        files_copied.append(relative_text)
        if dry_run:
            continue

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)

    return files_copied, files_skipped


def write_sync_manifest(
    context: RunContext,
    stage: str,
    direction: str,
    result_payload: dict,
) -> Path:
    manifest_path = (
        context.local_month_root / "outputs" / "manifests" / f"{stage}_sync_manifest.json"
    )
    payload = {
        "run_id": context.run_id,
        "competencia": context.competencia,
        "competencia_slug": context.competencia_slug,
        "stage": stage,
        "direction": direction,
        "source_root": str(result_payload["source_root"]),
        "destination_root": str(result_payload["destination_root"]),
        "files_copied": result_payload["files_copied"],
        "files_skipped": result_payload["files_skipped"],
        "dry_run": result_payload["dry_run"],
        "status": result_payload["status"],
        "data_processamento": context.data_processamento,
    }
    return write_json(manifest_path, payload)


def write_sync_checkpoint(
    context: RunContext,
    stage: str,
    direction: str,
    status: str,
) -> Path:
    if status != "ok":
        raise RuntimeError("Sync checkpoint can only be written for status ok")

    checkpoint_path = context.local_month_root / "outputs" / "checkpoints" / f"{stage}_sync.ok"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        "\n".join(
            [
                f"run_id={context.run_id}",
                f"competencia={context.competencia}",
                f"stage={stage}",
                f"direction={direction}",
                f"status={status}",
                f"data_processamento={context.data_processamento}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return checkpoint_path


def _build_result_payload(
    source_root: Path,
    destination_root: Path,
    files_copied: list[str],
    files_skipped: list[str],
    dry_run: bool,
    status: str,
) -> dict:
    return {
        "source_root": source_root,
        "destination_root": destination_root,
        "files_copied": files_copied,
        "files_skipped": files_skipped,
        "dry_run": dry_run,
        "status": status,
    }


def sync_stage_to_gdrive(
    context: RunContext,
    stage: str,
    paths_to_sync: list[Path],
    dry_run: bool | None = None,
    overwrite: bool = False,
) -> SyncResult:
    resolved_dry_run = context.dry_run if dry_run is None else dry_run
    source_root = context.local_month_root
    destination_root = context.gdrive_month_root
    files_copied, files_skipped = copy_paths(
        paths_to_sync,
        source_root=source_root,
        destination_root=destination_root,
        dry_run=resolved_dry_run,
        overwrite=overwrite,
    )
    status = "ok"
    payload = _build_result_payload(
        source_root, destination_root, files_copied, files_skipped, resolved_dry_run, status
    )
    manifest_path = write_sync_manifest(context, stage, "local_to_gdrive", payload)
    checkpoint_path = None
    if status == "ok" and not resolved_dry_run:
        checkpoint_path = write_sync_checkpoint(context, stage, "local_to_gdrive", status)

    return SyncResult(
        stage=stage,
        direction="local_to_gdrive",
        source_root=source_root,
        destination_root=destination_root,
        files_copied=files_copied,
        files_skipped=files_skipped,
        dry_run=resolved_dry_run,
        status=status,
        manifest_path=manifest_path,
        checkpoint_path=checkpoint_path,
    )


def restore_month_from_gdrive(
    context: RunContext,
    paths_to_restore: list[Path] | None = None,
    dry_run: bool | None = None,
    overwrite: bool = False,
) -> SyncResult:
    resolved_dry_run = context.dry_run if dry_run is None else dry_run
    source_root = context.gdrive_month_root
    destination_root = context.local_month_root
    source_paths = paths_to_restore or [source_root]
    files_copied, files_skipped = copy_paths(
        source_paths,
        source_root=source_root,
        destination_root=destination_root,
        dry_run=resolved_dry_run,
        overwrite=overwrite,
    )
    status = "ok"
    stage = "restore_month"
    payload = _build_result_payload(
        source_root, destination_root, files_copied, files_skipped, resolved_dry_run, status
    )
    manifest_path = write_sync_manifest(context, stage, "gdrive_to_local", payload)
    checkpoint_path = None
    if status == "ok" and not resolved_dry_run:
        checkpoint_path = write_sync_checkpoint(context, stage, "gdrive_to_local", status)

    return SyncResult(
        stage=stage,
        direction="gdrive_to_local",
        source_root=source_root,
        destination_root=destination_root,
        files_copied=files_copied,
        files_skipped=files_skipped,
        dry_run=resolved_dry_run,
        status=status,
        manifest_path=manifest_path,
        checkpoint_path=checkpoint_path,
    )


__all__ = [
    "SyncResult",
    "collect_files_to_sync",
    "copy_paths",
    "write_sync_manifest",
    "write_sync_checkpoint",
    "sync_stage_to_gdrive",
    "restore_month_from_gdrive",
]
