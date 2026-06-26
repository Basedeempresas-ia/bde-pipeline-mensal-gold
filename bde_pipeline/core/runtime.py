from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from bde_pipeline.core.config import ConfigError


@dataclass(frozen=True)
class RunContext:
    competencia: str
    competencia_slug: str
    ano_referencia: int
    mes_referencia: int
    run_id: str
    dry_run: bool
    local_month_root: Path
    gdrive_month_root: Path
    data_processamento: str


def validate_competencia(config: dict[str, Any]) -> None:
    competencia = config.get("competencia")
    competencia_slug = config.get("competencia_slug")
    ano_referencia = config.get("ano_referencia")
    mes_referencia = config.get("mes_referencia")

    if not isinstance(competencia, str) or len(competencia) != 7:
        raise ConfigError("Config field 'competencia' must use YYYY-MM format")

    try:
        year_text, month_text = competencia.split("-")
        competencia_year = int(year_text)
        competencia_month = int(month_text)
    except ValueError as exc:
        raise ConfigError("Config field 'competencia' must use YYYY-MM format") from exc

    if f"{competencia_year:04d}-{competencia_month:02d}" != competencia:
        raise ConfigError("Config field 'competencia' must use YYYY-MM format")

    if not isinstance(competencia_slug, str):
        raise ConfigError("Config field 'competencia_slug' must use YYYY_MM format")

    expected_slug = f"{competencia_year:04d}_{competencia_month:02d}"
    if competencia_slug != expected_slug:
        raise ConfigError(
            "Config field 'competencia_slug' must match competencia as YYYY_MM"
        )

    if not isinstance(ano_referencia, int):
        raise ConfigError("Config field 'ano_referencia' must be an integer")

    if not isinstance(mes_referencia, int) or not 1 <= mes_referencia <= 12:
        raise ConfigError("Config field 'mes_referencia' must be an integer from 1 to 12")

    if ano_referencia != competencia_year or mes_referencia != competencia_month:
        raise ConfigError(
            "Config fields 'ano_referencia' and 'mes_referencia' must match competencia"
        )


def build_run_context(config: dict[str, Any], run_id: str | None = None) -> RunContext:
    validate_competencia(config)

    data_processamento = datetime.now().isoformat(timespec="seconds")
    resolved_run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    competencia_slug = str(config["competencia_slug"])

    return RunContext(
        competencia=str(config["competencia"]),
        competencia_slug=competencia_slug,
        ano_referencia=int(config["ano_referencia"]),
        mes_referencia=int(config["mes_referencia"]),
        run_id=resolved_run_id,
        dry_run=bool(config["dry_run"]),
        local_month_root=Path(config["local_root"]) / competencia_slug,
        gdrive_month_root=Path(config["gdrive_root"]) / competencia_slug,
        data_processamento=data_processamento,
    )
