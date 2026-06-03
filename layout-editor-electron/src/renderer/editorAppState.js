(function exposeEditorAppState(globalScope) {
  function createInitialState(i18n, storage) {
    return {
      layout: null,
      path: "",
      currentScreen: "standalone",
      metadata: null,
      vehicleProfiles: {},
      selectedId: "",
      activeCategory: "",
      dirty: false,
      renderToken: 0,
      previewBusy: false,
      previewPending: false,
      drag: null,
      paletteQuery: "",
      validationMessages: [],
      history: {
        undo: [],
        redo: [],
        applying: false,
      },
      appLanguage: i18n.normalizeLanguage(storage.getItem(i18n.APP_LANGUAGE_KEY)),
    };
  }

  function createEditorDom() {
    return {};
  }

  const api = {
    createInitialState,
    createEditorDom,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppState = api;
})(typeof window !== "undefined" ? window : globalThis);
