from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REQUIRED_CONFIG_FIELDS = {
    "competencia",
    "ano_referencia",
    "mes_referencia",
    "competencia_slug",
    "local_root",
    "gdrive_root",
    "dry_run",
    "paths",
}


class ConfigError(ValueError):
    """Raised when the pipeline configuration is missing or invalid."""


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate a YAML configuration file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML config at {config_path}: {exc}") from exc

    if not isinstance(config, dict):
        raise ConfigError(f"Config file must contain a YAML mapping: {config_path}")

    missing_fields = sorted(REQUIRED_CONFIG_FIELDS - set(config))
    if missing_fields:
        raise ConfigError(
            "Config file is missing required fields: " + ", ".join(missing_fields)
        )

    if not isinstance(config["paths"], dict):
        raise ConfigError("Config field 'paths' must be a mapping")

    return config
