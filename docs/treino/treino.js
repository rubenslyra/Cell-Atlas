/* Cell-Atlas, em voz alta — offline trainer with optional Claude (BYO API key).
   Vanilla JS. Speech: Web Speech API (recognition: Chrome/Edge; synthesis: all modern browsers). */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);

  /* ======================= Knowledge ======================= */
  const KB = `PROJETO: Cell-Atlas, pipeline reprodutível de RNA-seq de célula única (scRNA-seq) em Python, autor Rubens Lyra. Repositório github.com/rubenslyra/Cell-Atlas, versão 0.2.0.
OBJETIVO: a partir das 2.700 células do sangue (PBMC3k, 10x Genomics, Zheng et al. 2017), sem rótulos, reencontrar os tipos de células imunes só pela expressão gênica.
DADO: 2.700 células x 32.738 genes (cerca de 88 milhões de valores). Não está no GEO; vem da 10x Genomics via scanpy.datasets.pbmc3k().
ETAPAS: 1) QC: remove células com menos de 200 genes, mais de 2.500 (prováveis dupletos) e mais de 5% de RNA mitocondrial; genes em menos de 3 células. Resultado: 2.638 células x 13.656 genes. 2) Normalização para 10 mil contagens + log1p; matriz completa guardada em .raw; 2.000 genes altamente variáveis. 3) Escala e PCA com 10 componentes (a curva de variância achata no 10º). 4) Grafo k-NN com 15 vizinhos; Leiden (Traag et al. 2019) nas resoluções 0,2 (6 grupos), 0,4 (9), 0,6 (10) e 1,0 (13); escolhida 0,6. 5) UMAP para visualização (não mede distâncias entre ilhas). 6) Wilcoxon para marcadores; anotação automática por escore de marcadores clássicos escalado de 0 a 1 entre grupos (limiar 0,5).
MARCADORES: T (CD3E, CD3D, IL7R), B (MS4A1, CD79A), Monócitos CD14+ (CD14, LYZ), Monócitos FCGR3A+ (FCGR3A, MS4A7), NK (GNLY, NKG7), Dendríticas (FCER1A, CST3), Plaquetas (PPBP, PF4).
RESULTADO (Leiden 0,6, semente 0): 0 T naive 737 (RPS12, RPS6, RPS27); 1 T CD8 citotóxicas 332 (CCL5, NKG7, B2M); 2 B 344 (CD74, CD79A, HLA-DRA); 3 T CD4 memória 330 (LTB, IL32, CD3D); 4 Monócitos FCGR3A+ 196 (LST1, COTL1, FCER1G); 5 Plaquetas 14 (PF4, PPBP, NRGN); 6 NK 142 (NKG7, GZMB, PRF1); 7 Monócitos CD14+ 443 (S100A9, LYZ, S100A8); 8 T de baixa especificidade 65 (MALAT1, RPL32, RPS3); 9 Dendríticas 35 (HLA-DPA1, HLA-DPB1, HLA-DRA). Células T somam 1.464 de 2.638 (55%). Bate com o tutorial oficial do Scanpy.
ENGENHARIA: pacote instalável (pyproject, src/cellatlas) em camadas core/data/analysis/utils/cli com interfaces; CLI cellatlas (download, preprocess, cluster, annotate, run-all), também python -m cellatlas e python main.py; --config TOML/JSON, --resolutions, --target-resolution, --seed; semente fixa em vizinhança, UMAP e Leiden; gravação atômica dos .h5ad; 17 testes pytest; validação do site no CI.
VALIDAÇÃO (cellatlas compare): comparada aos rótulos de especialistas do tutorial clássico do PBMC3k nas mesmas 2.638 células, a anotação por marcadores tem acurácia 96,8% e ARI 0,96. Maiores discordâncias: 49 monócitos CD14+ rotulados como FCGR3A+ (provavelmente monócitos intermediários) e 12 NK rotuladas como T (grupo misto com T CD8+). ARI dos grupos Leiden 0,6 contra os rótulos finos: 0,64.
FUNDAMENTOS: PBMC = células mononucleares do sangue periférico (núcleo único e redondo): linfócitos T, B, NK, monócitos e dendríticas; separadas por gradiente de Ficoll (Bøyum, 1968). Hemácias, granulócitos e plaquetas não são PBMC; plaquetas contaminam a amostra. T CD4+ coordenam, T CD8+ matam células infectadas, B produzem anticorpos (MS4A1 = CD20, alvo do rituximabe), NK matam sem exposição prévia, monócitos fagocitam e viram macrófagos, dendríticas apresentam antígenos. PBMC3k: ~2.700 PBMC de um doador saudável, 10x Genomics, 2016, conjunto de ensino padrão. Arquivo .h5ad: AnnData em HDF5; X = matriz células x genes, obs = tabela das células, var = tabela dos genes, obsm = coordenadas (X_pca, X_umap), obsp = grafo, uns = resultados, raw = todos os genes. UMAP (McInnes 2018): visualização 2D que preserva vizinhança; distâncias entre ilhas e tamanhos não são confiáveis; os grupos vêm do Leiden.
DIFICULDADE REAL: marcadores clássicos sumiam por não estarem entre os 2.000 genes variáveis; solução: guardar a matriz completa em .raw antes do recorte, com teste de regressão.
LIMITAÇÕES: rótulos são sugestões; T CD8+ ficam como "T"; grupo 8 parece baixa qualidade; um doador e 2.700 células; resolução escolhida pelo analista; versões de bibliotecas podem mudar levemente a contagem.
PRÓXIMOS PASSOS: marcadores finos, detecção de dupletos, métrica de estabilidade (silhueta), integração de amostras maiores, GPU para escalar.`;

  const ASK_SYSTEM = `Você é o assistente de voz do projeto Cell-Atlas e ajuda o autor a entender os resultados e apresentá-los num vídeo para recrutadores. Responda em português do Brasil, em linguagem falada, para alguém inteligente que não é biólogo. No máximo 90 palavras. Sem markdown, listas ou emojis: o texto será lido por voz. Use só os fatos abaixo; se algo não constar, diga isso. Quando ajudar, termine com uma frase pronta começando com "No vídeo, você pode dizer:".\n\nFATOS:\n${KB}`;

  const FAQ = [
    { k: ["30 segundos", "resumo", "explique o projeto", "o que e o projeto", "pitch", "elevator"],
      a: "O Cell-Atlas pega 2.700 células do sangue, cada uma com a atividade de mais de 32 mil genes, e, sem dizer ao computador o que procurar, encontra 10 grupos que correspondem a 7 tipos de células imunes: T, B, NK, dois tipos de monócitos, dendríticas e plaquetas. Tudo roda com um comando, com semente fixa e testes automatizados." },
    { k: ["grupo", "cluster", "umap", "cada cor", "significa"],
      a: "Na resolução 0,6 há 10 grupos. Os grupos 0, 1, 3 e 8 são células T, 55% do total. O 2 é de células B, o 6 de NK, o 7 de monócitos clássicos, o 4 de monócitos CD16, o 9 de dendríticas e o 5 são 14 plaquetas." },
    { k: ["resolucao", "0,6", "0.6", "zoom", "granularidade"],
      a: "A resolução do Leiden funciona como zoom. Em 0,2 aparecem 6 grupos; em 1,0, 13. Em 0,6, com 10 grupos, cada tipo imune principal já está separado sem fragmentar populações homogêneas." },
    { k: ["certo", "correto", "valid", "confiavel", "confianca", "prova"],
      a: "O PBMC3k é uma referência com resposta conhecida. Os grupos bateram com o tutorial oficial do Scanpy, e os marcadores clássicos, como CD3E para T e MS4A1 para B, acendem exatamente nas regiões dos grupos correspondentes." },
    { k: ["leiden", "k-means", "kmeans", "louvain", "algoritmo"],
      a: "O k-means exige saber antes quantos grupos existem e supõe grupos esféricos. O Leiden encontra comunidades num grafo de vizinhança e garante que cada grupo seja bem conectado, corrigindo um defeito do Louvain." },
    { k: ["pca", "componentes", "10 componentes", "dimensao", "variancia"],
      a: "A PCA comprime os 2.000 genes mais variáveis em 10 eixos. A curva de variância explicada achata por volta do décimo componente; depois disso cada eixo acrescenta pouco e mais ruído do que sinal." },
    { k: ["vizinho", "15", "k-nn", "knn", "grafo"],
      a: "Cada célula é ligada às 15 células com perfil mais parecido, formando uma rede. Quinze é o padrão do Scanpy e equilibra estrutura local e ruído. O Leiden procura comunidades nessa rede." },
    { k: ["qualidade", "qc", "filtro", "mitocondrial", "2.638", "2638"],
      a: "O controle de qualidade remove células com menos de 200 genes, que estão vazias, com mais de 2.500, que provavelmente são duas células juntas, e com mais de 5% de RNA mitocondrial, que estão morrendo. Das 2.700 sobram 2.638." },
    { k: ["marcador", "wilcoxon", "anotacao", "nome", "tipo celular"],
      a: "Primeiro o teste de Wilcoxon acha os genes mais característicos de cada grupo. Depois, para cada tipo imune, o programa mede seus marcadores clássicos em cada grupo e dá ao grupo o tipo de maior escore." },
    { k: ["plaqueta", "14", "raro"],
      a: "São só 14 plaquetas, meio por cento da amostra, e mesmo assim o algoritmo as separou num grupo próprio, marcado por PF4 e PPBP. É um bom exemplo de sensibilidade a populações raras." },
    { k: ["grupo 8", "malat1", "baixa qualidade"],
      a: "O grupo 8 tem 65 células dominadas por MALAT1 e genes ribossomais, um padrão típico de células de baixa qualidade. Eu mostro isso como limitação e como próximo passo: um filtro mais rígido ou detecção de dupletos." },
    { k: ["limitacao", "fraqueza", "limite", "problema"],
      a: "Os nomes são sugestões automáticas; as T CD8 ficam só como T porque os marcadores são amplos; o grupo 8 parece de baixa qualidade; e é um único doador, então valida o método, não é uma descoberta nova." },
    { k: ["engenharia", "codigo", "arquitetura", "solid", "pacote", "organizado"],
      a: "É um pacote Python instalável em camadas: dados, análise, configuração e linha de comando. Cada etapa é uma classe atrás de uma interface, fácil de testar e trocar. Um comando, cellatlas run-all, roda tudo." },
    { k: ["teste", "pytest", "cobre"],
      a: "São 17 testes automatizados: preservação dos marcadores depois da seleção de genes, ordenação numérica dos grupos, atribuição de tipos, métricas de comparação de métodos, a linha de comando, os três pontos de entrada e a consistência de versão." },
    { k: ["reprodut", "semente", "seed", "mesmo resultado"],
      a: "A semente é fixa na vizinhança, no UMAP e no Leiden, os parâmetros ficam num só lugar e as dependências estão declaradas no pacote. Qualquer pessoa clona, roda um comando e obtém as mesmas figuras." },
    { k: ["dificuldade", "desafio", "bug", "aprendi"],
      a: "Os marcadores clássicos, como CD3E, sumiam porque não estão entre os 2.000 genes mais variáveis. Resolvi guardando a matriz completa antes do recorte e criei um teste para isso nunca mais regredir." },
    { k: ["escala", "escalar", "milhoes", "gpu", "grande"],
      a: "O fluxo é o mesmo para centenas de milhares de células; mudariam o armazenamento e, se necessário, a execução em GPU com rapids-singlecell." },
    { k: ["fora da biologia", "aplica", "negocio", "empresa", "cliente"],
      a: "É agrupamento não supervisionado em dado de alta dimensão. A mesma ideia serve para segmentar clientes, detectar comunidades em redes ou agrupar comportamentos de uso." },
    { k: ["abrir", "abertura", "comeco", "gancho", "video"],
      a: "Abra com a pergunta: dá para descobrir os tipos de células do sangue só pelos genes, sem dizer ao computador o que procurar? E mostre logo o mapa colorido com os nomes. Seu nome vem depois do gancho." },
    { k: ["pbmc", "mononuclear", "sangue periferico", "ficoll"],
      a: "PBMC são as células mononucleares do sangue periférico: as que têm um núcleo único e redondo, ou seja, linfócitos T, B e NK, monócitos e algumas dendríticas. Elas são separadas do resto do sangue por centrifugação sobre Ficoll. Hemácias, granulócitos e plaquetas ficam de fora, embora algumas plaquetas contaminem a amostra." },
    { k: ["celula t", "celulas t", "linfocito t", "cd4", "cd8"],
      a: "As células T amadurecem no timo. As T CD4 coordenam a resposta imune e as T CD8 matam células infectadas ou tumorais. No Cell-Atlas são os grupos 0, 1, 3 e 8, marcados por CD3E e CD3D, e somam 55% das células." },
    { k: ["celula b", "celulas b", "linfocito b", "anticorpo", "cd20", "ms4a1", "rituximabe"],
      a: "As células B produzem anticorpos. O marcador MS4A1 é o gene da proteína CD20, alvo do rituximabe, usado contra linfomas e doenças autoimunes. No Cell-Atlas são o grupo 2, com 344 células." },
    { k: ["nk", "natural killer", "matadora"],
      a: "As células NK, natural killer, destroem células infectadas ou tumorais sem precisar de exposição prévia, usando perforina e granzimas. Por compartilharem esses genes com as T CD8, ficam vizinhas no mapa." },
    { k: ["monocito", "macrofago", "cd14", "cd16", "fcgr3a"],
      a: "Monócitos patrulham o sangue, engolem micróbios e viram macrófagos nos tecidos. Os clássicos expressam CD14 e LYZ; os não clássicos expressam CD16, gene FCGR3A. Entre eles há monócitos intermediários, e é ali que o Cell-Atlas mais discorda dos especialistas." },
    { k: ["pbmc3k", "3k", "conjunto de dados", "dataset"],
      a: "O PBMC3k tem cerca de 2.700 PBMC de um doador saudável, sequenciadas pela 10x Genomics e publicadas em 2016. Virou o conjunto de ensino padrão porque é pequeno, público e tem resposta conhecida, usado nos tutoriais do Seurat e do Scanpy." },
    { k: ["h5ad", "anndata", "arquivo", "hdf5", "formato"],
      a: "O h5ad guarda um objeto AnnData dentro de um arquivo HDF5. No centro está a matriz X, de células por genes. Em obs fica a tabela das células, como o grupo e o tipo; em var, a tabela dos genes; em obsm, as coordenadas do PCA e do UMAP; em obsp, o grafo; e em raw, todos os genes antes do recorte." },
    { k: ["umap", "mapa", "visualizacao", "distancia entre"],
      a: "O UMAP achata os dados em duas dimensões mantendo juntas as células vizinhas. Ele serve para ver, não para medir: distância entre ilhas distantes e tamanho das ilhas não são confiáveis, e outra semente gera outro desenho. Os grupos vêm do Leiden, não do desenho." },
    { k: ["compar", "especialista", "celltypist", "acuracia", "ari", "validacao"],
      a: "Comparei a anotação automática com os rótulos de especialistas do tutorial clássico, nas mesmas 2.638 células: 96,8% de acurácia e ARI de 0,96. As maiores discordâncias são 49 monócitos CD14 rotulados como CD16, provavelmente intermediários, e 12 NK rotuladas como T." },
    { k: ["dado", "10x", "geo", "fonte"],
      a: "O dado é o PBMC3k da 10x Genomics, publicado por Zheng e colegas em 2017: 2.700 células do sangue de um doador saudável. É a referência padrão da área, baixada pelo próprio Scanpy." },
  ];

  const ASK_CHIPS = ["O que são PBMC?", "O que tem dentro do arquivo h5ad?", "Como comparei com especialistas?", "Explique o projeto em 30 segundos", "O que significa cada grupo no UMAP?", "Por que resolução 0,6?", "Como sei que o resultado está certo?", "Por que Leiden e não k-means?", "Qual foi a maior dificuldade?", "Quais limitações devo admitir?", "Como abro o vídeo?"];

  const INTERVIEW = [
    { q: "Me explique o Cell-Atlas em meio minuto, como se eu não fosse da área.",
      pts: [["o dado (células do sangue, genes)", ["celula", "sangue", "gene", "pbmc"]], ["sem rótulos / não supervisionado", ["sem rotulo", "sem dizer", "nao supervisionado", "sem saber", "sozinho"]], ["o resultado (7 tipos ou 10 grupos)", ["7 tipos", "sete tipos", "10 grupos", "dez grupos", "tipos imunes", "tipos de celula"]], ["reprodutível / um comando", ["reprodut", "um comando", "run-all", "semente"]]],
      model: "Peguei 2.700 células do sangue, cada uma descrita pela atividade de 32 mil genes, sem nenhum rótulo. Sem dizer ao algoritmo o que procurar, o pipeline encontrou 10 grupos que correspondem a 7 tipos de células imunes conhecidos. Tudo roda com um único comando reprodutível." },
    { q: "Como você sabe que os grupos que o algoritmo encontrou estão corretos?",
      pts: [["dataset de referência com resposta conhecida", ["referencia", "conhecid", "tutorial", "scanpy", "benchmark"]], ["marcadores clássicos confirmam", ["marcador", "cd3e", "ms4a1", "lyz", "nkg7"]], ["evidência independente / visual", ["acende", "umap", "independente", "visual", "coincide"]]],
      model: "O PBMC3k é uma referência pública com resposta conhecida, e meus grupos batem com o tutorial oficial do Scanpy. Além disso, marcadores clássicos como CD3E e MS4A1 acendem exatamente nas regiões dos grupos de células T e B: são duas evidências que concordam." },
    { q: "Por que você escolheu o Leiden e não um k-means, por exemplo?",
      pts: [["k-means exige número de grupos", ["numero de grupos", "quantos grupos", "k fixo", "definir o k", "saber antes"]], ["Leiden trabalha em grafo / comunidades", ["grafo", "comunidade", "rede", "vizinh"]], ["garante grupos conectados / melhora Louvain", ["conectad", "louvain"]]],
      model: "O k-means exige saber antes quantos grupos existem e supõe grupos esféricos. O Leiden encontra comunidades num grafo de vizinhança, não precisa do número de grupos e garante que cada grupo seja bem conectado, corrigindo o Louvain." },
    { q: "Como você decidiu a resolução de 0,6?",
      pts: [["testou várias resoluções", ["0,2", "0.2", "1,0", "1.0", "varias", "quatro", "compar"]], ["equilíbrio detalhe vs fragmentação", ["equilibr", "fragment", "detalhe", "zoom"]], ["número de grupos (10)", ["10 grupos", "dez grupos", "10"]]],
      model: "Testei quatro resoluções: 0,2, 0,4, 0,6 e 1,0, que deram 6, 9, 10 e 13 grupos. Em 0,6 cada tipo imune principal já aparece separado sem fragmentar populações homogêneas. É uma escolha do analista, e eu deixo isso configurável." },
    { q: "Qual foi a parte mais difícil do projeto e como você resolveu?",
      pts: [["problema concreto", ["marcador", "sumia", "hvg", "genes variaveis", "bug", "erro"]], ["solução técnica", ["raw", "matriz completa", "guardar", "antes do recorte"]], ["prevenção / teste", ["teste", "regress", "pytest"]]],
      model: "Os marcadores clássicos, como CD3E, sumiam porque não estão entre os 2.000 genes mais variáveis. Passei a guardar a matriz completa em .raw antes do recorte e escrevi um teste de regressão para isso não voltar." },
    { q: "Como o código está organizado? Por que não deixar tudo em scripts?",
      pts: [["pacote instalável / camadas", ["pacote", "camada", "modul", "src"]], ["interfaces / testável / trocável", ["interface", "testa", "trocar", "solid", "classe"]], ["CLI / um comando", ["cli", "comando", "run-all", "linha de comando"]]],
      model: "É um pacote Python instalável em camadas: dados, análise, configuração e linha de comando. Cada etapa é uma classe atrás de uma interface, o que facilita testar e trocar partes. Scripts soltos não garantem ordem, parâmetros nem reprodutibilidade." },
    { q: "Quais são as limitações desse resultado?",
      pts: [["rótulos são sugestões", ["sugest", "automatic", "confirma"]], ["um doador / amostra pequena", ["doador", "pequen", "2.700", "uma amostra"]], ["granularidade / grupo 8", ["cd8", "grupo 8", "baixa qualidade", "granular", "malat1"]], ["próximo passo", ["proximo passo", "melhorar", "dupleto", "silhueta", "futuro"]]],
      model: "Os nomes são sugestões automáticas e precisam de confirmação biológica; as T CD8 ficam como T porque os marcadores são amplos; o grupo 8 parece de baixa qualidade; e é um doador só. Os próximos passos são marcadores finos, detecção de dupletos e amostras maiores." },
    { q: "Onde essa experiência se aplica fora da biologia?",
      pts: [["agrupamento não supervisionado", ["nao supervisionado", "agrupamento", "cluster", "segment"]], ["alta dimensão", ["alta dimens", "muitas variaveis", "pca", "dimens"]], ["exemplo de negócio", ["cliente", "fraude", "comportamento", "mercado", "usuario", "rede social"]]],
      model: "É agrupamento não supervisionado em dado de alta dimensão. A mesma abordagem, reduzir dimensões, montar um grafo de semelhança e achar comunidades, serve para segmentar clientes, detectar comunidades em redes ou agrupar padrões de uso." },
  ];

  const SCRIPT = [
    { t: 15, screen: "Slide 1 · título e mapa colorido", text: "Uma gota de sangue tem dezenas de tipos de células imunes. A pergunta é: dá para descobrir quais são olhando só para os genes que cada célula usa, sem dizer ao computador o que procurar? Esse é o Cell-Atlas." },
    { t: 20, screen: "Slide 2 · 2.700 células × 32.738 genes", text: "O dado vem de sequenciamento de RNA de célula única: 2.700 células, e para cada uma, a atividade de mais de 32 mil genes. São quase 90 milhões de números, e nenhum rótulo dizendo que célula é qual." },
    { t: 30, screen: "Slide 3 · pipeline em 5 etapas", text: "Construí um pipeline em cinco etapas. Primeiro, controle de qualidade: descarto células danificadas e ficam 2.638. Depois normalizo, seleciono os 2.000 genes mais informativos e comprimo tudo em 10 componentes principais. Em seguida, ligo cada célula às 15 mais parecidas, formando uma rede, e o algoritmo Leiden encontra as comunidades nessa rede." },
    { t: 20, screen: "Slide 4 · comparação de resoluções", text: "O Leiden tem um botão de zoom, a resolução. Em 0,2 vejo 6 grupos, as grandes famílias. Em 1,0, 13 grupos, já com subtipos. Escolhi 0,6, com 10 grupos: detalhe suficiente sem fragmentar populações." },
    { t: 30, screen: "Slide 5 · marcadores e tipos celulares", text: "Agora a parte que convence. Para cada grupo, o programa mede genes-marcadores clássicos da imunologia e sugere um nome. Ele reencontrou células T, B, NK, dois tipos de monócitos, células dendríticas e até 14 plaquetas, meio por cento da amostra. É o mesmo resultado da análise de referência da área." },
    { t: 30, screen: "Slide 6 · terminal e testes", text: "Por trás disso há engenharia: um pacote Python instalável, uma linha de comando, parâmetros por arquivo, semente fixa para o resultado ser sempre o mesmo e testes automatizados. Qualquer pessoa clona, roda um comando e obtém exatamente estas figuras." },
    { t: 20, screen: "Slide 7 · o que aprendi e link", text: "O que levo daqui: transformar um dado enorme e sem rótulos em uma resposta que um especialista reconhece, com código que outra pessoa consegue reproduzir. O código está no GitHub. Obrigado." },
  ];

  /* ======================= Utilities ======================= */
  const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  const fmt = (sec) => `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;
  const store = {
    get(k) { try { return sessionStorage.getItem(k) ?? localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v, persist) {
      try {
        sessionStorage.setItem(k, v);
        if (persist) localStorage.setItem(k, v); else localStorage.removeItem(k);
      } catch (e) { /* storage blocked */ }
    },
    del(k) { try { sessionStorage.removeItem(k); localStorage.removeItem(k); } catch (e) { /* ignore */ } },
  };

  /* ======================= Speech output ======================= */
  const synth = window.speechSynthesis;
  const voiceSel = $("opt-voice");
  let voices = [];
  function loadVoices() {
    if (!synth) return;
    voices = synth.getVoices().filter((v) => /^pt/i.test(v.lang));
    const saved = store.get("cellatlas-voice");
    voiceSel.replaceChildren(new Option("Padrão do sistema", ""));
    voices.sort((a, b) => (/pt-BR/i.test(b.lang) - /pt-BR/i.test(a.lang)) || (/natural|online|google/i.test(b.name) - /natural|online|google/i.test(a.name)));
    voices.forEach((v) => voiceSel.add(new Option(`${v.name} (${v.lang})`, v.name)));
    if (saved && voices.some((v) => v.name === saved)) voiceSel.value = saved;
    else if (voices[0]) voiceSel.value = voices[0].name;
  }
  if (synth) { loadVoices(); synth.addEventListener?.("voiceschanged", loadVoices); }
  voiceSel.addEventListener("change", () => store.set("cellatlas-voice", voiceSel.value, true));

  function speak(text, force) {
    if (!synth || (!force && !$("opt-speak").checked)) return;
    synth.cancel();
    const v = voices.find((x) => x.name === voiceSel.value);
    (text.match(/[^.!?]+[.!?]*\s*/g) || [text]).forEach((part) => {
      const u = new SpeechSynthesisUtterance(part.trim());
      u.lang = "pt-BR"; if (v) u.voice = v; u.rate = Number($("opt-rate").value);
      synth.speak(u);
    });
  }
  const hush = () => { try { synth && synth.cancel(); } catch (e) { /* ignore */ } };
  $("opt-stop").addEventListener("click", hush);
  if (!synth) { $("opt-speak").checked = false; $("opt-speak").disabled = true; }

  /* ======================= Speech input ======================= */
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const notice = $("mic-notice");
  const TIP = "Microfone indisponível neste navegador ou bloqueado. Use Chrome ou Edge, permita o microfone no cadeado da barra de endereço, ou dite com Windows + H na caixa de texto.";
  function showNotice(t) { notice.textContent = t; notice.hidden = !t; }

  /** Binds a mic button to a textarea. onDone(text, seconds) fires when listening ends. */
  function bindMic(btn, area, { continuous = false, onDone } = {}) {
    let rec = null, on = false, t0 = 0;
    const stop = () => { if (rec && on) { try { rec.stop(); } catch (e) { /* ignore */ } } };
    btn.addEventListener("click", () => {
      if (on) { stop(); return; }
      if (!SR) { showNotice(TIP); area.focus(); return; }
      hush();
      rec = new SR(); rec.lang = "pt-BR"; rec.interimResults = true; rec.continuous = continuous;
      const base = area.value ? area.value.trim() + " " : "";
      let finals = "";
      rec.onresult = (e) => {
        let interim = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const r = e.results[i];
          if (r.isFinal) finals += r[0].transcript + " "; else interim += r[0].transcript;
        }
        area.value = (base + finals + interim).trim();
      };
      rec.onerror = (e) => {
        if (["not-allowed", "service-not-allowed", "audio-capture"].includes(e.error)) showNotice(TIP);
        else if (e.error === "network") showNotice("O reconhecimento de voz do navegador precisa de internet. Verifique a conexão ou digite.");
      };
      rec.onend = () => {
        on = false; btn.setAttribute("aria-pressed", "false");
        const secs = (performance.now() - t0) / 1000;
        if (onDone) onDone(area.value.trim(), secs);
      };
      try { rec.start(); on = true; t0 = performance.now(); btn.setAttribute("aria-pressed", "true"); showNotice(""); }
      catch (e) { showNotice(TIP); }
    });
    return { stop, isOn: () => on };
  }

  /* ======================= Claude (optional) ======================= */
  const keyInput = $("opt-key"), modelInput = $("opt-model"), remember = $("opt-remember"), cStatus = $("claude-status");
  keyInput.value = store.get("cellatlas-key") || "";
  modelInput.value = store.get("cellatlas-model") || modelInput.value;
  remember.checked = (() => { try { return !!localStorage.getItem("cellatlas-key"); } catch (e) { return false; } })();
  const saveKey = () => {
    const k = keyInput.value.trim();
    if (k) store.set("cellatlas-key", k, remember.checked); else store.del("cellatlas-key");
    store.set("cellatlas-model", modelInput.value.trim() || "claude-sonnet-4-5", true);
    refreshClaude();
  };
  keyInput.addEventListener("change", saveKey); modelInput.addEventListener("change", saveKey); remember.addEventListener("change", saveKey);
  $("opt-forget").addEventListener("click", () => { keyInput.value = ""; store.del("cellatlas-key"); refreshClaude(); cStatus.textContent = "Chave apagada deste navegador."; });
  const hasClaude = () => !!keyInput.value.trim();
  function refreshClaude() {
    $("int-claude").hidden = !hasClaude();
    cStatus.textContent = hasClaude() ? "Claude ativo para perguntas livres e feedback." : "";
  }

  async function askClaude(system, messages, maxTokens = 600) {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": keyInput.value.trim(),
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
      },
      body: JSON.stringify({ model: modelInput.value.trim() || "claude-sonnet-4-5", max_tokens: maxTokens, system, messages }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.error?.message || `HTTP ${res.status}`;
      throw new Error(res.status === 401 ? "Chave inválida." : res.status === 404 ? `Modelo não encontrado: ${msg}` : msg);
    }
    return (data.content || []).filter((b) => b.type === "text").map((b) => b.text).join("").trim();
  }

  /* ======================= Modes ======================= */
  const tabs = ["ask", "int", "reh"];
  function setMode(m) {
    hush();
    tabs.forEach((t) => {
      $(`m-${t}`).setAttribute("aria-selected", String(t === m));
      $(`p-${t}`).hidden = t !== m;
    });
    try { history.replaceState(null, "", `#${m === "ask" ? "perguntar" : m === "int" ? "entrevista" : "ensaio"}`); } catch (e) { /* ignore */ }
  }
  tabs.forEach((t) => $(`m-${t}`).addEventListener("click", () => setMode(t)));
  const HASHES = { "#entrevista": "int", "#ensaio": "reh", "#perguntar": "ask" };
  const applyHash = () => { const m = HASHES[location.hash]; if (m) setMode(m); };
  window.addEventListener("hashchange", applyHash);
  applyHash();

  /* ---------- Perguntar ---------- */
  const log = $("ask-log"), askInput = $("ask-input");
  let turns = [], busy = false;
  function addMsg(who, text, src) {
    const d = document.createElement("div"); d.className = `msg ${who}`;
    const w = document.createElement("span"); w.className = "who"; w.textContent = who === "you" ? "Você" : "Cell-Atlas";
    const t = document.createElement("span"); t.textContent = text;
    d.append(w, t);
    if (who === "ai") {
      if (src) { const s = document.createElement("span"); s.className = "src"; s.textContent = src; d.append(s); }
      const r = document.createElement("button"); r.type = "button"; r.className = "replay"; r.textContent = "Ouvir de novo";
      r.addEventListener("click", () => speak(t.textContent, true)); d.append(r);
    }
    log.append(d); log.scrollTop = log.scrollHeight;
    return t;
  }
  function offline(q) {
    const s = norm(q); let best = null, score = 0;
    for (const f of FAQ) {
      const h = f.k.reduce((n, k) => n + (s.includes(norm(k)) ? 1 : 0), 0);
      if (h > score) { score = h; best = f; }
    }
    return best ? best.a : "Ainda não tenho uma resposta pronta para isso. Tente uma das perguntas sugeridas, ou ative o Claude no painel lateral para perguntas livres.";
  }
  async function ask(text) {
    text = (text || "").trim(); if (!text || busy) return;
    askInput.value = ""; addMsg("you", text);
    busy = true; $("ask-send").disabled = true;
    if (hasClaude()) {
      const out = addMsg("ai", "Pensando…", "Claude");
      turns.push({ role: "user", content: text }); turns = turns.slice(-12);
      if (turns[0].role !== "user") turns.shift();
      try {
        const a = await askClaude(ASK_SYSTEM, turns, 400);
        out.textContent = a; turns.push({ role: "assistant", content: a }); speak(a);
      } catch (e) {
        turns.pop();
        const a = offline(text);
        out.textContent = a; out.nextSibling.textContent = `Resposta pronta (Claude falhou: ${e.message})`; speak(a);
      }
    } else {
      const a = offline(text); addMsg("ai", a, "Resposta pronta"); speak(a);
    }
    busy = false; $("ask-send").disabled = false;
  }
  $("ask-send").addEventListener("click", () => ask(askInput.value));
  askInput.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(askInput.value); } });
  $("ask-chips").replaceChildren(...ASK_CHIPS.map((c) => {
    const b = document.createElement("button"); b.type = "button"; b.textContent = c; b.addEventListener("click", () => ask(c)); return b;
  }));
  bindMic($("ask-mic"), askInput, { onDone: (t) => { if (t) ask(t); } });
  addMsg("ai", "Oi! Pergunte qualquer coisa sobre os resultados ou sobre como apresentar o vídeo. Toque no microfone ou escolha uma pergunta abaixo.", "Cell-Atlas");

  /* ---------- Entrevista ---------- */
  let qi = -1, scores = [], answerSecs = 0, typedStart = 0;
  const intInput = $("int-input");
  const intMic = bindMic($("int-mic"), intInput, { continuous: true, onDone: (_t, s) => { answerSecs += s; } });
  intInput.addEventListener("input", () => { if (!typedStart) typedStart = performance.now(); });

  function loadQuestion(i) {
    qi = i; answerSecs = 0; typedStart = 0;
    const item = INTERVIEW[qi];
    $("int-progress").textContent = `Pergunta ${qi + 1} de ${INTERVIEW.length}`;
    $("int-q").textContent = item.q;
    $("int-feedback").hidden = true; $("int-model-text").hidden = true; $("int-ai").hidden = true;
    intInput.value = ""; intInput.disabled = false; $("int-mic").disabled = false; $("int-submit").disabled = false; $("int-repeat").disabled = false;
    $("int-start").textContent = "Recomeçar";
    speak(item.q, true);
  }
  $("int-start").addEventListener("click", () => { scores = []; $("int-score-total").textContent = "Pontuação: —"; loadQuestion(0); });
  $("int-repeat").addEventListener("click", () => { if (qi >= 0) speak(INTERVIEW[qi].q, true); });

  function evaluate() {
    if (qi < 0) return;
    if (intMic.isOn()) intMic.stop();
    const ans = intInput.value.trim();
    if (!ans) { intInput.focus(); return; }
    const item = INTERVIEW[qi], s = norm(ans);
    const hits = item.pts.map(([label, keys]) => ({ label, hit: keys.some((k) => s.includes(norm(k))) }));
    const got = hits.filter((h) => h.hit).length;
    const pct = Math.round((got / hits.length) * 100);
    scores[qi] = pct;
    const words = ans.split(/\s+/).filter(Boolean).length;
    let secs = answerSecs || (typedStart ? (performance.now() - typedStart) / 1000 : 0);
    const spoken = answerSecs > 0;
    const numbers = (ans.match(/\d/g) || []).length > 0;

    $("int-fb-title").textContent = `${got} de ${hits.length} pontos-chave (${pct}%)`;
    $("int-points").replaceChildren(...hits.map((h) => { const li = document.createElement("li"); li.className = h.hit ? "hit" : "miss"; li.textContent = h.label; return li; }));
    const tips = [];
    tips.push(`${words} palavras`);
    if (spoken) tips.push(`${Math.round(secs)} s falando${secs < 15 ? " (curto: desenvolva mais)" : secs > 50 ? " (longo: corte para 45 s)" : " (bom ritmo)"}`);
    else if (words < 35) tips.push("resposta curta: mire em 50 a 100 palavras");
    else if (words > 130) tips.push("resposta longa: mire em até 100 palavras");
    if (!numbers) tips.push("cite um número do projeto (2.638 células, 10 grupos, 7 tipos)");
    $("int-meta").textContent = tips.join(" · ");
    $("int-model-text").textContent = item.model;
    $("int-feedback").hidden = false;
    const valid = scores.filter((x) => typeof x === "number");
    $("int-score-total").textContent = `Pontuação: ${Math.round(valid.reduce((a, b) => a + b, 0) / valid.length)}%`;
    $("int-next").textContent = qi + 1 < INTERVIEW.length ? "Próxima pergunta" : "Ver resultado final";
    speak(got === hits.length ? "Muito bem, você cobriu todos os pontos." : `Você cobriu ${got} de ${hits.length} pontos. Faltou: ${hits.filter((h) => !h.hit).map((h) => h.label).join("; ")}.`);
  }
  $("int-submit").addEventListener("click", evaluate);
  $("int-model").addEventListener("click", () => { $("int-model-text").hidden = false; speak(INTERVIEW[qi].model, true); });
  $("int-next").addEventListener("click", () => {
    if (qi + 1 < INTERVIEW.length) { loadQuestion(qi + 1); return; }
    const avg = Math.round(scores.reduce((a, b) => a + (b || 0), 0) / INTERVIEW.length);
    $("int-q").textContent = `Fim da entrevista. Média: ${avg}%. ${avg >= 75 ? "Pronto para gravar." : "Revise as respostas-modelo das perguntas com menor pontuação e repita."}`;
    $("int-feedback").hidden = true; intInput.disabled = true; $("int-mic").disabled = true; $("int-submit").disabled = true;
    speak($("int-q").textContent, true);
  });
  $("int-claude").addEventListener("click", async () => {
    const box = $("int-ai"); box.hidden = false; box.textContent = "Pensando…";
    const item = INTERVIEW[qi];
    try {
      const a = await askClaude(
        `Você é um recrutador técnico de dados avaliando o autor do Cell-Atlas. Dê um retorno em português do Brasil, em até 80 palavras, linguagem falada, sem markdown: o que funcionou, o que faltou e uma frase melhorada que ele poderia dizer. Use só estes fatos:\n${KB}`,
        [{ role: "user", content: `Pergunta: ${item.q}\nResposta do candidato: ${intInput.value.trim()}` }], 350);
      box.textContent = a; speak(a);
    } catch (e) { box.textContent = `Não foi possível consultar o Claude: ${e.message}`; }
  });

  /* ---------- Ensaio ---------- */
  const TOTAL = SCRIPT.reduce((a, s) => a + s.t, 0);
  $("reh-target").textContent = `Meta total: ${fmt(TOTAL)}`;
  let si = 0, running = false, t0 = 0, sceneStart = 0, times = [], timer = null;
  function showScene() {
    const s = SCRIPT[si];
    $("reh-scene").textContent = `Cena ${si + 1} de ${SCRIPT.length} · meta ${s.t} s`;
    $("reh-screen").textContent = s.screen; $("reh-text").textContent = s.text;
  }
  function tick() {
    const now = performance.now();
    $("reh-clock").textContent = fmt((now - t0) / 1000);
    const el = (now - sceneStart) / 1000, lim = SCRIPT[si].t;
    $("reh-bar").style.width = `${Math.min(100, (el / lim) * 100)}%`;
    $("reh-bar").parentElement.classList.toggle("over", el > lim);
  }
  function finish() {
    running = false; clearInterval(timer); $("reh-next").disabled = true; $("reh-go").textContent = "Ensaiar de novo";
    const total = times.reduce((a, b) => a + b, 0);
    $("reh-rows").replaceChildren(...SCRIPT.map((s, i) => {
      const tr = document.createElement("tr"), d = times[i] - s.t;
      const verdict = Math.abs(d) <= 3 ? ["ok", "no tempo"] : d > 0 ? ["late", `${Math.round(d)} s acima`] : ["ok", `${Math.round(-d)} s abaixo`];
      [`${i + 1}. ${s.screen.split("·")[1]?.trim() || s.screen}`, `${s.t} s`, `${Math.round(times[i])} s`].forEach((v, j) => {
        const td = document.createElement("td"); td.textContent = v; if (j) td.className = "num"; tr.append(td);
      });
      const td = document.createElement("td"); td.textContent = verdict[1]; td.className = verdict[0]; tr.append(td);
      return tr;
    }));
    $("reh-summary").textContent = `Total ${fmt(total)} (meta ${fmt(TOTAL)}, limite 2:50) · ${total <= 170 ? "dentro do tempo" : "acima do tempo: enxugue as cenas em laranja"}`;
    $("reh-result").hidden = false;
  }
  function next() {
    if (!running) return;
    const now = performance.now();
    times[si] = (now - sceneStart) / 1000;
    if (si + 1 >= SCRIPT.length) { finish(); return; }
    si += 1; sceneStart = now; showScene();
  }
  $("reh-go").addEventListener("click", () => {
    hush(); si = 0; times = []; running = true; t0 = sceneStart = performance.now();
    $("reh-result").hidden = true; $("reh-next").disabled = false; $("reh-go").textContent = "Reiniciar";
    showScene(); clearInterval(timer); timer = setInterval(tick, 200);
  });
  $("reh-next").addEventListener("click", next);
  $("reh-reset").addEventListener("click", () => { running = false; clearInterval(timer); si = 0; times = []; $("reh-clock").textContent = "0:00"; $("reh-bar").style.width = "0"; $("reh-next").disabled = true; $("reh-result").hidden = true; $("reh-go").textContent = "Iniciar ensaio"; showScene(); });
  $("reh-listen").addEventListener("click", () => speak(SCRIPT[si].text, true));
  document.addEventListener("keydown", (e) => {
    if ($("p-reh").hidden || e.target.closest("textarea, input, select")) return;
    if (e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); next(); }
  });
  showScene();
  refreshClaude();
})();
