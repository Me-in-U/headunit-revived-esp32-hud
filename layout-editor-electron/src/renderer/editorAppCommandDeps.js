(function exposeEditorAppCommandDeps(globalScope) {
  function fileCommandDeps(runtime) {
    return {
      confirm: (message) => runtime.windowRef.confirm(message),
      confirmDiscardChanges: runtime.confirmDiscardChanges,
      editor: runtime.editor,
      fileActions: runtime.fileActions,
      hideDragGhost: () => runtime.pointerActions.hideDragGhost(runtime.dom),
      hideValidationDrawer: runtime.hideValidationDrawer,
      pixelStatus: runtime.dom.pixelStatus,
      renderAll: runtime.renderAll,
      renderPreview: runtime.renderPreview,
      setStatus: runtime.setStatus,
      showValidationDrawer: runtime.showValidationDrawer,
      translate: runtime.translate,
    };
  }

  function weatherActionDeps(runtime) {
    return {
      markDirty: runtime.markDirty,
      recordHistory: runtime.recordHistory,
      renderAll: runtime.renderAll,
      schedulePreview: runtime.schedulePreview,
      setStatus: runtime.setStatus,
      translate: runtime.translate,
    };
  }

  function vehicleLiveActionDeps(runtime) {
    return {
      markDirty: runtime.markDirty,
      recordHistory: runtime.recordHistory,
      renderAll: runtime.renderAll,
      renderLayers: runtime.renderLayers,
      renderOverlay: runtime.renderOverlay,
      renderProperties: runtime.renderProperties,
      renderVehicleTools: runtime.renderVehicleTools,
      schedulePreview: runtime.schedulePreview,
      setStatus: runtime.setStatus,
      vehicleLiveState: runtime.vehicleLiveState,
    };
  }

  function contextCommandDeps(runtime) {
    return {
      applyLanguage: runtime.applyLanguage,
      contextActions: runtime.contextActions,
      editor: runtime.editor,
      i18n: runtime.i18n,
      localStorageRef: runtime.localStorageRef,
      markDirty: runtime.markDirty,
      recordHistory: runtime.recordHistory,
      renderAll: runtime.renderAll,
      schedulePreview: runtime.schedulePreview,
    };
  }

  function backgroundActionDeps(runtime) {
    return {
      markDirty: runtime.markDirty,
      recordHistory: runtime.recordHistory,
      schedulePreview: runtime.schedulePreview,
    };
  }

  function editActionDeps(runtime) {
    return {
      editor: runtime.editor,
      markDirty: runtime.markDirty,
      propertyActions: runtime.propertyActions,
      pushUndoSnapshot: runtime.pushUndoSnapshot,
      recordHistory: runtime.recordHistory,
      renderAll: runtime.renderAll,
      renderLayers: runtime.renderLayers,
      renderOverlay: runtime.renderOverlay,
      renderProperties: runtime.renderProperties,
      requestAnimationFrame: runtime.requestAnimationFrameRef,
      schedulePreview: runtime.schedulePreview,
      snapshotState: runtime.snapshotState,
    };
  }

  function pointerActionDeps(runtime) {
    return {
      canvasScale: runtime.canvasScale,
      dragActions: runtime.dragActions,
      dragGhost: runtime.dragGhost,
      editor: runtime.editor,
      elementActions: runtime.elementActions,
      elementById: runtime.elementById,
      eventToCanvas: runtime.eventToCanvas,
      hitTest: runtime.hitTest,
      markDirty: runtime.markDirty,
      recordHistory: runtime.recordHistory,
      renderAll: runtime.renderAll,
      renderOverlay: runtime.renderOverlay,
      renderProperties: runtime.renderProperties,
      schedulePreview: runtime.schedulePreview,
    };
  }

  function commandActionDeps(runtime) {
    return {
      editor: runtime.editor,
      elementActions: runtime.elementActions,
      keyboardActions: runtime.keyboardActions,
      markDirty: runtime.markDirty,
      recordHistory: runtime.recordHistory,
      redo: runtime.redo,
      renderAll: runtime.renderAll,
      renderLayers: runtime.renderLayers,
      renderOverlay: runtime.renderOverlay,
      schedulePreview: runtime.schedulePreview,
      selectedElement: runtime.selectedElement,
      setStatus: runtime.setStatus,
      translate: runtime.translate,
      undo: runtime.undo,
    };
  }

  function historyCommandDeps(runtime) {
    return {
      editor: runtime.editor,
      history: runtime.history,
      renderAll: runtime.renderAll,
      renderTopControls: runtime.renderTopControls,
      schedulePreview: runtime.schedulePreview,
      updateFilePath: runtime.updateFilePath,
    };
  }

  const api = {
    backgroundActionDeps,
    commandActionDeps,
    contextCommandDeps,
    editActionDeps,
    fileCommandDeps,
    historyCommandDeps,
    pointerActionDeps,
    vehicleLiveActionDeps,
    weatherActionDeps,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppCommandDeps = api;
})(typeof window !== "undefined" ? window : globalThis);
