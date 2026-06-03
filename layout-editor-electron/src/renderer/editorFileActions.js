(function exposeEditorFileActions(globalScope) {
  function errorMessage(response, fallback) {
    if (Array.isArray(response?.errors) && response.errors.length > 0) {
      return response.errors.join("\n");
    }
    return fallback;
  }

  function layoutPayload(state) {
    return {
      layout: state.layout,
      path: state.path,
      currentScreen: state.currentScreen,
    };
  }

  function applyLoadedLayout(state, response, editor) {
    if (!response || response.canceled) {
      return { applied: false, canceled: true };
    }
    if (!response.ok) {
      return { applied: false, errorMessage: errorMessage(response, "Failed to load layout") };
    }
    state.layout = response.layout;
    state.path = response.path || "";
    state.currentScreen = response.currentScreen || editor.ensureScreens(state.layout, "standalone");
    state.vehicleProfiles = response.vehicleProfiles || state.vehicleProfiles || {};
    editor.ensureScreens(state.layout, state.currentScreen);
    state.layout.language = state.layout.language || "ko";
    state.layout.supported_languages = ["ko", "en"];
    state.selectedId = "";
    state.dirty = false;
    state.validationMessages = [];
    state.history.undo = [];
    state.history.redo = [];
    return { applied: true };
  }

  async function saveLayout(state, saveAs, service) {
    const response = saveAs
      ? await service.saveLayoutAs(layoutPayload(state))
      : await service.saveLayout(layoutPayload(state));
    if (response?.canceled) {
      return { saved: false, canceled: true };
    }
    if (!response?.ok) {
      return { saved: false, errorMessage: errorMessage(response, "Save failed") };
    }
    state.layout = response.layout;
    state.path = response.path;
    state.dirty = false;
    state.history.undo = [];
    state.history.redo = [];
    return { saved: true, message: response.message || "Saved" };
  }

  async function validateLayout(state, service) {
    return service.validateLayout(layoutPayload(state));
  }

  async function exportWithMessage(state, serviceCall, okPrefix) {
    const response = await serviceCall(layoutPayload(state));
    if (response?.canceled) {
      return { canceled: true };
    }
    if (response?.ok) {
      return { canceled: false, ok: true, message: `${okPrefix}: ${response.output}` };
    }
    return { canceled: false, ok: false, errorMessage: errorMessage(response, `${okPrefix} failed`) };
  }

  function exportSnapshot(state, service) {
    return exportWithMessage(state, service.exportSnapshot.bind(service), "PNG exported");
  }

  function exportFieldPack(state, service) {
    return exportWithMessage(state, service.exportFieldPack.bind(service), "Field pack exported");
  }

  const api = {
    applyLoadedLayout,
    exportFieldPack,
    exportSnapshot,
    layoutPayload,
    saveLayout,
    validateLayout,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorFileActions = api;
})(typeof window !== "undefined" ? window : globalThis);
