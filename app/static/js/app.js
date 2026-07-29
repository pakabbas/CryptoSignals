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

  function parseSortValue(raw, type) {
    if (raw == null) return "";
    const text = String(raw).trim();
    if (type === "number") {
      const n = Number(text.replace(/[%$,]/g, ""));
      return Number.isFinite(n) ? n : 0;
    }
    if (type === "date") {
      const t = Date.parse(text);
      return Number.isNaN(t) ? 0 : t;
    }
    return text.toLowerCase();
  }

  function initSortableTables() {
    document.querySelectorAll("table.sortable-table").forEach((table) => {
      const tbody = table.tBodies[0];
      if (!tbody) return;
      const headers = table.querySelectorAll("thead th[data-sort]");
      headers.forEach((th, colIndex) => {
        th.classList.add("sortable-th");
        th.setAttribute("role", "button");
        th.tabIndex = 0;
        const runSort = () => {
          const type = th.getAttribute("data-sort") || "text";
          const current = th.getAttribute("data-dir") === "asc" ? "asc" : "desc";
          const next = current === "asc" ? "desc" : "asc";
          headers.forEach((h) => {
            h.removeAttribute("data-dir");
            h.classList.remove("sorted-asc", "sorted-desc");
          });
          th.setAttribute("data-dir", next);
          th.classList.add(next === "asc" ? "sorted-asc" : "sorted-desc");

          const rows = Array.from(tbody.querySelectorAll("tr")).filter(
            (row) => row.querySelectorAll("td").length > 1
          );
          rows.sort((a, b) => {
            const aCell = a.children[colIndex];
            const bCell = b.children[colIndex];
            const aVal = parseSortValue(
              aCell?.getAttribute("data-sort-value") ?? aCell?.textContent,
              type
            );
            const bVal = parseSortValue(
              bCell?.getAttribute("data-sort-value") ?? bCell?.textContent,
              type
            );
            if (aVal < bVal) return next === "asc" ? -1 : 1;
            if (aVal > bVal) return next === "asc" ? 1 : -1;
            return 0;
          });
          rows.forEach((row) => tbody.appendChild(row));
        };
        th.addEventListener("click", runSort);
        th.addEventListener("keydown", (ev) => {
          if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            runSort();
          }
        });
      });
    });
  }

  initSortableTables();
})();
