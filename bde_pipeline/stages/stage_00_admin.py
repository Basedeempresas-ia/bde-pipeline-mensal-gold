from __future__ import annotations

import argparse
from pathlib import Path

from bde_pipeline.core.checkpoints import write_checkpoint
from bde_pipeline.core.config import load_config
from bde_pipeline.core.manifest import STAGE_00_NAME, write_initial_manifest, write_initial_qa
from bde_pipeline.core.paths import create_monthly_structure
from bde_pipeline.core.runtime import RunContext, build_run_context, validate_competencia


def run_stage_00(config_path: str | Path, run_id: str | None = None) -> RunContext:
    config = load_config(config_path)
    validate_competencia(config)
    context = build_run_context(config, run_id=run_id)
    created_dirs = create_monthly_structure(context)
    write_initial_manifest(context)
    write_initial_qa(context, created_dirs)
    write_checkpoint(context, STAGE_00_NAME)
    return context


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BDE Pipeline Mensal Gold Stage 00.")
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    parser.add_argument("--run-id", default=None, help="Optional deterministic run id.")
    args = parser.parse_args()
    run_stage_00(args.config, run_id=args.run_id)


if __name__ == "__main__":
    main()
