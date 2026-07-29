(function () {
  function formatRelativeAgo(iso) {
    const t = Date.parse(iso);
    if (Number.isNaN(t)) return null;
    let sec = Math.floor((Date.now() - t) / 1000);
    if (sec < 0) sec = 0;
    if (sec < 60) {
      return sec + (sec === 1 ? " second ago" : " seconds ago");
    }
    const m = Math.floor(sec / 60);
    sec %= 60;
    if (m < 60) {
      if (sec === 0) {
        return m + (m === 1 ? " minute ago" : " minutes ago");
      }
      return m + "m " + sec + "s ago";
    }
    const h = Math.floor(m / 60);
    m %= 60;
    if (h < 24) {
      if (m === 0) return h + (h === 1 ? " hour ago" : " hours ago");
      return h + "h " + m + "m ago";
    }
    const d = Math.floor(h / 24);
    return d + (d === 1 ? " day ago" : " days ago");
  }

  function tickRelativeTimes() {
    document.querySelectorAll("[data-relative-time]").forEach((el) => {
      const iso = el.getAttribute("data-relative-time");
      if (!iso) {
        el.textContent = "Never";
        return;
      }
      const label = formatRelativeAgo(iso);
      el.textContent = label || "—";
    });
  }

  tickRelativeTimes();
  setInterval(tickRelativeTimes, 1000);
})();
