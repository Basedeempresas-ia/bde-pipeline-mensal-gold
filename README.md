# BDE Pipeline Mensal Gold

Repositório de governança e estrutura base do pipeline mensal gold da Base de Empresas (BDE).

## Objetivo

Este repositório organiza a documentação, os contratos mínimos e a estrutura inicial para evolução futura do pipeline mensal gold.

## Escopo atual

Esta versão contém somente a base de governança do repositório:

- documentação inicial de governança;
- visão arquitetural conceitual;
- template de configuração;
- pacotes Python vazios para evolução futura;
- contrato automatizado para garantir a estrutura mínima.

## Fora de escopo nesta etapa

- download de dados reais;
- implementação de pipeline real;
- geração ou versionamento de arquivos ZIP, CSV, Parquet, DuckDB, SQLite, XLSX ou binários;
- inclusão de segredos, tokens ou credenciais.

## Estrutura

```text
.github/
  pull_request_template.md
  workflows/ci.yml
configs/
  config_template.yaml
bde_pipeline/
  __init__.py
  core/__init__.py
  stages/__init__.py
docs/
  ARQUITETURA_PIPELINE_MENSAL_GOLD.md
  GOVERNANCA_REPOSITORIO.md
notebooks/
  .gitkeep
tests/
  test_repository_contract.py
```

## Validações locais

```bash
python -m compileall bde_pipeline
python -m pytest -q tests
git diff --check
```
