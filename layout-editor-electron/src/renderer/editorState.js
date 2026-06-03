(function exposeEditorState(globalScope) {
  const COLOR_KEYS = ["color", "active_color", "inactive_color", "accent", "redline_color"];
  const DEFAULT_GEARS = ["P", "R", "N", "D", "3", "2", "L"];
  const VALUE_STYLE_OPTIONS = ["digital", "bar", "analog", "needle", "sport_gauge"];
  const GEAR_STYLE_OPTIONS = ["strip", "active_only"];
  const FONT_WEIGHT_OPTIONS = ["normal", "bold"];
  const FONT_STYLE_OPTIONS = ["normal", "italic"];
  const ALIGN_OPTIONS = ["left", "center", "right"];

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function paletteKey(template, category) {
    if (template.palette_key) {
      return String(template.palette_key);
    }
    const elementType = String(template.type || "value");
    const identity = String(
      template.binding ||
        template.event_binding ||
        template.icon ||
        template.text ||
        template.label ||
        ""
    ).trim();
    const style = String(template.value_style || template.gear_style || "").trim();
    return `${String(category).trim().toLowerCase()}:${elementType}:${identity}:${style}`;
  }

  function elementFamilyKey(source) {
    const elementType = String(source.type || "value");
    if (elementType === "value") {
      return `value:${String(source.binding || source.label || "").trim()}`;
    }
    if (elementType === "gear_indicator") {
      return `gear_indicator:${String(source.binding || "vehicle.gear_range").trim()}`;
    }
    if (elementType === "warning_icon") {
      return `warning_icon:${String(source.icon || source.binding || source.label || "").trim()}`;
    }
    if (elementType === "nav_icon") {
      return `nav_icon:${String(source.event_binding || source.label || "nav_icon").trim()}`;
    }
    return `${elementType}:${String(source.binding || source.text || source.label || source.id || "").trim()}`;
  }

  function elementVariant(source) {
    const elementType = String(source.type || "value");
    if (elementType === "value") {
      return String(source.value_style || "digital");
    }
    if (elementType === "gear_indicator") {
      return String(source.gear_style || "strip");
    }
    if (elementType === "warning_icon") {
      return String(source.icon || "icon");
    }
    if (elementType === "nav_icon") {
      return "icon";
    }
    return String(source.value_style || source.gear_style || source.type || "default");
  }

  function elementPaletteKey(element) {
    if (element.palette_key) {
      return String(element.palette_key);
    }
    const category = String(element.category || "").trim().toLowerCase();
    const elementType = String(element.type || "value");
    const identity = String(
      element.binding ||
        element.event_binding ||
        element.icon ||
        element.text ||
        element.label ||
        element.id ||
        ""
    ).trim();
    const style = String(element.value_style || element.gear_style || "").trim();
    return `${category}:${elementType}:${identity}:${style}`;
  }

  function paletteTemplateMatchesElement(template, element) {
    if (String(template.type || "value") !== String(element.type || "value")) {
      return false;
    }
    for (const key of ["binding", "event_binding", "icon", "text"]) {
      const templateValue = String(template[key] || "").trim();
      if (templateValue && templateValue !== String(element[key] || "").trim()) {
        return false;
      }
    }
    if (template.type === "value") {
      return String(template.value_style || "digital") === String(element.value_style || "digital");
    }
    if (template.type === "gear_indicator") {
      return String(template.gear_style || "strip") === String(element.gear_style || "strip");
    }
    return true;
  }

  function paletteTemplateMatchesFamily(template, element) {
    return elementFamilyKey(template) === elementFamilyKey(element);
  }

  function elementPaletteKeys(element, palette) {
    const keys = new Set([elementPaletteKey(element)]);
    for (const [category, items] of Object.entries(palette || {})) {
      for (const item of items) {
        if (paletteTemplateMatchesElement(item, element)) {
          keys.add(paletteKey(item, category));
        }
      }
    }
    return keys;
  }

  function findPaletteElement(layout, template, category, palette) {
    const key = paletteKey(template, category);
    return (layout.elements || []).find((element) => elementPaletteKeys(element, palette).has(key)) || null;
  }

  function findPaletteFamilyElement(layout, template) {
    return (layout.elements || []).find((element) => paletteTemplateMatchesFamily(template, element)) || null;
  }

  function findGearFamilyElement(layout, template) {
    if (template.type !== "gear_indicator") {
      return null;
    }
    const binding = String(template.binding || "vehicle.gear_range").trim();
    return (
      (layout.elements || []).find(
        (element) => element.type === "gear_indicator" && String(element.binding || "").trim() === binding
      ) || null
    );
  }

  function cleanFamilyLabel(item) {
    const label = String(item.label || item.binding || item.icon || item.type || "Element").trim();
    const variant = elementVariant(item).replace(/_/g, " ");
    if (String(item.type || "value") === "value") {
      return label.replace(new RegExp(`\\s+${escapeRegExp(variant)}$`, "i"), "") || label;
    }
    if (String(item.type || "value") === "gear_indicator") {
      return label.replace(/\s+(strip|active|active only)$/i, "") || label;
    }
    return label;
  }

  function variantLabel(value) {
    return titleCase(String(value || "default"));
  }

  function groupPaletteFamilies(items, category) {
    const groups = [];
    const byKey = new Map();
    for (const item of items || []) {
      const familyKey = elementFamilyKey(item);
      if (!byKey.has(familyKey)) {
        const group = {
          category,
          familyKey,
          label: cleanFamilyLabel(item),
          type: String(item.type || "value"),
          binding: item.binding || "",
          variants: [],
        };
        byKey.set(familyKey, group);
        groups.push(group);
      }
      const variant = elementVariant(item);
      byKey.get(familyKey).variants.push({
        variant,
        label: variantLabel(variant),
        paletteKey: paletteKey(item, category),
        item,
      });
    }
    return groups;
  }

  function uniqueId(layout, base, allow = "") {
    const clean = String(base || "element")
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
      palette_key: paletteKey(template, category),
      label: template.label || elementId,
      binding: template.binding || "",
      event_binding: template.event_binding || "",
      side_binding: template.side_binding || "",
      fallback_bindings: clone(template.fallback_bindings || []),
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
      gears: clone(template.gears || []),
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
      element.gears = clone(template.gears || DEFAULT_GEARS);
      element.active_font_size = template.active_font_size || Math.max(Number(element.font_size) * 2, 64);
    }
    normalizeElementForCanvas(element, layout.canvas || {});
    return element;
  }

  function applyValueTemplate(element, template, category) {
    element.category = String(category).toLowerCase();
    element.palette_key = paletteKey(template, category);
    element.label = template.label || element.label || cleanFamilyLabel(template);
    element.binding = template.binding || element.binding || "";
    element.fallback_bindings = clone(template.fallback_bindings || element.fallback_bindings || []);
    element.value_style = template.value_style || element.value_style || "digital";
    element.font_size = template.font_size || element.font_size || 32;
    for (const key of ["min_value", "max_value", "tick_interval", "prefix", "suffix", "accent", "inactive_color", "redline_color"]) {
      if (Object.prototype.hasOwnProperty.call(template, key)) {
        element[key] = clone(template[key]);
      }
    }
    delete element.gear_style;
    return normalizeElementForCanvas(element, { width: 1920, height: 480 });
  }

  function applyGearTemplate(element, template, category) {
    element.category = String(category).toLowerCase();
    element.palette_key = paletteKey(template, category);
    element.label = template.label || element.label || "Gear";
    element.binding = template.binding || element.binding || "vehicle.gear_range";
    element.gear_style = template.gear_style || element.gear_style || "strip";
    element.gears = clone(template.gears || element.gears || DEFAULT_GEARS);
    element.font_size = template.font_size || element.font_size || 28;
    element.active_font_size = template.active_font_size || element.active_font_size || 92;
    if (element.gear_style === "active_only") {
      element.w = Math.max(Number(element.w || 0), 180);
      element.h = Math.max(Number(element.h || 0), 110);
    } else {
      element.w = Math.max(Number(element.w || 0), 420);
      element.h = Math.max(Number(element.h || 0), 96);
    }
    delete element.value_style;
    return normalizeElementForCanvas(element, { width: 1920, height: 480 });
  }

  function applyPaletteTemplate(element, template, category) {
    const type = String(template.type || element.type || "value");
    if (type === "value") {
      return applyValueTemplate(element, template, category);
    }
    if (type === "gear_indicator") {
      return applyGearTemplate(element, template, category);
    }
    element.category = String(category).toLowerCase();
    element.palette_key = paletteKey(template, category);
    element.label = template.label || element.label || cleanFamilyLabel(template);
    element.type = type;
    for (const key of ["binding", "event_binding", "side_binding", "icon", "text", "font_size", "accent", "inactive_color"]) {
      if (Object.prototype.hasOwnProperty.call(template, key)) {
        element[key] = clone(template[key]);
      }
    }
    return normalizeElementForCanvas(element, { width: 1920, height: 480 });
  }

  function addOrTogglePaletteElement(layout, template, category, palette) {
    const existing = findPaletteElement(layout, template, category, palette);
    if (existing) {
      return { action: "selected", element: existing };
    }
    const family = findPaletteFamilyElement(layout, template) || findGearFamilyElement(layout, template);
    if (family) {
      applyPaletteTemplate(family, template, category);
      return { action: "updated", element: family };
    }
    const element = createElement(layout, template, category);
    layout.elements = [...(layout.elements || []), element];
    return { action: "added", element };
  }

  function inspectorSectionsForElement(element) {
    if (!element) {
      return [];
    }
    const type = String(element.type || "value");
    const sections = [
      {
        id: "basic",
        label: "Basic",
        fields: [
          field("label", "Label", "text"),
          ...(type === "value" || type === "text" ? [field("text", "Text", "text")] : []),
        ],
      },
      {
        id: "layout",
        label: "Position / Size",
        fields: [
          field("x", "X", "number"),
          field("y", "Y", "number"),
          field("w", "W", "number"),
          field("h", "H", "number"),
        ],
      },
    ];
    if (type === "value") {
      sections.push({
        id: "data",
        label: "Data",
        fields: [
          field("binding", "Binding", "binding-select"),
          field("min_value", "Minimum value", "number"),
          field("max_value", "Maximum value", "number"),
          field("tick_interval", "Tick interval", "number"),
        ],
      });
      sections.push({
        id: "presentation",
        label: "Presentation",
        fields: [
          field("value_style", "Value style", "select", VALUE_STYLE_OPTIONS),
          field("prefix", "Prefix", "text"),
          field("suffix", "Suffix", "text"),
          field("font_size", "Font size", "number"),
          field("align", "Align", "select", ALIGN_OPTIONS),
          field("font_weight", "Weight", "select", FONT_WEIGHT_OPTIONS),
          field("font_style", "Style", "select", FONT_STYLE_OPTIONS),
          field("color", "Color", "color"),
          field("accent", "Accent", "color"),
          field("inactive_color", "Inactive", "color"),
          field("redline_color", "Redline", "color"),
        ],
      });
      sections.push({
        id: "advanced",
        label: "Advanced",
        collapsed: true,
        fields: [
          field("id", "ID", "text"),
          field("binding", "Raw binding", "text"),
          field("fallback_bindings", "Fallbacks", "text"),
        ],
      });
      return sections;
    }
    if (type === "gear_indicator") {
      sections.push({
        id: "data",
        label: "Data",
        fields: [
          field("binding", "Binding", "binding-select"),
          field("gears", "Gears", "text"),
        ],
      });
      sections.push({
        id: "presentation",
        label: "Presentation",
        fields: [
          field("gear_style", "Gear style", "select", GEAR_STYLE_OPTIONS),
          field("font_size", "Font size", "number"),
          field("active_font_size", "Active font", "number"),
          field("color", "Color", "color"),
          field("active_color", "Active", "color"),
          field("inactive_color", "Inactive", "color"),
        ],
      });
      sections.push({
        id: "advanced",
        label: "Advanced",
        collapsed: true,
        fields: [
          field("id", "ID", "text"),
          field("binding", "Raw binding", "text"),
          field("fallback_bindings", "Fallbacks", "text"),
        ],
      });
      return sections;
    }
    if (type === "nav_icon") {
      sections.push({
        id: "data",
        label: "Data",
        fields: [
          field("event_binding", "Event binding", "binding-select"),
          field("side_binding", "Side binding", "binding-select"),
        ],
      });
      sections.push({
        id: "presentation",
        label: "Presentation",
        fields: [
          field("font_size", "Font size", "number"),
          field("color", "Color", "color"),
          field("accent", "Accent", "color"),
          field("inactive_color", "Inactive", "color"),
        ],
      });
    } else if (type === "warning_icon") {
      sections.push({
        id: "data",
        label: "Data",
        fields: [
          field("binding", "Binding", "binding-select"),
          field("icon", "Icon", "text"),
        ],
      });
      sections.push({
        id: "presentation",
        label: "Presentation",
        fields: [
          field("font_size", "Font size", "number"),
          field("color", "Color", "color"),
          field("active_color", "Active", "color"),
          field("inactive_color", "Inactive", "color"),
        ],
      });
    } else {
      sections.push({
        id: "presentation",
        label: "Presentation",
        fields: [
          field("font_size", "Font size", "number"),
          field("color", "Color", "color"),
          field("font_weight", "Weight", "select", FONT_WEIGHT_OPTIONS),
          field("font_style", "Style", "select", FONT_STYLE_OPTIONS),
        ],
      });
    }
    sections.push({
      id: "advanced",
      label: "Advanced",
      collapsed: true,
      fields: [
        field("id", "ID", "text"),
        field("binding", "Raw binding", "text"),
        field("fallback_bindings", "Fallbacks", "text"),
      ],
    });
    return sections;
  }

  function field(key, label, type, options = []) {
    return { key, label, type, options };
  }

  function ensureScreens(layout, currentScreen = "standalone") {
    const baseElements = clone(layout.elements || []);
    if (!layout.screens || typeof layout.screens !== "object" || Array.isArray(layout.screens)) {
      layout.screens = {};
    }
    for (const [screen, label] of [
      ["standalone", "Standalone vehicle HUD"],
      ["bridge", "Bridge navigation HUD"],
    ]) {
      if (!layout.screens[screen] || typeof layout.screens[screen] !== "object") {
        layout.screens[screen] = { label, elements: clone(baseElements) };
      }
      if (!Array.isArray(layout.screens[screen].elements)) {
        layout.screens[screen].elements = clone(baseElements);
      }
    }
    const selected = layout.screens[currentScreen] ? currentScreen : "standalone";
    layout.elements = clone(layout.screens[selected].elements);
    return selected;
  }

  function syncCurrentScreen(layout, currentScreen) {
    if (!layout.screens || typeof layout.screens !== "object" || Array.isArray(layout.screens)) {
      layout.screens = {};
    }
    if (!layout.screens[currentScreen] || typeof layout.screens[currentScreen] !== "object") {
      layout.screens[currentScreen] = { label: titleCase(currentScreen), elements: [] };
    }
    layout.screens[currentScreen].elements = clone(layout.elements || []);
  }

  function switchScreen(layout, fromScreen, toScreen) {
    syncCurrentScreen(layout, fromScreen);
    const selected = layout.screens[toScreen] ? toScreen : "standalone";
    layout.elements = clone(layout.screens[selected].elements || []);
    return selected;
  }

  function importOtherScreen(layout, currentScreen) {
    syncCurrentScreen(layout, currentScreen);
    const other = currentScreen === "standalone" ? "bridge" : "standalone";
    layout.screens[currentScreen].elements = clone(layout.screens[other].elements || []);
    layout.elements = clone(layout.screens[currentScreen].elements);
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

  function titleCase(value) {
    return String(value || "")
      .replace(/[_-]+/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function escapeRegExp(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  const api = {
    COLOR_KEYS,
    DEFAULT_GEARS,
    VALUE_STYLE_OPTIONS,
    GEAR_STYLE_OPTIONS,
    clone,
    paletteKey,
    elementFamilyKey,
    elementVariant,
    elementPaletteKey,
    elementPaletteKeys,
    paletteTemplateMatchesElement,
    paletteTemplateMatchesFamily,
    findPaletteElement,
    findPaletteFamilyElement,
    groupPaletteFamilies,
    uniqueId,
    nextZ,
    normalizeElementForCanvas,
    createElement,
    addOrTogglePaletteElement,
    inspectorSectionsForElement,
    ensureScreens,
    syncCurrentScreen,
    switchScreen,
    importOtherScreen,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorState = api;
})(typeof window !== "undefined" ? window : globalThis);
