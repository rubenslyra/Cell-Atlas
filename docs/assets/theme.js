/* Applies the saved theme before first paint (loaded in <head>, no defer). */
(function () {
  try {
    var saved = localStorage.getItem("cellatlas-theme");
    if (saved === "light" || saved === "dark") document.documentElement.setAttribute("data-theme", saved);
  } catch (e) { /* storage unavailable: follow the OS */ }
})();
