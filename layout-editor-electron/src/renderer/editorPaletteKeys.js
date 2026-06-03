(function exposeEditorPaletteKeys(globalScope) {
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

  const api = {
    clone,
    elementFamilyKey,
    elementPaletteKey,
    elementPaletteKeys,
    elementVariant,
    paletteKey,
    paletteTemplateMatchesElement,
    paletteTemplateMatchesFamily,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPaletteKeys = api;
})(typeof window !== "undefined" ? window : globalThis);
