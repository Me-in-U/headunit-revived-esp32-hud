(function exposeEditorPropertyActions(globalScope) {
  const INTEGER_FIELDS = new Set(["x", "y", "w", "h", "font_size", "active_font_size"]);
  const VALUE_RANGE_FIELDS = new Set(["min_value", "max_value", "tick_interval"]);
  const PALETTE_IDENTITY_FIELDS = new Set(["binding", "event_binding", "side_binding", "icon"]);

  function applyPropertyInput(state, element, key, rawValue, editor) {
    let value = rawValue;
    if (key === "id" && value && value !== element.id) {
      value = editor.uniqueId(state.layout, value, element.id);
      element.id = value;
      state.selectedId = value;
    } else if (INTEGER_FIELDS.has(key)) {
      if (value !== "") {
        element[key] = Number.parseInt(value, 10);
      }
    } else if (VALUE_RANGE_FIELDS.has(key)) {
      if (element.type === "value") {
        if (value === "") {
          delete element[key];
        } else {
          const number = Number.parseFloat(value);
          if (Number.isFinite(number)) {
            element[key] = Number.isInteger(number) ? Number.parseInt(value, 10) : number;
          }
        }
      }
    } else if (key === "fallback_bindings") {
      element[key] = value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    } else if (key === "gears") {
      element[key] = value
        .replace(/\//g, ",")
        .split(",")
        .map((item) => item.trim().toUpperCase())
        .filter(Boolean);
    } else if (key === "value_style") {
      if (element.type === "value") {
        element[key] = value;
        delete element.palette_key;
      }
    } else if (key === "gear_style") {
      if (element.type === "gear_indicator") {
        element[key] = value;
        delete element.palette_key;
      }
    } else if (editor.COLOR_KEYS.includes(key)) {
      if (value) {
        element[key] = value.toLowerCase();
      }
    } else {
      element[key] = value;
      if (PALETTE_IDENTITY_FIELDS.has(key)) {
        delete element.palette_key;
      }
    }
    editor.normalizeElementForCanvas(element, state.layout.canvas || {});
    return { inputValue: value };
  }

  const api = {
    applyPropertyInput,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPropertyActions = api;
})(typeof window !== "undefined" ? window : globalThis);
