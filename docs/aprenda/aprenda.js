/* Quiz dos fundamentos — vanilla JS, speech synthesis optional. */
(() => {
  "use strict";
  const QUESTIONS = [
    { q: "O que define uma célula como PBMC?",
      o: ["Ter um núcleo único e arredondado e circular no sangue", "Ser qualquer célula vermelha do sangue", "Ter vários lóbulos no núcleo", "Ser produzida no timo"], a: 0,
      e: "PBMC são as células mononucleares do sangue periférico: linfócitos T, B e NK, monócitos e dendríticas. Hemácias não têm núcleo e granulócitos têm núcleo lobulado." },
    { q: "Por que o Cell-Atlas encontra 14 plaquetas se plaquetas não são PBMC?",
      o: ["Porque o algoritmo errou", "Porque algumas plaquetas contaminam a amostra durante a separação", "Porque plaquetas têm núcleo", "Porque o PBMC3k é de outro tecido"], a: 1,
      e: "Plaquetas são fragmentos de megacariócitos e grudam nos PBMC durante o isolamento. Reconhecê-las como grupo próprio mostra a sensibilidade do método." },
    { q: "Qual técnica separa os PBMC do resto do sangue?",
      o: ["PCR", "Centrifugação em gradiente de densidade (Ficoll)", "Sequenciamento", "UMAP"], a: 1,
      e: "Bøyum (1968): o sangue é centrifugado sobre Ficoll e os PBMC formam um anel na interface, separados de hemácias e granulócitos." },
    { q: "Qual é a função principal das células T CD8+?",
      o: ["Produzir anticorpos", "Coagular o sangue", "Matar células infectadas ou tumorais", "Transportar oxigênio"], a: 2,
      e: "As T CD8+ são citotóxicas. As T CD4+ coordenam a resposta e as células B produzem anticorpos." },
    { q: "O gene MS4A1 corresponde a qual proteína, alvo de qual remédio?",
      o: ["CD3, alvo da insulina", "CD20, alvo do rituximabe", "CD14, alvo da penicilina", "CD16, alvo do paracetamol"], a: 1,
      e: "MS4A1 codifica CD20, marcador de células B. O rituximabe é um anticorpo anti-CD20 usado em linfomas e doenças autoimunes." },
    { q: "Por que células NK e T CD8+ ficam vizinhas no UMAP?",
      o: ["Porque são o mesmo tipo de célula", "Porque compartilham genes de citotoxicidade como NKG7 e granzimas", "Porque o UMAP é aleatório", "Porque vêm do mesmo doador"], a: 1,
      e: "Ambas matam células-alvo usando perforina e granzimas, então expressam genes parecidos. É também onde o Cell-Atlas mais confunde: 12 NK foram rotuladas como T." },
    { q: "O que é o PBMC3k?",
      o: ["Um software de análise", "Cerca de 2.700 PBMC de um doador saudável, publicados pela 10x Genomics em 2016", "Um banco de pacientes com COVID-19", "Um tipo de célula imune"], a: 1,
      e: "É o conjunto de ensino padrão da área: pequeno, público e com resposta conhecida, usado nos tutoriais do Seurat e do Scanpy." },
    { q: "Num arquivo .h5ad, onde fica a coluna cell_type com o nome de cada célula?",
      o: ["Em X", "Em var", "Em obs", "Em obsp"], a: 2,
      e: "obs tem uma linha por célula (observação). var tem uma linha por gene. X é a matriz; obsp guarda o grafo de vizinhança." },
    { q: "Para que o Cell-Atlas guarda a matriz completa em .raw?",
      o: ["Para ocupar menos espaço", "Porque marcadores clássicos podem ficar fora dos 2.000 genes variáveis", "Para o UMAP ficar colorido", "Porque o HDF5 exige"], a: 1,
      e: "Genes como CD3E nem sempre estão entre os mais variáveis. Sem .raw eles sumiriam e a anotação falharia; há um teste automatizado para isso." },
    { q: "Qual afirmação sobre o UMAP está correta?",
      o: ["A distância entre ilhas distantes mede o quanto os tipos diferem", "O tamanho de cada ilha é a proporção de células", "Ele desenha a vizinhança; os grupos vêm do Leiden no grafo", "Ele é determinístico mesmo sem semente"], a: 2,
      e: "O UMAP é visualização. Distâncias globais e tamanhos de ilhas não são confiáveis, e outra semente gera outro desenho." },
    { q: "O que significa ARI = 0,96 entre o Cell-Atlas e os rótulos de especialistas?",
      o: ["96% das células são T", "As duas partições agrupam quase exatamente as mesmas células", "O método é 96% mais rápido", "Há 96 grupos"], a: 1,
      e: "O adjusted Rand index mede concordância de agrupamento independentemente dos nomes: 1 é idêntico, 0 é acaso." },
    { q: "Onde está a maior discordância entre o Cell-Atlas e os especialistas?",
      o: ["Células B", "Plaquetas", "49 monócitos CD14+ rotulados como FCGR3A+", "Células dendríticas"], a: 2,
      e: "Provavelmente monócitos intermediários, que expressam CD14 e CD16. Discordância localizada é uma pergunta científica, não um erro a esconder." },
  ];

  const $ = (id) => document.getElementById(id);
  const qEl = $("quiz-q"), opts = $("quiz-opts"), exp = $("quiz-exp"), next = $("quiz-next");
  if (!qEl) return;
  let i = 0, score = 0, done = false;

  const synth = window.speechSynthesis;
  function speak(text) {
    if (!synth) return;
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "pt-BR";
    const v = synth.getVoices().find((x) => /pt-BR/i.test(x.lang));
    if (v) u.voice = v;
    synth.speak(u);
  }
  if (!synth) $("quiz-listen").hidden = true;

  function render() {
    const item = QUESTIONS[i];
    $("quiz-progress").textContent = `Pergunta ${i + 1} de ${QUESTIONS.length}`;
    $("quiz-score").textContent = `Acertos: ${score}`;
    qEl.textContent = item.q;
    exp.hidden = true; next.hidden = true;
    opts.replaceChildren(...item.o.map((text, k) => {
      const b = document.createElement("button");
      b.type = "button"; b.textContent = text;
      b.addEventListener("click", () => choose(k));
      return b;
    }));
  }

  function choose(k) {
    const item = QUESTIONS[i];
    const buttons = Array.from(opts.children);
    buttons.forEach((b, j) => {
      b.disabled = true;
      if (j === item.a) b.classList.add("right");
      else if (j === k) b.classList.add("wrong");
    });
    const ok = k === item.a;
    if (ok) score += 1;
    $("quiz-score").textContent = `Acertos: ${score}`;
    exp.replaceChildren();
    const head = document.createElement("b");
    head.textContent = ok ? "Certo. " : "Ainda não. ";
    exp.append(head, document.createTextNode(item.e));
    exp.hidden = false;
    next.textContent = i + 1 < QUESTIONS.length ? "Próxima" : "Ver resultado";
    next.hidden = false;
    next.focus();
  }

  next.addEventListener("click", () => {
    if (done) { done = false; i = 0; score = 0; render(); return; }
    if (i + 1 < QUESTIONS.length) { i += 1; render(); return; }
    const pct = Math.round((score / QUESTIONS.length) * 100);
    qEl.textContent = `Resultado: ${score} de ${QUESTIONS.length} (${pct}%). ${pct >= 75 ? "Fundamentos firmes: passe para o modo Entrevista do treino." : "Releia as seções das questões erradas e tente de novo."}`;
    opts.replaceChildren(); exp.hidden = true;
    next.textContent = "Recomeçar";
    done = true;
    try { localStorage.setItem("cellatlas-quiz-fundamentos", String(pct)); } catch (e) { /* ignore */ }
  });

  $("quiz-listen").addEventListener("click", () => {
    const item = QUESTIONS[i];
    speak(`${item.q} Opções: ${item.o.map((o, k) => `${k + 1}, ${o}`).join(". ")}.`);
  });

  render();
})();
