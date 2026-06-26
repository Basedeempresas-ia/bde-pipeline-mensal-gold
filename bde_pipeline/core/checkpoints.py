from __future__ import annotations

import json
from pathlib import Path

from bde_pipeline.core.manifest import STAGE_00_NAME
from bde_pipeline.core.runtime import RunContext


def write_checkpoint(context: RunContext, stage: str) -> Path:
    qa_path = context.local_month_root / "outputs" / "qa" / "stage_00_admin_qa.json"
    if not qa_path.exists():
        raise RuntimeError("Stage 00 checkpoint requires QA file to exist")

    qa_payload = json.loads(qa_path.read_text(encoding="utf-8"))
    if not qa_payload.get("checkpoint_allowed"):
        raise RuntimeError("Stage 00 checkpoint blocked by QA status")

    checkpoint_path = (
        context.local_month_root / "outputs" / "checkpoints" / f"{stage}.ok"
    )
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        "\n".join(
            [
                f"run_id={context.run_id}",
                f"competencia={context.competencia}",
                f"stage={stage}",
                "status=ok",
                f"data_processamento={context.data_processamento}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return checkpoint_path


__all__ = ["STAGE_00_NAME", "write_checkpoint"]
