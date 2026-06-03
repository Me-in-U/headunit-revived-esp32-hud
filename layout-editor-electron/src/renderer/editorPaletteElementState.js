(function exposeEditorPaletteElementState(globalScope) {
  const Identity =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorPaletteIdentity.js")
      : globalScope.EditorPaletteIdentity;
  const Factory =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorPaletteElementFactory.js")
      : globalScope.EditorPaletteElementFactory;

  function findPaletteElement(layout, template, category, palette) {
    const key = Identity.paletteKey(template, category);
    return (layout.elements || []).find((element) => Identity.elementPaletteKeys(element, palette).has(key)) || null;
  }

  function findPaletteFamilyElement(layout, template) {
    return (layout.elements || []).find((element) => Identity.paletteTemplateMatchesFamily(template, element)) || null;
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

  function applyValueTemplate(element, template, category) {
    element.category = String(category).toLowerCase();
    element.palette_key = Identity.paletteKey(template, category);
    element.label = template.label || element.label || Identity.cleanFamilyLabel(template);
    element.binding = template.binding || element.binding || "";
    element.fallback_bindings = Identity.clone(template.fallback_bindings || element.fallback_bindings || []);
    element.value_style = template.value_style || element.value_style || "digital";
    element.font_size = template.font_size || element.font_size || 32;
    for (const key of ["min_value", "max_value", "tick_interval", "prefix", "suffix", "accent", "inactive_color", "redline_color"]) {
      if (Object.prototype.hasOwnProperty.call(template, key)) {
        element[key] = Identity.clone(template[key]);
      }
    }
    delete element.gear_style;
    return Factory.normalizeElementForCanvas(element, { width: 1920, height: 480 });
  }

  function applyGearTemplate(element, template, category) {
    element.category = String(category).toLowerCase();
    element.palette_key = Identity.paletteKey(template, category);
    element.label = template.label || element.label || "Gear";
    element.binding = template.binding || element.binding || "vehicle.gear_range";
    element.gear_style = template.gear_style || element.gear_style || "strip";
    element.gears = Identity.clone(template.gears || element.gears || Factory.DEFAULT_GEARS);
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
    return Factory.normalizeElementForCanvas(element, { width: 1920, height: 480 });
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
    element.palette_key = Identity.paletteKey(template, category);
    element.label = template.label || element.label || Identity.cleanFamilyLabel(template);
    element.type = type;
    for (const key of ["binding", "event_binding", "side_binding", "icon", "text", "font_size", "accent", "inactive_color"]) {
      if (Object.prototype.hasOwnProperty.call(template, key)) {
        element[key] = Identity.clone(template[key]);
      }
    }
    return Factory.normalizeElementForCanvas(element, { width: 1920, height: 480 });
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
    const element = Factory.createElement(layout, template, category);
    layout.elements = [...(layout.elements || []), element];
    return { action: "added", element };
  }

  const api = {
    DEFAULT_GEARS: Factory.DEFAULT_GEARS,
    addOrTogglePaletteElement,
    createElement: Factory.createElement,
    findPaletteElement,
    findPaletteFamilyElement,
    nextZ: Factory.nextZ,
    normalizeElementForCanvas: Factory.normalizeElementForCanvas,
    uniqueId: Factory.uniqueId,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPaletteElementState = api;
})(typeof window !== "undefined" ? window : globalThis);
