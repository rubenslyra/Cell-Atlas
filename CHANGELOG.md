# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-01

### Added

- **Scaffold inicial**: Estrutura base do projeto `Cell-Atlas` com diretórios `dados/`, `scripts/`, `figuras/`, `resultados/`.
- **Pipeline reprodutível**: Scripts `01_baixar_dados.py`, `02_processar.py`, `03_agrupar.py` e `04_anotar.py` seguindo boas práticas de análise scRNA-seq.
- **Documentação científica**: `README.md` com apresentação do projeto e `ARTIGO_PROJETO.md` com artigo acadêmico completo.
- **Ambiente reprodutível**: `requisitos.txt` com dependências necessárias para execução do pipeline.
- **Rastreabilidade de dados**: `dados/fonte.txt` com procedência do conjunto PBMC3k (10x Genomics / GEO GSE139324).
- **Git hygiene**: `.gitignore` configurado para artefatos de análise (`.h5ad`, figuras, resultados).
- **Documentação web (GitHub Pages)**: Diretório `docs/` com `index.html` estático, seguro e responsivo para publicação da documentação do projeto.
- **Marco inicial**: Release `v0.1.0` estabelecida como base para evolução do projeto seguindo GitFlow.
