(function exposeEditorInspectorView(globalScope) {
  const WIDE_PROPERTY_KEYS = ["id", "label", "binding", "text", "fallback_bindings", "gears"];

  function renderProperties(state, dom, options) {
    const element = options.selectedElement();
    dom.selectedLabel.textContent = element ? options.viewModel.elementSummary(element) : options.translate("noSelection");
    dom.propertyForm.replaceChildren();
    if (!element) {
      const empty = options.documentRef.createElement("div");
      empty.className = "empty-state";
      empty.textContent = options.translate("selectElement");
      dom.propertyForm.append(empty);
      return;
    }

    const sections = options.editor.inspectorSectionsForElement(element);
    for (const section of sections) {
      dom.propertyForm.append(renderPropertySection(state, element, section, options));
    }
  }

  function renderPropertySection(state, element, section, options) {
    const sectionNode = section.collapsed ? options.documentRef.createElement("details") : options.documentRef.createElement("section");
    sectionNode.className = `property-section ${section.id}`;
    if (section.collapsed) {
      sectionNode.open = false;
      const summary = options.documentRef.createElement("summary");
      summary.textContent = options.sectionLabel(section);
      sectionNode.append(summary);
    } else {
      const heading = options.documentRef.createElement("h3");
      heading.textContent = options.sectionLabel(section);
      sectionNode.append(heading);
    }

    const grid = options.documentRef.createElement("div");
    grid.className = "property-section-grid";
    for (const field of section.fields) {
      grid.append(renderPropertyField(state, element, section, field, options));
    }
    sectionNode.append(grid);
    return sectionNode;
  }

  function renderPropertyField(state, element, section, field, options) {
    const key = field.key;
    const type = field.type;
    const wrap = options.documentRef.createElement("div");
    wrap.className = `property-field${WIDE_PROPERTY_KEYS.includes(key) ? " wide" : ""}`;

    const fieldLabel = options.documentRef.createElement("label");
    fieldLabel.textContent = options.propertyLabel(key, field.label);
    fieldLabel.htmlFor = `prop-${section.id}-${key}`;
    wrap.append(fieldLabel);

    const input = options.documentRef.createElement(type === "select" || type === "binding-select" ? "select" : "input");
    input.id = `prop-${section.id}-${key}`;
    input.dataset.key = key;
    input.dataset.inputType = type;
    if (type === "select") {
      for (const optionValue of field.options || []) {
        appendOption(input, optionValue, options.viewModel.optionLabel(optionValue), options.documentRef);
      }
      input.value = String(element[key] || field.options?.[0] || "");
    } else if (type === "binding-select") {
      const current = String(element[key] || "");
      const bindings = options.viewModel.bindingOptions({
        palette: state.metadata?.palette || {},
        dummyData: state.layout?.dummy_data || {},
        current,
      });
      for (const optionValue of bindings) {
        appendOption(input, optionValue, optionValue || "-", options.documentRef);
      }
      input.value = current;
    } else {
      input.type = type;
      input.value = options.viewModel.propertyValue(element, key, type);
    }
    input.addEventListener(type === "color" ? "input" : "change", options.onPropertyInput);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        options.onPropertyInput(event);
      }
    });
    wrap.append(input);
    return wrap;
  }

  function appendOption(select, value, label, documentRef) {
    const option = documentRef.createElement("option");
    option.value = value;
    option.textContent = label;
    select.append(option);
  }

  const api = {
    renderProperties,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorInspectorView = api;
})(typeof window !== "undefined" ? window : globalThis);
