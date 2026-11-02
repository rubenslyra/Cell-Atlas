# Cell-Atlas: Construção de um Mapa Celular por Meio de Análise de Dados de Sequenciamento de RNA de Célula Única

_Projeto de Pesquisa Aplicada em Bioinformática_
**Autor:** Rubens Lyra
**Data:** 01 de novembro de 2026
**Repositório:** https://github.com/rubenslyra/Cell-Atlas

---

## Resumo

A compreensão da heterogeneidade celular em tecidos biológicos representa um dos maiores avanços da biologia contemporânea. O sequenciamento de RNA de célula única (scRNA-seq) permite perfilar a expressão gênica de milhares de células individualmente, superando a limitação das abordagens tradicionais que fornecem apenas valores médios de populações celulares mistas. O presente trabalho descreve a construção de um fluxo completo e reprodutível para aquisição, processamento, agrupamento e anotação de dados de scRNA-seq. Utilizando o conjunto de referência PBMC3k — composto por aproximadamente 2.700 células imunes humanas — implementou-se o algoritmo de agrupamento Leiden em múltiplas resoluções, permitindo visualizar a estrutura celular em diferentes níveis de detalhe. Os resultados demonstram a capacidade de separar populações celulares conhecidas (linfócitos T, linfócitos B, monócitos e células NK) a partir exclusivamente de seus perfis transcricionais. Este trabalho estabelece uma base metodológica transparente e documentada para estudos futuros, alinhando-se aos princípios de reprodutibilidade em ciência computacional.

**Palavras-chave:** Bioinformática · Sequenciamento de célula única · Agrupamento Leiden · Expressão gênica · Células imunes

---

## 1. Introdução

### 1.1 Contexto e Justificativa

Por muito tempo, a análise molecular de tecidos biológicos baseou-se em medições agregadas, nas quais o sinal obtido refletia a média de milhares ou milhões de células. Essa abordagem ocultava a diversidade intrínseca dos tecidos, na qual células vizinhas podem desempenhar funções distintas e responder de maneira diferenciada a estímulos, doenças e tratamentos.

O advento do sequenciamento de RNA de célula única (scRNA-seq), no entanto, transformou essa paisagem. A tecnologia permite a quantificação simultânea da expressão de milhares de genes em cada célula individualmente, gerando conjuntos de dados de alta dimensionalidade que revelam a arquitetura celular de amostras biológicas com resolução sem precedentes. Iniciativas como o _Human Cell Atlas_ têm como objetivo mapear sistematicamente todos os tipos celulares do corpo humano, tarefa que depende inteiramente de métodos computacionais capazes de transformar matrizes de dados em conhecimento biológico.

### 1.2 Problema de Pesquisa

Apesar do potencial transformador, os dados de scRNA-seq apresentam desafios analíticos significativos:

- Cada amostra contém milhares de células, cada uma descrita pela atividade de milhares de genes;
- A estrutura biológica — grupos de células com perfis semelhantes — não é conhecida _a priori_;
- A granularidade de interesse pode variar: em alguns casos busca-se grandes populações; em outros, subtipos raros.

Portanto, faz-se necessário um fluxo analítico capaz de reduzir a dimensionalidade dos dados, identificar grupos naturais e interpretar esses grupos em termos biológicos.

### 1.3 Objetivos

Este trabalho tem por objetivos:

1. Implementar um pipeline reprodutível de análise de scRNA-seq, desde a obtenção pública dos dados até a anotação biológica dos resultados;
2. Avaliar o comportamento do algoritmo Leiden em diferentes resoluções, demonstrando como este parâmetro influencia a interpretação biológica;
3. Estabelecer uma referência documentada e citável para estudos subsequentes em bioinformática de célula única.

---

## 2. Materiais e Métodos

### 2.1 Conjunto de Dados

Utilizou-se o conjunto **PBMC3k**, composto por 2.700 células mononucleares de sangue periférico humano, gerado pela plataforma 10x Genomics. Este é amplamente reconhecido como referência para validação de métodos na área, sendo acessível via repositório público Scanpy e alternativamente sob identificação **GSE139324** no repositório NCBI Gene Expression Omnibus (GEO).

### 2.2 Ambiente Computacional

As análises foram realizadas em Python 3.9+, utilizando-se as bibliotecas:

- **Scanpy** v1.10 — processamento e análise de dados de célula única;
- **Leidenalg** v0.10 — implementação do algoritmo de agrupamento;
- **Matplotlib** e **Pandas** — visualização e manipulação de dados.

### 2.3 Fluxo Analítico

O processo seguiu boas práticas consolidadas na literatura:

#### 2.3.1 Controle de Qualidade e Filtragem

Removeram-se células com menos de 200 genes detectados ou mais de 2.500 genes (possíveis duplicações), bem como células com mais de 5% de contagens em genes mitocondriais (indicativo de degradação celular). Genes presentes em menos de 3 células foram excluídos.

#### 2.3.2 Normalização e Redução de Dimensionalidade

Aplicou-se normalização por soma total (10 mil contagens por célula) seguida de transformação logarítmica. Selecionaram-se os 2.000 genes com maior variabilidade de expressão para análise. Após escalonamento, realizou-se Análise de Componentes Principais (PCA) para redução de dimensionalidade.

#### 2.3.3 Construção do Grafo de Vizinhança

Construiu-se um grafo k-vizinhos mais próximos (k-NN), no qual cada célula é representada por um nó conectado às 15 células com perfis genéticos mais semelhantes, considerando os 10 primeiros componentes principais. Este grafo representa a estrutura de afinidade celular na amostra.

#### 2.3.4 Agrupamento com Algoritmo Leiden

Aplicou-se o algoritmo de detecção de comunidades Leiden, que otimiza a modularidade do grafo de vizinhança. Diferentemente de métodos anteriores (como Louvain), o Leiden garante a conectividade interna dos grupos formados, tornando-o o padrão atual em scRNA-seq. Testaram-se as resoluções 0,2; 0,4; 0,6 e 1,0 — parâmetro que controla a granularidade dos agrupamentos.

#### 2.3.5 Visualização e Anotação

Projetou-se a estrutura em duas dimensões pelo método UMAP. Identificaram-se genes diferencialmente expressos por grupo (teste de Wilcoxon) e comparou-se com marcadores canônicos de populações imunes humanas.

---

## 3. Resultados

### 3.1 Controle de Qualidade

O conjunto inicial de 2.700 células foi reduzido a aproximadamente 2.600 células após filtragem, mantendo-se cerca de 13 mil genes. A análise de variância explicada pela PCA mostrou declínio acentuado após os primeiros 10 componentes, justificando a retenção destes para construção do grafo.

### 3.2 Agrupamento em Múltiplas Resoluções

O número de grupos identificados variou conforme a resolução aplicada:

- **0,2** → ~4–5 grupos (visão ampla: grandes famílias celulares)
- **0,6** → ~8–10 grupos (equilíbrio entre detalhe e estabilidade)
- **1,0** → ~12–15 grupos (visão detalhada: subtipos e estados celulares)

A projeção UMAP mostrou clara separação entre populações, com aglomerados distintos correspondentes a linhagens celulares diferentes.

### 3.3 Anotação Biológica

A análise de genes marcadores permitiu associar os grupos a tipos celulares conhecidos:

- **CD3E+, CD3D+** → Células T
- **MS4A1+, CD79A+** → Células B
- **CD14+, LYZ+** → Monócitos
- **NKG7+, GNLY+** → Células NK

---

## 4. Discussão

O uso do algoritmo Leiden demonstrou-se adequado para este conjunto de dados, permitindo identificar as principais populações de células mononucleares do sangue periférico. A comparação entre resoluções evidencia a importância da escolha criteriosa deste parâmetro: resoluções muito baixas podem agrupar subtipos distintos, enquanto resoluções muito altas podem subdividir artificialmente populações homogêneas.

A metodologia adotada segue as boas práticas propostas por Luecken e Theis (2019), garantindo reprodutibilidade e comparabilidade com outros estudos. Além disso, o uso de um conjunto de dados público e amplamente validado permite que este pipeline sirva como ponto de partida para análises mais complexas, incluindo integração de múltiplas amostras, análise de trajetórias celulares e inferência de redes reguladoras.

---

## 5. Conclusão

Este trabalho apresenta um pipeline completo, transparente e reprodutível para análise de scRNA-seq. A partir do conjunto PBMC3k, foi possível construir um mapa celular que identifica corretamente as principais populações imunes humanas. O código-fonte, dados documentados e figuras geradas estão organizados no repositório Cell-Atlas, visando facilitar a reutilização por estudantes e pesquisadores da área de bioinformática.

---

## Referências Bibliográficas

- Wolf, F. A., Angerer, P. & Theis, F. J. SCANPY: large-scale single-cell gene expression data analysis. _Genome Biol._ 19, 15 (2018). https://doi.org/10.1186/s13059-017-1382-0
- Traag, V. A., Waltman, L. & van Eck, N. J. From Louvain to Leiden: guaranteeing well-connected communities. _Sci. Rep._ 9, 5233 (2019). https://doi.org/10.1038/s41598-019-41695-z
- Luecken, M. D. & Theis, F. J. Current best practices in single-cell RNA-seq analysis: a tutorial. _Mol. Syst. Biol._ 15, e8746 (2019). https://doi.org/10.15252/msb.20188746
- Zheng, G. X. Y. et al. Massively parallel digital transcriptional profiling of single cells. _Nat. Commun._ 8, 14049 (2017). https://doi.org/10.1038/ncomms14049
