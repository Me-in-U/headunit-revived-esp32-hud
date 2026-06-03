(function exposeEditorLayerView(globalScope) {
  function renderLayers(state, dom, options) {
    const elements = [...(state.layout.elements || [])].sort((left, right) => Number(right.z || 0) - Number(left.z || 0));
    dom.layerCount.textContent = String(elements.length);
    dom.layerList.replaceChildren();
    if (!elements.length) {
      const empty = options.documentRef.createElement("div");
      empty.className = "empty-state";
      empty.textContent = options.translate("noElements");
      dom.layerList.append(empty);
      return;
    }
    for (const element of elements) {
      dom.layerList.append(renderLayerRow(state, element, options));
    }
  }

  function renderLayerRow(state, element, options) {
    const row = options.documentRef.createElement("button");
    row.type = "button";
    row.className = `layer-row${element.id === state.selectedId ? " selected" : ""}`;
    row.innerHTML = `<div><div class="layer-id">${options.viewModel.escapeHtml(
      options.viewModel.elementLabel(element)
    )}</div><div class="layer-type">${options.viewModel.escapeHtml(options.viewModel.elementStyleLabel(element))} · ${options.viewModel.escapeHtml(
      options.viewModel.elementDataLabel(element)
    )}</div></div><div class="layer-type">z ${Number(element.z || 0)}</div>`;
    row.addEventListener("click", () => options.onLayerSelect(element.id));
    return row;
  }

  const api = {
    renderLayers,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorLayerView = api;
})(typeof window !== "undefined" ? window : globalThis);
