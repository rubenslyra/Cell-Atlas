# Cell-Atlas

**Construção de um Mapa Celular por Meio de Análise de Dados de Sequenciamento de RNA de Célula Única**

Este projeto implementa um fluxo completo e reprodutível para aquisição, processamento, agrupamento e anotação de dados de scRNA-seq. Utiliza o conjunto de referência **PBMC3k** (células mononucleares de sangue periférico humano) para demonstrar a separação de populações celulares imunes a partir de seus perfis transcricionais.

## Objetivos

1. Implementar um pipeline reprodutível de análise de scRNA-seq, desde a obtenção pública dos dados até a anotação biológica dos resultados
2. Avaliar o comportamento do algoritmo Leiden em diferentes resoluções
3. Estabelecer uma referência documentada e citável para estudos subsequentes em bioinformática de célula única

## Estrutura do Projeto

```
Cell-Atlas/
├── README.md                  # Apresentação científica completa
├── ARTIGO_PROJETO.md          # Artigo acadêmico do projeto
├── requisitos.txt             # Ambiente reprodutível
├── .gitignore                 # Arquivos que não sobem ao repositório
├── dados/
│   └── fonte.txt              # Procedência documentada
└── scripts/
    ├── 01_baixar_dados.py     # Aquisição transparente
    ├── 02_processar.py        # QC → Normalização → PCA
    ├── 03_agrupar.py          # Grafo k-NN → Leiden → UMAP
    └── 04_anotar.py           # Marcadores → Tipos celulares
```

## Instalação

```bash
# Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requisitos.txt
```

## Execução

Execute os scripts em ordem:

```bash
python scripts/01_baixar_dados.py
python scripts/02_processar.py
python scripts/03_agrupar.py
python scripts/04_anotar.py
```

## Referências

- Wolf et al. (2018) SCANPY: large-scale single-cell gene expression data analysis. *Genome Biology* 19:15. DOI:10.1186/s13059-017-1382-0
- Traag et al. (2019) From Louvain to Leiden: guaranteeing well-connected communities. *Scientific Reports* 9:5233. DOI:10.1038/s41598-019-41695-z
- Luecken & Theis (2019) Current best practices in single-cell RNA-seq analysis: a tutorial. *Molecular Systems Biology* 15:e8746. DOI:10.15252/msb.20188746
- 10x Genomics — Official PBMC3k Dataset
