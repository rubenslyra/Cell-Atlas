# Cell-Atlas — roteiro do vídeo e guia de interpretação

> Vídeo de 2 a 3 minutos para recrutadores. Números da execução de referência (`random_state=0`, Leiden 0,6).
> Antes de gravar, rode `cellatlas run-all` e confira com `resultados/resumo_grupos.csv`.
> Slides: [`docs/apresentacao/`](https://rubenslyra.github.io/Cell-Atlas/apresentacao/) · Treino com voz e cronômetro: [`docs/treino/`](https://rubenslyra.github.io/Cell-Atlas/treino/)

## Mensagem central

**Em uma frase:** a partir de 2.700 células do sangue, sem dizer ao algoritmo o que procurar, o Cell-Atlas reencontra sozinho os 7 tipos de células imunes conhecidos — com um único comando reprodutível.

O recrutador precisa sair convencido de três coisas:

1. **Você resolve problemas reais com dados:** o resultado bate com a referência da área (tutorial oficial do Scanpy sobre o PBMC3k).
2. **Você escreve software de verdade:** pacote instalável, CLI, configuração por arquivo, testes automatizados (pytest) e semente fixa.
3. **Você sabe explicar:** traduz um resultado técnico em uma história clara.

## Roteiro narrado (2min45s)

| Tempo | Na tela | Narração |
| --- | --- | --- |
| 0:00–0:15 | Slide 1 — título e UMAP colorido por tipo celular | “Uma gota de sangue tem dezenas de tipos de células imunes. A pergunta é: dá para descobrir quais são olhando só para os genes que cada célula usa, sem dizer ao computador o que procurar? Esse é o Cell-Atlas.” |
| 0:15–0:35 | Slide 2 — 2.700 células × 32.738 genes | “O dado vem de sequenciamento de RNA de célula única: 2.700 células, e para cada uma, a atividade de mais de 32 mil genes. São quase 90 milhões de números, e nenhum rótulo dizendo que célula é qual.” |
| 0:35–1:05 | Slide 3 — pipeline em 5 etapas | “Construí um pipeline em cinco etapas. Primeiro, controle de qualidade: descarto células danificadas e ficam 2.638. Depois normalizo, seleciono os 2.000 genes mais informativos e comprimo tudo em 10 componentes principais. Em seguida, ligo cada célula às 15 mais parecidas, formando uma rede, e o algoritmo Leiden encontra as comunidades nessa rede.” |
| 1:05–1:25 | Slide 4 — `umap_todas_resolucoes.png` | “O Leiden tem um botão de zoom, a resolução. Em 0,2 vejo 6 grupos, as grandes famílias. Em 1,0, 13 grupos, já com subtipos. Escolhi 0,6, com 10 grupos: detalhe suficiente sem fragmentar populações.” |
| 1:25–1:55 | Slide 5 — marcadores e tipos celulares | “Agora a parte que convence. Para cada grupo, o programa mede genes-marcadores clássicos da imunologia e sugere um nome. Ele reencontrou células T, B, NK, dois tipos de monócitos, células dendríticas e até 14 plaquetas — 0,5% da amostra. É o mesmo resultado da análise de referência da área.” |
| 1:55–2:25 | Slide 6 — terminal com `cellatlas run-all` e testes | “Por trás disso há engenharia: um pacote Python instalável, uma linha de comando, parâmetros por arquivo, semente fixa para o resultado ser sempre o mesmo e testes automatizados. Qualquer pessoa clona, roda um comando e obtém exatamente estas figuras.” |
| 2:25–2:45 | Slide 7 — o que aprendi e link | “O que levo daqui: transformar um dado enorme e sem rótulos em uma resposta que um especialista reconhece, com código que outra pessoa consegue reproduzir. O código está no GitHub. Obrigado.” |

## Guia de interpretação

O resultado é confiável porque duas evidências concordam: os grupos surgem só da semelhança entre células, e depois os marcadores conhecidos da biologia confirmam o nome de cada grupo.

**As etapas, em linguagem simples**

1. **Controle de qualidade (2.700 → 2.638 células, 32.738 → 13.656 genes).** Sai célula com menos de 200 genes (vazia), com mais de 2.500 (provavelmente duas células grudadas) ou com mais de 5% de RNA mitocondrial (morrendo). Saem genes vistos em menos de 3 células.
2. **Normalização e genes variáveis.** Cada célula é escalada para 10 mil contagens e passa por log. Ficam os 2.000 genes que mais variam: são eles que distinguem tipos.
3. **PCA (10 componentes).** Comprime 2.000 dimensões em 10 eixos que concentram a variação útil.
4. **Grafo k-NN (k = 15) e Leiden.** Cada célula se liga às 15 mais parecidas; o Leiden procura comunidades. A resolução controla o tamanho dos grupos.
5. **UMAP.** Desenha a rede em 2D. Serve para visualizar, não para medir distâncias entre ilhas.
6. **Marcadores e anotação.** O Wilcoxon acha os genes mais característicos de cada grupo; cada grupo recebe o tipo cujo conjunto de marcadores clássicos está mais expresso nele.

**Como ler cada figura**

- `pca_variancia.png` — a curva achata por volta do 10º componente: justifica usar 10.
- `umap_todas_resolucoes.png` — mesmas células, quatro níveis de zoom (6, 9, 10 e 13 grupos). Os grupos se subdividem em vez de se embaralharem.
- `genes_marcadores.png` — os 5 genes que mais diferenciam cada grupo (CD79A nas B, S100A8/9 e LYZ nos monócitos, GZMB e PRF1 nas NK).
- `marcadores_classicos.png` — cada painel acende onde um marcador é expresso; as regiões coincidem com os grupos.
- `umap_tipos_celulares.png` — o mapa final, com o nome sugerido em cada grupo.

## Os 10 grupos (Leiden 0,6)

| Grupo | Células | Top genes | Tipo sugerido | O que dizer |
| --- | ---: | --- | --- | --- |
| 0 | 737 | RPS12, RPS6, RPS27 | T cells | T naïve; genes ribossomais dominam |
| 1 | 332 | CCL5, NKG7, B2M | T cells | T CD8+ citotóxicas |
| 2 | 344 | CD74, CD79A, HLA-DRA | B cells | Linfócitos B |
| 3 | 330 | LTB, IL32, CD3D | T cells | T CD4+ de memória |
| 4 | 196 | LST1, COTL1, FCER1G | FCGR3A+ Monocytes | Monócitos não clássicos (CD16+) |
| 5 | 14 | PF4, PPBP, NRGN | Platelets | Plaquetas: só 14 células e mesmo assim separadas |
| 6 | 142 | NKG7, GZMB, PRF1 | NK cells | Células NK |
| 7 | 443 | S100A9, LYZ, S100A8 | CD14+ Monocytes | Monócitos clássicos |
| 8 | 65 | MALAT1, RPL32, RPS3 | T cells | Pouco específico; possível baixa qualidade |
| 9 | 35 | HLA-DPA1, HLA-DPB1, HLA-DRA | Dendritic cells | Células dendríticas |

Células T somam 1.464 das 2.638 células (55%).

## Limitações e como falar delas

- **Os rótulos são sugestões.** A confirmação final é biológica.
- **Granularidade.** T CD8+ (grupo 1) ficam como “T cells”. Próximo passo: marcadores para CD4, CD8 e memória.
- **Grupo 8.** Padrão típico de baixa qualidade. Próximo passo: filtro mais rígido ou detecção de dupletos.
- **Um doador, 2.700 células.** Valida o método, não é achado novo. Próximo passo: amostras maiores.
- **Resolução escolhida pelo analista.** Próximo passo: métrica de estabilidade (silhueta).
- **Versões das bibliotecas** podem mudar levemente a contagem de grupos.

## Perguntas prováveis

| Pergunta | Resposta curta |
| --- | --- |
| Como você sabe que está certo? | O PBMC3k é referência pública com resposta conhecida; os grupos batem com o tutorial do Scanpy e com marcadores clássicos. |
| Por que Leiden e não k-means? | k-means exige o número de grupos e supõe grupos esféricos; Leiden acha comunidades no grafo e garante grupos conectados. |
| Por que 10 componentes e 15 vizinhos? | 10: a curva de variância achata ali. 15: padrão do Scanpy. Ambos configuráveis por arquivo. |
| Como garante reprodutibilidade? | Semente fixa em vizinhança, UMAP e Leiden; parâmetros num só lugar; um comando roda tudo. |
| Como o código está organizado? | Pacote em camadas (dados, análise, configuração, CLI), cada etapa atrás de uma interface. |
| O que os testes cobrem? | Marcadores após seleção de genes, ordenação dos grupos, atribuição de tipos, CLI e versão. |
| Maior dificuldade? | Marcadores sumiam após a seleção de genes variáveis; solução: matriz completa em `.raw` + teste de regressão. |
| Isso escala? | O fluxo é o mesmo; mudam armazenamento e, se preciso, GPU (rapids-singlecell). |
| Aplicação fora da biologia? | Agrupamento não supervisionado em alta dimensão: segmentação de clientes, comunidades em redes. |

## Checklist antes de publicar

- [ ] Rodar `cellatlas run-all` e conferir os números
- [ ] Rodar `pytest` e gravar a saída verde
- [ ] Ensaiar 3 vezes no modo **Ensaiar roteiro** do treino (meta: até 2min50s)
- [ ] Fazer a **Entrevista** do treino até média ≥ 75%
- [ ] Publicar com link para o repositório e o GitHub Pages na descrição
