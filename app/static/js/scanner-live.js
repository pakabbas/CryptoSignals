(function () {
  const countdownEls = document.querySelectorAll("[data-next-close]");
  if (!countdownEls.length) return;

  function tick() {
    const now = Date.now();
    countdownEls.forEach((el) => {
      const iso = el.getAttribute("data-next-close");
      if (!iso) return;
      const target = Date.parse(iso);
      let diff = Math.max(0, Math.floor((target - now) / 1000));
      const h = Math.floor(diff / 3600);
      diff %= 3600;
      const m = Math.floor(diff / 60);
      const s = diff % 60;
      const parts = [];
      if (h) parts.push(String(h).padStart(2, "0") + "h");
      parts.push(String(m).padStart(2, "0") + "m");
      parts.push(String(s).padStart(2, "0") + "s");
      el.textContent = parts.join(" ");
    });
  }

  tick();
  setInterval(tick, 1000);
})();
