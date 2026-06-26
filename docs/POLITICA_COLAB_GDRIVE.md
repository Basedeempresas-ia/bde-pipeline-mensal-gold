# Política operacional Colab/GDrive

## 1. Objetivo da política

Esta política define como o pipeline BDE Mensal Gold deve operar em Google Colab com persistência no Google Drive, antes da implementação de código real. O objetivo é separar responsabilidades, reduzir risco de perda de artefatos mensais, evitar processamento pesado em armazenamento persistente e estabelecer regras mínimas de restore, sync, checkpoints, manifests, QA, logs, segurança e reexecução.

Esta política é normativa para os próximos PRs do pipeline e não implementa execução real, download de dados, geração de bases ou criação de artefatos binários.

## 2. Separação de responsabilidades

- **GitHub:** código, documentação, configurações sem segredo, testes e CI.
- **Google Colab:** execução do pipeline.
- **`/content`:** processamento pesado temporário.
- **Google Drive:** persistência mensal dos dados e artefatos.

## 3. Regra principal

- Nunca processar bases grandes diretamente no Google Drive.
- Processar em `/content`.
- Sincronizar para Drive apenas em pontos controlados.

## 4. Estrutura local no Colab

A estrutura local de trabalho no Colab deve seguir o padrão:

```text
/content/bde_pipeline_mensal_gold/{competencia_slug}/
```

## 5. Estrutura persistente no Google Drive

A estrutura persistente mensal no Google Drive deve seguir o padrão:

```text
/content/drive/MyDrive/BDE/pipeline_mensal_gold/{competencia_slug}/
```

## 6. Estrutura mensal esperada

Cada competência deve conter, no mínimo, a seguinte estrutura lógica:

```text
raw/
staging/
processed/current/
processed/snapshots/
outputs/manifests/
outputs/qa/
outputs/checkpoints/
exports/current/
logs/
```

## 7. Fluxo de inicialização

O fluxo de inicialização deve executar, no mínimo, os seguintes passos:

1. Montar Google Drive.
2. Carregar config.
3. Validar `competencia_slug`.
4. Criar `run_id`.
5. Verificar se a pasta mensal existe em `/content`.
6. Se não existir em `/content`, verificar no Drive.
7. Se existir no Drive, restaurar para `/content`.
8. Se não existir em nenhum lugar, criar estrutura nova.
9. Registrar manifest inicial.

## 8. Fluxo de restore

- O restore deve copiar artefatos persistidos do Drive para `/content`.
- Validar estrutura.
- Validar manifests.
- Validar checkpoints.
- Não sobrescrever `/content` sem confirmação se houver execução em andamento.

## 9. Fluxo de sync

- Sincronizar `/content` para Drive após stages críticos.
- Gerar manifest de sync.
- Registrar tamanho, quantidade de arquivos e status.
- Criar checkpoint apenas depois do sync validado.

## 10. Pontos mínimos de sync

Os pontos mínimos de sync são:

- Após aquisição de fontes.
- Após normalização de estabelecimentos.
- Após geração de base ativa.
- Após PGFN/regimes.
- Após base final.
- Após exportações.

## 11. Política de checkpoints

- Deve existir checkpoint `.ok` por stage.
- Checkpoint só pode ser criado após QA mínimo passar.
- Checkpoint deve conter `run_id`, competência, stage, data/hora e status.

## 12. Política de manifests

Devem existir os seguintes manifests:

- Manifest por stage.
- Manifest de arquivos brutos.
- Manifest de artefatos processados.
- Manifest de sync Drive.

Campos mínimos dos manifests:

- `run_id`.
- `competencia`.
- `stage`.
- `caminho_local`.
- `caminho_drive`.
- `linhas`, quando aplicável.
- `tamanho_bytes`.
- `sha256`, quando aplicável.
- `status`.
- `data_processamento`.

## 13. Política de QA

- QA antes de checkpoint.
- QA antes de sync.
- QA antes de exportação.
- Cardinalidade obrigatória nos joins críticos.

## 14. Política de logs

- Logs por `run_id`.
- Logs em `/content` durante execução.
- Logs sincronizados para Drive ao final.
- Não versionar logs no Git.

## 15. Política de segurança

- Não salvar tokens no notebook.
- Não salvar `.env` no Git.
- Não expor credenciais.
- Configs versionadas devem ser templates sem segredo.

## 16. Política de arquivos proibidos no Git

ZIP, CSV, CSV.GZ, Parquet, DuckDB, SQLite, XLSX, dumps e dados reais não entram no Git.

## 17. Política de falha

- Se o Drive não montar, parar.
- Se restore falhar, parar.
- Se sync falhar, não criar checkpoint.
- Se QA falhar, não criar checkpoint.
- Se cardinalidade quebrar, falhar stage.

## 18. Política de reexecução

- Stage pode ser reexecutado se não houver checkpoint válido.
- Se houver checkpoint válido, exigir confirmação manual para reprocessar.
- Nunca sobrescrever artefato final sem backup ou snapshot.

## 19. Política de snapshots

- `processed/current` representa a versão corrente da competência.
- `processed/snapshots` pode guardar versões intermediárias ou versões validadas.
- Snapshot não deve ser criado para todo arquivo temporário, apenas marcos relevantes.

## 20. Próximos PRs recomendados

- Add stage 00 admin environment setup.
- Add stage 01 source acquisition.
- Add stage 02 active establishments artifacts.
