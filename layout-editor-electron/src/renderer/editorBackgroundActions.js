(function exposeEditorBackgroundActions(globalScope) {
  function ensureCanvas(state) {
    state.layout.canvas = state.layout.canvas || {};
    return state.layout.canvas;
  }

  function applyBackgroundColor(state, color) {
    const canvas = ensureCanvas(state);
    canvas.background = color;
    return { changed: true };
  }

  function applyBackgroundImage(state, response) {
    if (!response || response.canceled) {
      return { changed: false };
    }
    const canvas = ensureCanvas(state);
    canvas.background_image = response.dataUrl;
    canvas.background_image_name = response.name;
    canvas.background_image_fit = "cover";
    return { changed: true };
  }

  function clearBackgroundImage(state) {
    const canvas = state.layout.canvas || {};
    delete canvas.background_image;
    delete canvas.background_image_name;
    delete canvas.background_image_fit;
    return { changed: true };
  }

  function applyBackgroundColorCommand(state, color, deps) {
    deps.recordHistory();
    const result = applyBackgroundColor(state, color);
    deps.markDirty();
    deps.schedulePreview(40);
    return result;
  }

  async function chooseBackgroundImageCommand(state, service, deps) {
    const response = await service.chooseBackgroundImage();
    const result = applyBackgroundImage(state, response);
    if (!result.changed) {
      return result;
    }
    deps.recordHistory();
    deps.markDirty();
    deps.schedulePreview(40);
    return result;
  }

  function clearBackgroundImageCommand(state, deps) {
    deps.recordHistory();
    const result = clearBackgroundImage(state);
    deps.markDirty();
    deps.schedulePreview(40);
    return result;
  }

  const api = {
    applyBackgroundColor,
    applyBackgroundColorCommand,
    applyBackgroundImage,
    chooseBackgroundImageCommand,
    clearBackgroundImage,
    clearBackgroundImageCommand,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorBackgroundActions = api;
})(typeof window !== "undefined" ? window : globalThis);
