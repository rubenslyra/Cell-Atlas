# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-02

### Added

- **Arquitetura OOP em `src/cellatlas`** (core, data, analysis, utils, cli) com interfaces e `Config` centralizada.
- **Pontos de entrada**: `cellatlas <comando>` (console script), `python -m cellatlas` (`__main__.py`) e `python main.py` na raiz (sem instalação).
- **CLI**: `--version`, `--config` (TOML/JSON), `--data-dir`, `--figures-dir`, `--results-dir`, `--resolutions`, `--target-resolution`, `--seed` e `--debug`; códigos de saída corretos.
- **Anotação de tipos celulares**: cada cluster recebe um tipo sugerido (`obs["cell_type"]`) a partir de escores de marcadores canônicos; nova figura `umap_tipos_celulares.png` e coluna `Tipo_celular_sugerido` em `resumo_grupos.csv`.
- **Reprodutibilidade**: `random_state` aplicado a vizinhança, UMAP e Leiden.
- `cellatlas.example.toml`, testes de regressão (pytest) e validação estática de `docs/` no CI.
- **GitHub Pages reconstruído**: dados da execução atual (10 grupos, 7 tipos), explorador real de resoluções com os UMAPs do pipeline, tabela de grupos com as cores das figuras, comandos por sistema operacional com botão de copiar, tema claro/escuro.
- **`docs/treino/` — Cell-Atlas, em voz alta**: perguntas por microfone com resposta falada, entrevista simulada com pontuação por pontos-chave e ensaio do roteiro cronometrado; Claude opcional via chave da API do próprio usuário.
- **`docs/apresentacao/`**: os 7 slides do vídeo com notas do apresentador e `ROTEIRO.md` (roteiro, guia de interpretação, perguntas prováveis).
- Workflow `tests.yml` (pytest em Python 3.10 e 3.12) e arquivo `LICENSE` (MIT).

### Fixed

- Marcadores canônicos ausentes do subconjunto HVG: `.raw` agora guarda o transcriptoma completo antes da seleção de HVG.
- Ordenação numérica dos clusters no sumário (`0, 1, 10` em vez de `0, 10, 1`).
- `annotate` passa a salvar `pbmc3k_anotado.h5ad`.
- Opção `--config` era aceita mas ignorada.
- Filtro de mitocôndria retornava uma *view* do AnnData.
- `Config` não cria mais diretórios como efeito colateral ao ser instanciada.
- Procedência dos dados: PBMC3k não está no GEO sob GSE139324 (esse acesso pertence a outro estudo); referência corrigida para 10x Genomics / Zheng et al. (2017).
- Versões alinhadas entre `pyproject.toml`, pacote, README e docs.
- Site antigo mostrava 9 grupos, contagens desatualizadas, marcador inexistente (TRAC), simulação com dados inventados e comando de instalação obsoleto.
- `tools/check_docs.py` passa a validar todas as páginas de `docs/`, links relativos por página e código inline bloqueado pela CSP.

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
