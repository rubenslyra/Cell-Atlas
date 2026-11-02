/* Slide viewer: keyboard/touch navigation, fit-to-viewport scaling, speaker notes, fullscreen. */
(() => {
  "use strict";
  const stage = document.getElementById("stage");
  const viewport = document.getElementById("viewport");
  const slides = Array.from(stage.querySelectorAll(".slide"));
  const counter = document.getElementById("counter");
  const notes = document.getElementById("notes");
  const notesText = document.getElementById("notes-text");
  const notesBtn = document.getElementById("notes-btn");
  let i = 0;

  function fit() {
    const w = viewport.clientWidth, h = viewport.clientHeight;
    const s = Math.min(w / 1920, h / 1080) * 0.96;
    stage.style.transform = `scale(${s}) translate(-50%, -50%)`;
  }

  function show(n) {
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((el, k) => { el.hidden = k !== i; });
    counter.textContent = `${i + 1} / ${slides.length}`;
    const aside = slides[i].querySelector("aside");
    notesText.textContent = aside ? aside.textContent.trim() : "";
    try { history.replaceState(null, "", `#slide-${i + 1}`); } catch (e) { /* ignore */ }
  }

  const go = (d) => show(i + d);
  document.getElementById("prev").addEventListener("click", () => go(-1));
  document.getElementById("next").addEventListener("click", () => go(1));
  document.getElementById("zone-prev").addEventListener("click", () => go(-1));
  document.getElementById("zone-next").addEventListener("click", () => go(1));

  function toggleNotes() {
    notes.hidden = !notes.hidden;
    notesBtn.setAttribute("aria-pressed", String(!notes.hidden));
    requestAnimationFrame(fit);
  }
  notesBtn.addEventListener("click", toggleNotes);

  function toggleFull() {
    if (document.fullscreenElement) document.exitFullscreen?.();
    else document.body.requestFullscreen?.().catch(() => {});
  }
  document.getElementById("full-btn").addEventListener("click", toggleFull);

  document.addEventListener("keydown", (e) => {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    if (["ArrowRight", "PageDown", " "].includes(e.key)) { e.preventDefault(); go(1); }
    else if (["ArrowLeft", "PageUp"].includes(e.key)) { e.preventDefault(); go(-1); }
    else if (e.key === "Home") show(0);
    else if (e.key === "End") show(slides.length - 1);
    else if (e.key.toLowerCase() === "n") toggleNotes();
    else if (e.key.toLowerCase() === "f") toggleFull();
  });

  let x0 = null;
  viewport.addEventListener("touchstart", (e) => { x0 = e.touches[0].clientX; }, { passive: true });
  viewport.addEventListener("touchend", (e) => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0; x0 = null;
    if (Math.abs(dx) > 40) go(dx < 0 ? 1 : -1);
  });

  new ResizeObserver(fit).observe(viewport);
  document.addEventListener("fullscreenchange", () => requestAnimationFrame(fit));
  const m = /^#slide-(\d+)$/.exec(location.hash);
  show(m ? Number(m[1]) - 1 : 0);
  fit();
})();
