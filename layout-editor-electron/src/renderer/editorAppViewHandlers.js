(function exposeEditorAppViewHandlers(globalScope) {
  function createAppViewHandlers({ state, dom, modules, refs }) {
    function eventToCanvas(event) {
      const canvas = state.layout.canvas || { width: 1920, height: 480 };
      const rect = dom.previewStage.getBoundingClientRect();
      return modules.viewModel.eventToCanvasPoint(event, canvas, rect);
    }

    function canvasScale() {
      const canvas = state.layout?.canvas || { width: 1920, height: 480 };
      const stageRect = dom.previewStage.getBoundingClientRect();
      return modules.viewModel.canvasScale(canvas, stageRect);
    }

    function hitTest(x, y) {
      return modules.viewModel.hitTestElement(state.layout.elements || [], x, y);
    }

    function selectedElement() {
      return modules.elementActions.selectedElement(state);
    }

    function elementById(id) {
      return modules.elementActions.elementById(state.layout, id);
    }

    function confirmDiscardChanges() {
      if (!state.dirty) {
        return true;
      }
      return refs.windowRef.confirm(`${translate("unsaved")}. ${translate("discardConfirm")}`);
    }

    function showValidationDrawer(messages) {
      modules.domActions.showValidationDrawer(state, dom, messages, refs.documentRef);
    }

    function hideValidationDrawer() {
      modules.domActions.hideValidationDrawer(state, dom);
    }

    function updateFilePath() {
      modules.domActions.updateFilePath(state, dom, translate);
    }

    function setStatus(message, kind = "") {
      modules.domActions.setStatus(dom, message, kind);
    }

    function applyLanguage() {
      modules.domActions.applyLanguage(refs.documentRef, state.appLanguage, translate);
    }

    function translate(key) {
      return modules.i18n.translate(state.appLanguage, key);
    }

    function propertyLabel(key, fallback) {
      return modules.i18n.propertyLabel(state.appLanguage, key, fallback);
    }

    return {
      applyLanguage,
      canvasScale,
      confirmDiscardChanges,
      elementById,
      eventToCanvas,
      hideValidationDrawer,
      hitTest,
      propertyLabel,
      selectedElement,
      setStatus,
      showValidationDrawer,
      translate,
      updateFilePath,
    };
  }

  const api = {
    createAppViewHandlers,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppViewHandlers = api;
})(typeof window !== "undefined" ? window : globalThis);
