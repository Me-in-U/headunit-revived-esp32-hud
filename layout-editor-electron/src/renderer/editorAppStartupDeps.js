(function exposeEditorAppStartupDeps(globalScope) {
  function appBootstrapDeps(runtime) {
    return {
      applyLanguage: runtime.applyLanguage,
      applyLoadedLayout: runtime.applyLoadedLayout,
      documentRef: runtime.documentRef,
      domBindings: runtime.domBindings,
      handlers: editorEventHandlers(runtime),
      hudEditor: runtime.windowRef.hudEditor,
      renderAll: runtime.renderAll,
      renderPreview: runtime.renderPreview,
      setStatus: runtime.setStatus,
      translate: runtime.translate,
      windowRef: runtime.windowRef,
    };
  }

  function editorEventHandlers(runtime) {
    return {
      bumpZ: runtime.bumpZ,
      chooseBackgroundImage: runtime.chooseBackgroundImage,
      clearBackgroundImage: runtime.clearBackgroundImage,
      deleteSelected: runtime.deleteSelected,
      duplicateSelected: runtime.duplicateSelected,
      exportFieldPack: runtime.exportFieldPack,
      exportSnapshot: runtime.exportSnapshot,
      fetchWeather: runtime.fetchWeather,
      hideValidationDrawer: runtime.hideValidationDrawer,
      addObdProbeCommand: runtime.addObdProbeCommand,
      editObdPidDefinition: runtime.editObdPidDefinition,
      importOtherScreen: runtime.importOtherScreen,
      copyLiveSample: runtime.copyLiveSample,
      inspectObdBle: runtime.inspectObdBle,
      onBackgroundColor: runtime.onBackgroundColor,
      onKeyDown: runtime.onKeyDown,
      onLanguageChange: runtime.onLanguageChange,
      onSimulationToggle: runtime.onSimulationToggle,
      onPointerDown: runtime.onPointerDown,
      onPointerMove: runtime.onPointerMove,
      onPointerUp: runtime.onPointerUp,
      onScreenChange: runtime.onScreenChange,
      onVehicleChange: runtime.onVehicleChange,
      onVehicleLiveEvent: runtime.onVehicleLiveEvent,
      openLayout: runtime.openLayout,
      redo: runtime.redo,
      renderOverlay: runtime.renderOverlay,
      renderPalette: runtime.renderPalette,
      resetDefaultLayout: runtime.resetDefaultLayout,
      saveLayout: runtime.saveLayout,
      saveCanSignal: runtime.saveCanSignal,
      saveObdPidDefinition: runtime.saveObdPidDefinition,
      scanComPorts: runtime.scanComPorts,
      scanObdComPorts: runtime.scanObdComPorts,
      scanObdBle: runtime.scanObdBle,
      selectCanPort: runtime.selectCanPort,
      selectComPort: runtime.selectComPort,
      selectObdDevice: runtime.selectObdDevice,
      selectObdSerialPort: runtime.selectObdSerialPort,
      selectToolTab: runtime.selectToolTab,
      startCanLive: runtime.startCanLive,
      startObdLive: runtime.startObdLive,
      startVehicleLive: runtime.startVehicleLive,
      stopCanLive: runtime.stopCanLive,
      stopObdLive: runtime.stopObdLive,
      stopVehicleLive: runtime.stopVehicleLive,
      undo: runtime.undo,
      validateLayout: runtime.validateLayout,
    };
  }

  const api = {
    appBootstrapDeps,
    editorEventHandlers,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppStartupDeps = api;
})(typeof window !== "undefined" ? window : globalThis);
