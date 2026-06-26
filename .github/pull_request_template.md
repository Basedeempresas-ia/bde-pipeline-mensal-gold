## Resumo

- 

## Tipo de mudança

- [ ] Governança/documentação
- [ ] Estrutura base
- [ ] Correção
- [ ] Outro

## Checklist

- [ ] Não baixei dados reais.
- [ ] Não implementei pipeline real fora do escopo aprovado.
- [ ] Não versionei arquivos ZIP, CSV, Parquet, DuckDB, SQLite, XLSX ou binários.
- [ ] Rodei as validações aplicáveis.

## Validações

```bash
python -m compileall bde_pipeline
python -m pytest -q tests
git diff --check
```
