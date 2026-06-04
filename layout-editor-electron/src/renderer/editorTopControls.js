(function exposeEditorTopControls(globalScope) {
  function renderTopControls(state, dom, options) {
    const documentRef = options.documentRef;
    const validColor = options.validColor;
    const vehicleLabel = options.vehicleLabel;
    const canvas = state.layout.canvas || {};
    dom.canvasMeta.textContent = `${canvas.width || 1920} x ${canvas.height || 480}, ${state.layout.elements?.length || 0} elements`;
    dom.screenSelect.value = state.currentScreen;
    dom.languageSelect.value = state.appLanguage;
    dom.backgroundColor.value = validColor(canvas.background) ? canvas.background : "#05080c";
    if (dom.simulationToggle) {
      dom.simulationToggle.checked = Boolean(state.simulationEnabled);
    }
    dom.undoBtn.disabled = !state.history.undo.length;
    dom.redoBtn.disabled = !state.history.redo.length;
    dom.paletteSearch.value = state.paletteQuery;

    const vehicleIds = Object.keys(state.vehicleProfiles || {});
    dom.vehicleSelect.replaceChildren();
    for (const vehicleId of vehicleIds) {
      const option = documentRef.createElement("option");
      option.value = vehicleId;
      option.textContent = vehicleLabel(state.vehicleProfiles, vehicleId);
      dom.vehicleSelect.append(option);
    }
    const selected = state.layout.selected_vehicle || vehicleIds[0] || "";
    if (selected && !vehicleIds.includes(selected)) {
      const option = documentRef.createElement("option");
      option.value = selected;
      option.textContent = selected;
      dom.vehicleSelect.append(option);
    }
    dom.vehicleSelect.value = selected;
  }

  const api = {
    renderTopControls,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorTopControls = api;
})(typeof window !== "undefined" ? window : globalThis);
