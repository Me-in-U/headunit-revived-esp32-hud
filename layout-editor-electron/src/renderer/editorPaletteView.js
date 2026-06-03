(function exposeEditorPaletteView(globalScope) {
  function renderPalette(state, dom, options) {
    const palette = state.metadata.palette || {};
    const categories = Object.keys(palette);
    if (!categories.includes(state.activeCategory)) {
      state.activeCategory = categories[0] || "";
    }

    renderCategoryTabs(state, dom, categories, options);

    const existingByFamily = new Map();
    for (const element of state.layout.elements || []) {
      existingByFamily.set(options.editor.elementFamilyKey(element), element);
    }

    dom.paletteButtons.replaceChildren();
    const groups = options.editor
      .groupPaletteFamilies(palette[state.activeCategory] || [], state.activeCategory)
      .filter((group) => paletteGroupMatches(group, state.paletteQuery));
    if (!groups.length) {
      const empty = options.documentRef.createElement("div");
      empty.className = "empty-state";
      empty.textContent = options.translate("noPaletteResults");
      dom.paletteButtons.append(empty);
      return;
    }

    for (const group of groups) {
      dom.paletteButtons.append(renderPaletteFamily(state, group, existingByFamily, options));
    }
  }

  function renderCategoryTabs(state, dom, categories, options) {
    dom.categoryTabs.replaceChildren();
    for (const category of categories) {
      const button = options.documentRef.createElement("button");
      button.type = "button";
      button.className = `category-tab${category === state.activeCategory ? " active" : ""}`;
      button.textContent = category;
      button.addEventListener("click", () => options.onCategorySelect(category));
      dom.categoryTabs.append(button);
    }
  }

  function renderPaletteFamily(state, group, existingByFamily, options) {
    const existing = existingByFamily.get(group.familyKey);
    const activeVariant = existing ? options.editor.elementVariant(existing) : "";
    const card = options.documentRef.createElement("div");
    card.className = `palette-family${existing ? " added" : ""}`;

    const header = options.documentRef.createElement("div");
    header.className = "palette-family-header";
    header.innerHTML = `<div><span>${options.viewModel.escapeHtml(group.label)}</span><small>${options.viewModel.escapeHtml(
      group.binding || group.type
    )}</small></div><small>${existing ? options.translate("added") : group.type}</small>`;
    card.append(header);

    const variants = options.documentRef.createElement("div");
    variants.className = "variant-segment";
    for (const variant of group.variants) {
      const button = options.documentRef.createElement("button");
      button.type = "button";
      button.className = activeVariant === variant.variant ? "active" : "";
      button.textContent = variant.label;
      button.addEventListener("click", () => options.onVariantSelect(variant.item, state.activeCategory));
      variants.append(button);
    }
    card.append(variants);
    return card;
  }

  function paletteGroupMatches(group, query) {
    if (!query) {
      return true;
    }
    const haystack = [
      group.label,
      group.type,
      group.binding,
      ...group.variants.map((variant) => `${variant.label} ${variant.variant} ${variant.item?.label || ""}`),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  }

  const api = {
    paletteGroupMatches,
    renderPalette,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPaletteView = api;
})(typeof window !== "undefined" ? window : globalThis);
