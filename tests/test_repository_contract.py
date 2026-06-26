from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    ".gitignore",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    "docs/GOVERNANCA_REPOSITORIO.md",
    "docs/ARQUITETURA_PIPELINE_MENSAL_GOLD.md",
    "docs/CONTRATOS_ARTEFATOS.md",
    "docs/POLITICA_COLAB_GDRIVE.md",
    "configs/config_template.yaml",
    "bde_pipeline/__init__.py",
    "bde_pipeline/core/__init__.py",
    "bde_pipeline/stages/__init__.py",
    "tests/test_repository_contract.py",
    "notebooks/.gitkeep",
]

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


def test_required_governance_paths_exist() -> None:
    missing_paths = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]

    assert missing_paths == []


def test_no_prohibited_artifacts_are_versioned() -> None:
    prohibited_files = [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if ".git" not in path.parts and path.is_file() and path.suffix.lower() in PROHIBITED_SUFFIXES
    ]

    assert prohibited_files == []
