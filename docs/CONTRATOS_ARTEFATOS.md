# Contratos dos Artefatos Mensais do Pipeline BDE Gold

## 1. Objetivo do documento

Este documento define os contratos esperados dos artefatos mensais do pipeline BDE Gold antes da implementação de código real. Ele descreve a competência mensal, a estrutura de diretórios, os contratos por stage, os requisitos mínimos de QA, manifests, checkpoints, regras anti-cardinalidade e regras de exportação comercial.

Este contrato é documental e não autoriza, por si só, download de dados reais, geração de arquivos de dados, criação de ZIPs, CSVs, Parquets, DuckDBs, SQLite, XLSX, binários ou implementação de pipeline real.

## 2. Definição de competência mensal

Cada execução mensal deve ser identificada pelos seguintes campos:

- `ano_referencia`: ano da competência de referência, com quatro dígitos.
- `mes_referencia`: mês da competência de referência, com dois dígitos de `01` a `12`.
- `competencia`: identificador mensal no formato `AAAA-MM`.
- `competencia_slug`: identificador seguro para caminhos e nomes de artefatos no formato `AAAA_MM`.
- `data_processamento`: data e horário em que a execução foi processada.
- `run_id`: identificador único da execução mensal.

## 3. Estrutura mensal esperada

A estrutura mensal esperada dos artefatos é:

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

## 4. Contrato por stage

### stage_00_admin_ambiente

- **Objetivo:** preparar e validar o ambiente operacional da execução mensal.
- **Entradas:** configuração da execução, competência mensal, caminhos esperados e parâmetros administrativos.
- **Saídas:** estrutura de diretórios mensal validada e metadados administrativos da execução.
- **QA:** validar presença dos diretórios obrigatórios, consistência da competência, existência do `run_id` e ausência de segredos versionados.
- **Checkpoint:** `outputs/checkpoints/stage_00_admin_ambiente.ok`.

### stage_01_aquisicao_fontes

- **Objetivo:** registrar a aquisição das fontes oficiais necessárias para a competência mensal.
- **Entradas:** configuração de fontes, competência mensal e parâmetros de aquisição.
- **Saídas:** fontes recebidas ou referenciadas em `raw/` e registros de aquisição.
- **Manifest obrigatório:** manifest com fonte, artefato, caminho, tamanho, data de aquisição, status e hash quando aplicável.
- **QA:** validar existência e integridade mínima das fontes esperadas, sem interpretar regras de negócio dos dados.
- **Checkpoint:** `outputs/checkpoints/stage_01_aquisicao_fontes.ok`.

### stage_02_estabelecimentos_ativos

**Artefatos:**

- `processed/current/base_estabelecimentos_normalizada_completa.parquet`
- `processed/current/base_estabelecimentos_ativos.parquet`
- `processed/current/cnpjs_ativos_mes.parquet`

**Regras:**

- `cnpj` deve ser `VARCHAR` com 14 dígitos.
- `cnpj_basico` deve ser `VARCHAR` com 8 dígitos.
- `situacao_cadastral = '02'` define estabelecimento ativo.
- A base completa preserva ativos e inativos.
- A base ativa é a base-mãe comercial.

### stage_03_empresas_ativas

**Artefato:**

- `processed/current/empresas_cnpj_basico_ativos.parquet`

**Regra:**

- Filtrar por `cnpj_basico` presente em `cnpjs_ativos_mes`.

### stage_04_socios_relacional_ativos

**Artefato:**

- `processed/current/socios_unificado_cnpj_basico_ativos.parquet`

**Regras:**

- Pode haver várias linhas por `cnpj_basico`.
- Este artefato nunca entra direto no join final.

### stage_05_socios_colunas

**Artefato:**

- `processed/current/socios_colunas_por_cnpj_basico.parquet`

**Regras:**

- Deve conter uma linha por `cnpj_basico`.
- Deve conter `qtd_socios_total`.
- Deve conter `qtd_socios_exportados_em_colunas`.
- Deve conter `flag_socios_truncados`.

### stage_06_simples_mei_ativos

**Artefato:**

- `processed/current/simples_mei_cnpj_basico_ativos.parquet`

**Regras:**

- Simples/MEI é oficial mensal.
- Não inferir MEI/SIMPLES.

### stage_07_regimes_regulares_ativos

**Artefatos:**

- `processed/current/regimes_regulares_resolvidos_por_cnpj.parquet`
- `processed/current/regimes_regulares_cnpjs_ativos.parquet`

**Regras:**

- Normalizar CNPJ mascarado para 14 dígitos.
- Filtrar por `cnpj` presente em `cnpjs_ativos_mes`.

### stage_08_pgfn_flags_ativos

**Artefatos:**

- `processed/current/pgfn_flags_por_cnpj.parquet`
- `processed/current/pgfn_flags_cnpjs_ativos.parquet`

**Regras:**

- PGFN detalhada nunca entra direto no join final.
- Deve haver agregação por CNPJ antes do join.
- A exportação comercial deve usar flags `SIM`/`NÃO`.
- Tipos esperados: `FGTS`, `NAO_PREVIDENCIARIO`, `PREVIDENCIARIO`.

### stage_09_estado_tributario_pgf

**Artefato:**

- `processed/current/estado_tributario_pgf_cnpj_ativo.parquet`

**Regras:**

- Deve conter uma linha por CNPJ ativo.
- Dívida complementa regime, não substitui regime.

### stage_10_base_final_enriquecida

**Artefato:**

- `processed/current/base_cnpj_enriquecida_tributaria_pgf.parquet`

**Regra crítica:**

- `linhas_base_final = linhas_base_estabelecimentos_ativos`.
- Se a cardinalidade quebrar, o stage deve falhar.

### stage_11_duckdb_analitico

**Artefato:**

- `processed/current/base_cnpj_enriquecida_tributaria_pgf.duckdb`

**Regras:**

- DuckDB é camada analítica.
- DuckDB não decide regime.

### stage_12_exportacoes

**Diretórios:**

- `exports/current/por_regime/`
- `exports/current/por_divida/`
- `exports/current/por_regime_divida/`
- `exports/current/contagens/`
- `exports/current/amostras/`
- `exports/current/metodologia/`

## 5. QA obrigatório por stage

Todo stage deve produzir QA mínimo com os seguintes campos:

- `linhas_entrada`
- `linhas_saida`
- `chaves_nulas`
- `duplicidade_de_chave`
- `cardinalidade_preservada`
- `top_erros`
- `checkpoint_ok`

## 6. Manifest obrigatório por stage

Todo stage deve produzir manifest mínimo com os seguintes campos:

- `run_id`
- `competencia`
- `stage`
- `artefato`
- `caminho`
- `linhas`
- `colunas`
- `tamanho_bytes`
- `sha256` quando aplicável
- `data_processamento`
- `status`

## 7. Checkpoints

- Cada stage concluído deve gerar um checkpoint `.ok`.
- O checkpoint só pode ser criado após o QA mínimo passar.

## 8. Regras anti-cardinalidade

- Fontes com múltiplas linhas por CNPJ devem ser agregadas antes do join final.
- PGFN detalhada não entra direto no join final.
- Sócios relacionais não entram direto no join final.

## 9. Regras de exportação comercial

- Dívida comercial deve ser exposta apenas como flags.
- Valores e detalhes da PGFN ficam fora da entrega comercial padrão.
- Dados reais e exportações não são versionados no Git.

## 10. Próximos PRs recomendados

- Add Colab GDrive operational policy
- Add stage 00 admin environment setup
- Add stage 01 source acquisition
- Add stage 02 active establishments artifacts
