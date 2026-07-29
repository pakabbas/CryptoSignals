(() => {
  const root = document.getElementById("strategy-builder-root");
  const form = document.getElementById("strategy-form");
  if (!root || !form) return;

  const indicators = JSON.parse(root.dataset.indicators || "[]");
  const ruleTypes = JSON.parse(root.dataset.ruleTypes || "[]");
  const operators = JSON.parse(root.dataset.operators || "[]");
  const logicOps = JSON.parse(root.dataset.logicOps || "[]");
  let definition = JSON.parse(root.dataset.initial || "{}");

  if (!definition.version) {
    definition = { version: 1, long: { logic: "AND", rules: [] }, short: { logic: "AND", rules: [] } };
  }

  const hidden = document.getElementById("definition_json");
  const preview = document.getElementById("definition-preview");

  function ensureSide(side) {
    if (!definition[side]) definition[side] = { logic: "AND", rules: [] };
    if (!definition[side].rules) definition[side].rules = [];
  }

  function syncHidden() {
    hidden.value = JSON.stringify(definition);
    if (preview) preview.textContent = JSON.stringify(definition, null, 2);
  }

  function indicatorOptions(selected) {
    return indicators
      .map((ind) => `<option value="${ind.key}" ${ind.key === selected ? "selected" : ""}>${ind.label}</option>`)
      .join("");
  }

  function operatorOptions(selected) {
    return operators
      .map((op) => `<option value="${op.value}" ${op.value === selected ? "selected" : ""}>${op.label}</option>`)
      .join("");
  }

  function ruleTypeOptions(selected) {
    return ruleTypes
      .map((rt) => `<option value="${rt.key}" ${rt.key === selected ? "selected" : ""}>${rt.label}</option>`)
      .join("");
  }

  function renderRule(side, rule, index) {
    const wrap = document.createElement("div");
    wrap.className = "border rounded p-3 mb-2";
    wrap.dataset.side = side;
    wrap.dataset.index = String(index);

    const type = rule.type || "indicator_compare";
    wrap.innerHTML = `
      <div class="d-flex justify-content-between align-items-start mb-2">
        <strong>Rule ${index + 1}</strong>
        <button type="button" class="btn btn-sm btn-outline-danger" data-remove-rule>Remove</button>
      </div>
      <div class="row g-2">
        <div class="col-md-4">
          <label class="form-label small">Type</label>
          <select class="form-select form-select-sm" data-field="type">${ruleTypeOptions(type)}</select>
        </div>
        <div class="col-md-4">
          <label class="form-label small">NOT</label>
          <div class="form-check mt-2">
            <input class="form-check-input" type="checkbox" data-field="negate" ${rule.negate ? "checked" : ""}>
            <label class="form-check-label small">Invert rule</label>
          </div>
        </div>
      </div>
      <div data-fields="compare" class="mt-2 ${type === "indicator_compare" ? "" : "d-none"}">
        <div class="row g-2">
          <div class="col-md-3">
            <label class="form-label small">Left</label>
            <select class="form-select form-select-sm" data-left-name>${indicatorOptions(rule.left?.name || "EMA")}</select>
          </div>
          <div class="col-md-2">
            <label class="form-label small">Length</label>
            <input type="number" class="form-control form-control-sm" data-left-length value="${rule.left?.length ?? 50}">
          </div>
          <div class="col-md-2">
            <label class="form-label small">Operator</label>
            <select class="form-select form-select-sm" data-operator>${operatorOptions(rule.operator || "gt")}</select>
          </div>
          <div class="col-md-3">
            <label class="form-label small">Right type</label>
            <select class="form-select form-select-sm" data-right-kind>
              <option value="indicator" ${rule.right?.name ? "selected" : ""}>Indicator</option>
              <option value="value" ${rule.right?.value !== undefined ? "selected" : ""}>Fixed value</option>
            </select>
          </div>
          <div class="col-md-2" data-right-indicator>
            <label class="form-label small">Right ind.</label>
            <select class="form-select form-select-sm" data-right-name>${indicatorOptions(rule.right?.name || "EMA")}</select>
          </div>
          <div class="col-md-2" data-right-length-wrap>
            <label class="form-label small">Length</label>
            <input type="number" class="form-control form-control-sm" data-right-length value="${rule.right?.length ?? 200}">
          </div>
          <div class="col-md-2 d-none" data-right-value-wrap>
            <label class="form-label small">Value</label>
            <input type="number" step="any" class="form-control form-control-sm" data-right-value value="${rule.right?.value ?? 55}">
          </div>
        </div>
      </div>
      <div data-fields="macd" class="mt-2 ${type === "macd_cross" ? "" : "d-none"}">
        <label class="form-label small">Direction</label>
        <select class="form-select form-select-sm" data-macd-direction>
          <option value="up" ${rule.direction === "up" ? "selected" : ""}>Cross up</option>
          <option value="down" ${rule.direction === "down" ? "selected" : ""}>Cross down</option>
        </select>
      </div>
      <div data-fields="bb" class="mt-2 ${type === "price_at_bb" ? "" : "d-none"}">
        <label class="form-label small">Band</label>
        <select class="form-select form-select-sm" data-bb-band>
          <option value="lower" ${rule.band === "lower" ? "selected" : ""}>Lower band</option>
          <option value="upper" ${rule.band === "upper" ? "selected" : ""}>Upper band</option>
        </select>
      </div>
    `;

    wrap.querySelector("[data-remove-rule]")?.addEventListener("click", () => {
      ensureSide(side);
      definition[side].rules.splice(index, 1);
      renderAll();
    });

    wrap.querySelectorAll("input, select").forEach((el) => {
      el.addEventListener("change", () => readFromDom());
      el.addEventListener("input", () => readFromDom());
    });

    wrap.querySelector('[data-field="type"]')?.addEventListener("change", () => {
      readFromDom();
      renderAll();
    });

    toggleRightKind(wrap);
    wrap.querySelector("[data-right-kind]")?.addEventListener("change", () => toggleRightKind(wrap));

    return wrap;
  }

  function toggleRightKind(wrap) {
    const kind = wrap.querySelector("[data-right-kind]")?.value || "indicator";
    wrap.querySelector("[data-right-indicator]")?.classList.toggle("d-none", kind !== "indicator");
    wrap.querySelector("[data-right-length-wrap]")?.classList.toggle("d-none", kind !== "indicator");
    wrap.querySelector("[data-right-value-wrap]")?.classList.toggle("d-none", kind !== "value");
  }

  function readRuleFromWrap(wrap) {
    const type = wrap.querySelector('[data-field="type"]')?.value || "indicator_compare";
    const negate = wrap.querySelector('[data-field="negate"]')?.checked || false;
    const rule = { type, negate: negate || undefined };

    if (type === "indicator_compare") {
      const leftName = wrap.querySelector("[data-left-name]")?.value || "EMA";
      const leftLength = Number(wrap.querySelector("[data-left-length]")?.value || 20);
      rule.operator = wrap.querySelector("[data-operator]")?.value || "gt";
      rule.left = leftName === "volume" ? { name: "volume" } : { name: leftName, length: leftLength };

      const kind = wrap.querySelector("[data-right-kind]")?.value || "indicator";
      if (kind === "value") {
        rule.right = { value: Number(wrap.querySelector("[data-right-value]")?.value || 0) };
      } else {
        const rightName = wrap.querySelector("[data-right-name]")?.value || "EMA";
        const rightLength = Number(wrap.querySelector("[data-right-length]")?.value || 20);
        if (rightName === "volume") {
          rule.right = { name: "volume" };
        } else if (rightName === "SMA") {
          rule.right = { name: "SMA", length: rightLength, source: "volume" };
        } else {
          rule.right = { name: rightName, length: rightLength };
        }
      }
    } else if (type === "macd_cross") {
      rule.direction = wrap.querySelector("[data-macd-direction]")?.value || "up";
    } else if (type === "price_at_bb") {
      rule.band = wrap.querySelector("[data-bb-band]")?.value || "lower";
    }
    return rule;
  }

  function readFromDom() {
    ["long", "short"].forEach((side) => {
      ensureSide(side);
      definition[side].logic = document.querySelector(`[data-logic="${side}"]`)?.value || "AND";
      const container = document.querySelector(`[data-rules="${side}"]`);
      if (!container) return;
      definition[side].rules = Array.from(container.children).map((child) => readRuleFromWrap(child));
    });
    syncHidden();
  }

  function renderAll() {
    ["long", "short"].forEach((side) => {
      ensureSide(side);
      const logicSelect = document.querySelector(`[data-logic="${side}"]`);
      if (logicSelect) logicSelect.value = definition[side].logic || "AND";
      const container = document.querySelector(`[data-rules="${side}"]`);
      if (!container) return;
      container.innerHTML = "";
      definition[side].rules.forEach((rule, index) => {
        container.appendChild(renderRule(side, rule, index));
      });
    });
    syncHidden();
  }

  document.querySelectorAll("[data-add-rule]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const side = btn.getAttribute("data-add-rule");
      ensureSide(side);
      definition[side].rules.push({
        type: "indicator_compare",
        operator: "gt",
        left: { name: "EMA", length: 50 },
        right: { name: "EMA", length: 200 },
      });
      renderAll();
    });
  });

  document.querySelectorAll("[data-logic]").forEach((el) => {
    el.addEventListener("change", () => readFromDom());
  });

  form.addEventListener("submit", () => readFromDom());

  renderAll();
})();
