(function exposeEditorViewModel(globalScope) {
  const CanvasViewModel =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorCanvasViewModel.js")
      : globalScope.EditorCanvasViewModel;

  function optionLabel(value) {
    return String(value || "")
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function elementLabel(element) {
    return String(element?.label || element?.id || element?.type || "Element");
  }

  function elementStyleLabel(element) {
    if (element?.type === "value") {
      return optionLabel(element.value_style || "digital");
    }
    if (element?.type === "gear_indicator") {
      return optionLabel(element.gear_style || "strip");
    }
    if (element?.type === "warning_icon") {
      return "Warning";
    }
    if (element?.type === "nav_icon") {
      return "Nav icon";
    }
    return optionLabel(element?.type || "value");
  }

  function elementDataLabel(element) {
    return String(element?.binding || element?.event_binding || element?.icon || element?.text || element?.id || "");
  }

  function elementSummary(element) {
    return `${elementLabel(element)} · ${elementStyleLabel(element)}`;
  }

  function propertyValue(element, key, type) {
    const value = element?.[key];
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    if (type === "color") {
      return validColor(value) ? value : "#ffffff";
    }
    return value ?? "";
  }

  function fieldApplies(key, element) {
    if (["value_style", "min_value", "max_value", "tick_interval"].includes(key)) {
      return element?.type === "value";
    }
    if (["gear_style", "gears", "active_font_size"].includes(key)) {
      return element?.type === "gear_indicator";
    }
    if (["event_binding", "side_binding"].includes(key)) {
      return element?.type === "nav_icon";
    }
    return true;
  }

  function bindingOptions({ palette = {}, dummyData = {}, current = "" } = {}) {
    const values = new Set();
    for (const items of Object.values(palette || {})) {
      for (const item of items || []) {
        for (const key of ["binding", "event_binding", "side_binding"]) {
          if (item[key]) {
            values.add(String(item[key]));
          }
        }
        for (const fallback of item.fallback_bindings || []) {
          values.add(String(fallback));
        }
      }
    }
    collectBindingPaths(dummyData, "", values);
    if (current) {
      values.add(current);
    }
    return [...values].sort((left, right) => left.localeCompare(right));
  }

  function collectBindingPaths(value, prefix, output) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      return;
    }
    for (const [key, child] of Object.entries(value)) {
      const path = prefix ? `${prefix}.${key}` : key;
      if (child && typeof child === "object" && !Array.isArray(child)) {
        collectBindingPaths(child, path, output);
      } else {
        output.add(path);
      }
    }
  }

  function vehicleLabel(vehicleProfiles, vehicleId) {
    const profile = vehicleProfiles?.[vehicleId];
    return profile?.label ? `${profile.label} (${vehicleId})` : vehicleId;
  }

  function validColor(value) {
    return typeof value === "string" && /^#[0-9a-fA-F]{6}$/.test(value);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  const api = {
    bindingOptions,
    canvasScale: CanvasViewModel.canvasScale,
    elementDataLabel,
    elementLabel,
    elementStyleLabel,
    elementSummary,
    escapeHtml,
    eventToCanvasPoint: CanvasViewModel.eventToCanvasPoint,
    fieldApplies,
    hitTestElement: CanvasViewModel.hitTestElement,
    optionLabel,
    propertyValue,
    validColor,
    vehicleLabel,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorViewModel = api;
})(typeof window !== "undefined" ? window : globalThis);
