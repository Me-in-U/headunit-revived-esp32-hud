(function exposeEditorPreviewActions(globalScope) {
  async function renderPreview(state, dom, options) {
    if (!state.layout) {
      return;
    }
    if (state.previewBusy) {
      state.previewPending = true;
      return;
    }
    state.previewBusy = true;
    const token = ++state.renderToken;
    options.setStatus(options.translate("renderPreview"));
    try {
      const canvas = state.layout.canvas || {};
      const response = await options.renderPreview({
        layout: state.layout,
        currentScreen: state.currentScreen,
        width: canvas.width || 1920,
        height: canvas.height || 480,
      });
      if (token !== state.renderToken) {
        return;
      }
      dom.previewImage.src = `data:image/png;base64,${response.png}`;
      dom.pixelStatus.textContent = `${response.width} x ${response.height}`;
      options.hideDragGhost();
      options.setStatus(options.translate("previewReady"), "ok");
      options.requestAnimationFrame(options.renderOverlay);
    } catch (error) {
      options.setStatus(error.message, "error");
    } finally {
      state.previewBusy = false;
      if (state.previewPending) {
        state.previewPending = false;
        options.schedulePreview(30);
      }
    }
  }

  const api = {
    renderPreview,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPreviewActions = api;
})(typeof window !== "undefined" ? window : globalThis);
