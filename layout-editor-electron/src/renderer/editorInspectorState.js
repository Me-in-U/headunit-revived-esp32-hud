(function exposeEditorInspectorState(globalScope) {
  const VALUE_STYLE_OPTIONS = ["digital", "bar", "analog", "needle", "sport_gauge"];
  const GEAR_STYLE_OPTIONS = ["strip", "active_only"];
  const FONT_WEIGHT_OPTIONS = ["normal", "bold"];
  const FONT_STYLE_OPTIONS = ["normal", "italic"];
  const ALIGN_OPTIONS = ["left", "center", "right"];

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
      sections.push(advancedSection());
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
      sections.push(advancedSection());
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
    sections.push(advancedSection());
    return sections;
  }

  function advancedSection() {
    return {
      id: "advanced",
      label: "Advanced",
      collapsed: true,
      fields: [
        field("id", "ID", "text"),
        field("binding", "Raw binding", "text"),
        field("fallback_bindings", "Fallbacks", "text"),
      ],
    };
  }

  function field(key, label, type, options = []) {
    return { key, label, type, options };
  }

  const api = {
    VALUE_STYLE_OPTIONS,
    GEAR_STYLE_OPTIONS,
    inspectorSectionsForElement,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorInspectorState = api;
})(typeof window !== "undefined" ? window : globalThis);
