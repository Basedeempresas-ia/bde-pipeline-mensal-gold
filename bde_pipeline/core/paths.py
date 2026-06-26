from __future__ import annotations

from pathlib import Path

from bde_pipeline.core.runtime import RunContext


MONTHLY_DIRECTORIES = (
    "raw",
    "raw/rfb_cnpj",
    "raw/simples_mei",
    "raw/regimes",
    "raw/pgfn",
    "staging",
    "processed",
    "processed/current",
    "processed/snapshots",
    "outputs",
    "outputs/manifests",
    "outputs/qa",
    "outputs/checkpoints",
    "exports",
    "exports/current",
    "logs",
)


def monthly_directory_paths(context: RunContext) -> list[Path]:
    return [context.local_month_root / directory for directory in MONTHLY_DIRECTORIES]


def create_monthly_structure(context: RunContext) -> list[Path]:
    directories = monthly_directory_paths(context)
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    return directories
