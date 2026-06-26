# Governança do Repositório

Este documento define regras mínimas para manter o repositório do pipeline mensal gold seguro, auditável e estável.

## Princípios

1. Toda mudança deve passar por Pull Request para revisão.
2. A branch `main` deve representar apenas conteúdo revisado.
3. Dados reais não devem ser baixados ou versionados neste repositório.
4. Segredos, tokens e credenciais não devem ser adicionados ao Git.
5. Artefatos gerados devem permanecer fora do controle de versão.

## Arquivos proibidos no versionamento

Não versionar arquivos de dados ou binários, incluindo:

- ZIP;
- CSV;
- Parquet;
- DuckDB;
- SQLite;
- XLSX/XLS;
- binários e serializações locais.

## Fluxo recomendado

1. Criar branch a partir de `origin/main`.
2. Fazer a menor alteração possível para o objetivo aprovado.
3. Rodar validações locais.
4. Abrir Pull Request para `main`.
5. Aguardar revisão antes do merge.

## Validações mínimas

```bash
python -m compileall bde_pipeline
python -m pytest -q tests
git diff --check
```
