(function exposeEditorPaletteElementFactory(globalScope) {
  const Identity =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorPaletteIdentity.js")
      : globalScope.EditorPaletteIdentity;

  const DEFAULT_GEARS = ["P", "R", "N", "D", "3", "2", "L"];

  function uniqueId(layout, base, allow = "") {
    const clean =
      String(base || "element")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9_]+/g, "_")
        .replace(/^_+|_+$/g, "") || "element";
    const ids = new Set((layout.elements || []).map((element) => element.id));
    if (clean === allow || !ids.has(clean)) {
      return clean;
    }
    let index = 2;
    while (ids.has(`${clean}_${index}`)) {
      index += 1;
    }
    return `${clean}_${index}`;
  }

  function nextZ(layout) {
    return Math.max(0, ...(layout.elements || []).map((element) => Number.parseInt(element.z || 0, 10) || 0)) + 1;
  }

  function normalizeElementForCanvas(element, canvas) {
    const width = positiveInt(canvas.width, 1920);
    const height = positiveInt(canvas.height, 480);
    element.w = Math.min(positiveInt(element.w, 100), width);
    element.h = Math.min(positiveInt(element.h, 40), height);
    element.x = clampInt(element.x, 0, Math.max(0, width - element.w), 0);
    element.y = clampInt(element.y, 0, Math.max(0, height - element.h), 0);
    element.font_size = Math.max(8, intOrDefault(element.font_size, 28));
    return element;
  }

  function createElement(layout, template, category) {
    const elementId = uniqueId(layout, String(template.label || "element").replace(/\s+/g, "_"));
    const element = {
      id: elementId,
      type: template.type || "value",
      category: String(category).toLowerCase(),
      palette_key: Identity.paletteKey(template, category),
      label: template.label || elementId,
      binding: template.binding || "",
      event_binding: template.event_binding || "",
      side_binding: template.side_binding || "",
      fallback_bindings: Identity.clone(template.fallback_bindings || []),
      text: template.text || template.label || "",
      x: 820,
      y: 210,
      w: 260,
      h: 70,
      font_size: template.font_size || 32,
      font_family: template.font_family || "default",
      font_weight: "normal",
      font_style: "normal",
      color: "#f8fbff",
      active_color: template.active_color || "#22d36b",
      inactive_color: template.inactive_color || "#7b858d",
      accent: template.accent || "#1fd66f",
      redline_color: template.redline_color || "#ff334a",
      align: "center",
      value_style: template.value_style || "digital",
      gear_style: template.gear_style || "",
      gears: Identity.clone(template.gears || []),
      active_font_size: template.active_font_size || "",
      min_value: template.min_value ?? "",
      max_value: template.max_value ?? "",
      prefix: template.prefix || "",
      suffix: template.suffix || "",
      visible: true,
      z: nextZ(layout),
    };
    if (element.type === "warning_icon") {
      element.icon = template.icon || elementId;
      element.w = 64;
      element.h = 64;
      element.show_when_inactive = false;
    }
    if (element.type === "nav_icon") {
      element.w = 96;
      element.h = 96;
      element.binding = "";
      element.event_binding = template.event_binding || "nav.event_type";
      element.side_binding = template.side_binding || "nav.turn_side";
    }
    if (element.type === "gear_indicator") {
      element.w = template.gear_style === "active_only" ? 180 : 420;
      element.h = template.gear_style === "active_only" ? 110 : 96;
      delete element.value_style;
      element.gear_style = template.gear_style || "strip";
      element.gears = Identity.clone(template.gears || DEFAULT_GEARS);
      element.active_font_size = template.active_font_size || Math.max(Number(element.font_size) * 2, 64);
    }
    normalizeElementForCanvas(element, layout.canvas || {});
    return element;
  }

  function intOrDefault(value, fallback) {
    const number = Number.parseInt(value, 10);
    return Number.isFinite(number) ? number : fallback;
  }

  function positiveInt(value, fallback) {
    return Math.max(1, intOrDefault(value, fallback));
  }

  function clampInt(value, low, high, fallback) {
    return Math.min(high, Math.max(low, intOrDefault(value, fallback)));
  }

  const api = {
    DEFAULT_GEARS,
    createElement,
    nextZ,
    normalizeElementForCanvas,
    uniqueId,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPaletteElementFactory = api;
})(typeof window !== "undefined" ? window : globalThis);
