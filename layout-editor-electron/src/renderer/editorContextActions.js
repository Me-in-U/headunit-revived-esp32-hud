(function exposeEditorContextActions(globalScope) {
  function applyVehicleSelection(state, selectedVehicle, editor) {
    state.layout.selected_vehicle = selectedVehicle;
    const profile = state.vehicleProfiles?.[selectedVehicle];
    if (profile) {
      const vehicles = Array.isArray(state.layout.vehicles)
        ? state.layout.vehicles.filter((item) => item.id !== selectedVehicle)
        : [];
      vehicles.push(editor.clone(profile));
      state.layout.vehicles = vehicles.sort((left, right) => String(left.id).localeCompare(String(right.id)));
    }
    return { changed: true };
  }

  function applyScreenSelection(state, selectedScreen, editor) {
    state.currentScreen = editor.switchScreen(state.layout, state.currentScreen, selectedScreen);
    state.selectedId = "";
    return { changed: true };
  }

  function importOtherScreen(state, editor) {
    editor.importOtherScreen(state.layout, state.currentScreen);
    state.selectedId = "";
    return { changed: true };
  }

  function applyLanguageSelection(state, selectedLanguage, i18n, storage) {
    state.appLanguage = i18n.normalizeLanguage(selectedLanguage);
    storage.setItem(i18n.APP_LANGUAGE_KEY, state.appLanguage);
    return { changed: true };
  }

  const api = {
    applyLanguageSelection,
    applyScreenSelection,
    applyVehicleSelection,
    importOtherScreen,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorContextActions = api;
})(typeof window !== "undefined" ? window : globalThis);
