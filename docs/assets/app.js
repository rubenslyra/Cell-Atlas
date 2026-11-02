/* Cell-Atlas — GitHub Pages interactions. Vanilla JS, no dependencies. */
(() => {
  "use strict";

  /* ---------- theme toggle (shared by every page) ---------- */
  const root = document.documentElement;
  const toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const current = root.getAttribute("data-theme")
        || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      const next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("cellatlas-theme", next); } catch (e) { /* ignore */ }
    });
  }

  /* ---------- resolution explorer: real pipeline outputs ---------- */
  const RES = {
    "02": { label: "0,2", count: 6, alt: "UMAP com os 6 grupos da resolução 0,2.",
      desc: "Visão ampla: as grandes famílias. Todos os monócitos formam um só grupo, e NK dividem um grupo com T CD8+." },
    "04": { label: "0,4", count: 9, alt: "UMAP com os 9 grupos da resolução 0,4.",
      desc: "Monócitos se separam em clássicos e não clássicos; NK ganham grupo próprio." },
    "06": { label: "0,6", count: 10, alt: "UMAP com os 10 grupos encontrados pelo Leiden na resolução 0,6.",
      desc: "Resolução usada na anotação: cada tipo imune principal já aparece separado, sem fragmentar populações homogêneas." },
    "10": { label: "1,0", count: 13, alt: "UMAP com os 13 grupos da resolução 1,0.",
      desc: "Visão detalhada: subdivide as células T em vários grupos. Mais detalhe, mais risco de dividir uma população única." },
  };
  const img = document.getElementById("res-img");
  const count = document.getElementById("res-count");
  const desc = document.getElementById("res-desc");
  const rows = document.querySelectorAll(".bar-row");
  if (img && count && desc) {
    // Preload so switching never flashes an empty frame.
    Object.keys(RES).forEach((k) => { const i = new Image(); i.src = `assets/img/res_${k}.png`; });
    document.querySelectorAll('input[name="res"]').forEach((radio) => {
      radio.addEventListener("change", () => {
        const r = RES[radio.value];
        if (!r) return;
        img.src = `assets/img/res_${radio.value}.png`;
        img.alt = r.alt;
        count.textContent = String(r.count);
        desc.textContent = `Resolução ${r.label}: ${r.desc}`;
        rows.forEach((row) => row.classList.toggle("is-active", row.dataset.res === radio.value));
      });
    });
  }

  /* ---------- OS tabs for the install commands ---------- */
  const tabs = document.querySelectorAll('[role="tab"]');
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => {
        const selected = t === tab;
        t.setAttribute("aria-selected", String(selected));
        const panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) panel.hidden = !selected;
      });
    });
  });

  /* ---------- copy buttons ---------- */
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const panel = document.getElementById(btn.dataset.copy);
      const code = panel && panel.querySelector("code");
      if (!code) return;
      const text = Array.from(code.childNodes)
        .filter((n) => !(n.nodeType === 1 && n.classList.contains("p")))
        .map((n) => n.textContent).join("");
      try {
        await navigator.clipboard.writeText(text.trim());
        btn.textContent = "Copiado";
      } catch (e) {
        const range = document.createRange();
        range.selectNodeContents(code);
        const sel = getSelection(); sel.removeAllRanges(); sel.addRange(range);
        btn.textContent = "Selecionado";
      }
      setTimeout(() => { btn.textContent = "Copiar"; }, 1600);
    });
  });
})();
