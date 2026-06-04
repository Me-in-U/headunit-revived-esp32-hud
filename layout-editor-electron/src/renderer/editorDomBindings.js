(function exposeEditorDomBindings(globalScope) {
  const DOM_IDS = [
    "filePath",
    "openBtn",
    "saveBtn",
    "saveAsBtn",
    "undoBtn",
    "redoBtn",
    "resetBtn",
    "validateBtn",
    "exportPngBtn",
    "fieldPackBtn",
    "simulationToggle",
    "vehicleSelect",
    "screenSelect",
    "importScreenBtn",
    "languageSelect",
    "weatherBtn",
    "backgroundColor",
    "backgroundImageBtn",
    "clearBackgroundBtn",
    "elementsTab",
    "connectionTab",
    "canAnalysisTab",
    "obdAnalysisTab",
    "elementsPanel",
    "connectionPanel",
    "canAnalysisPanel",
    "obdAnalysisPanel",
    "obdEnabled",
    "obdBleMac",
    "obdBleRxUuid",
    "obdBleTxUuid",
    "obdTimeout",
    "scanObdBtn",
    "obdDeviceList",
    "obdSelectedStatus",
    "obdAdvancedSettings",
    "inspectObdBtn",
    "obdConnectionStatus",
    "canEnabled",
    "scanComPortsBtn",
    "comPortList",
    "comSelectedStatus",
    "canChannel",
    "canBitrate",
    "canListenOnly",
    "startVehicleLiveBtn",
    "stopVehicleLiveBtn",
    "canConnectionStatus",
    "liveCanStatus",
    "liveObdStatus",
    "liveSampleStatus",
    "copyLiveSampleBtn",
    "liveLogList",
    "canFrameCount",
    "canLastId",
    "canSignalFrameId",
    "canSignalName",
    "canSignalStartByte",
    "canSignalLength",
    "canSignalStartBit",
    "canSignalBitLength",
    "canSignalScale",
    "canSignalOffset",
    "saveCanSignalBtn",
    "canSummaryList",
    "canFrameList",
    "canDecodedPreview",
    "obdAdapterIdentity",
    "obdProtocol",
    "obdSupportedPids",
    "obdDtcList",
    "obdLastRequest",
    "obdLastResponse",
    "obdProbeCommand",
    "addObdProbeBtn",
    "obdRecordList",
    "categoryTabs",
    "paletteSearch",
    "paletteButtons",
    "previewFrame",
    "previewStage",
    "previewImage",
    "dragGhost",
    "selectionOverlay",
    "canvasMeta",
    "statusText",
    "pixelStatus",
    "zoomFitBtn",
    "deleteBtn",
    "selectedLabel",
    "propertyForm",
    "validationDrawer",
    "validationCloseBtn",
    "validationMessages",
    "frontBtn",
    "backBtn",
    "duplicateBtn",
    "layerCount",
    "layerList",
  ];

  function bindDom(dom, documentRef) {
    for (const id of DOM_IDS) {
      dom[id] = documentRef.getElementById(id);
    }
    return dom;
  }

  function bindActions(dom, windowRef, state, handlers) {
    dom.openBtn.addEventListener("click", handlers.openLayout);
    dom.saveBtn.addEventListener("click", () => handlers.saveLayout(false));
    dom.saveAsBtn.addEventListener("click", () => handlers.saveLayout(true));
    dom.undoBtn.addEventListener("click", handlers.undo);
    dom.redoBtn.addEventListener("click", handlers.redo);
    dom.resetBtn.addEventListener("click", handlers.resetDefaultLayout);
    dom.validateBtn.addEventListener("click", handlers.validateLayout);
    dom.exportPngBtn.addEventListener("click", handlers.exportSnapshot);
    dom.fieldPackBtn.addEventListener("click", handlers.exportFieldPack);
    dom.vehicleSelect.addEventListener("change", handlers.onVehicleChange);
    dom.screenSelect.addEventListener("change", handlers.onScreenChange);
    dom.importScreenBtn.addEventListener("click", handlers.importOtherScreen);
    dom.languageSelect.addEventListener("change", handlers.onLanguageChange);
    dom.simulationToggle.addEventListener("change", handlers.onSimulationToggle);
    dom.weatherBtn.addEventListener("click", handlers.fetchWeather);
    dom.backgroundColor.addEventListener("input", handlers.onBackgroundColor);
    dom.backgroundImageBtn.addEventListener("click", handlers.chooseBackgroundImage);
    dom.clearBackgroundBtn.addEventListener("click", handlers.clearBackgroundImage);
    dom.elementsTab.addEventListener("click", () => handlers.selectToolTab("elements"));
    dom.connectionTab.addEventListener("click", () => handlers.selectToolTab("connection"));
    dom.canAnalysisTab.addEventListener("click", () => handlers.selectToolTab("can"));
    dom.obdAnalysisTab.addEventListener("click", () => handlers.selectToolTab("obd"));
    dom.scanObdBtn.addEventListener("click", handlers.scanObdBle);
    dom.obdDeviceList.addEventListener("click", (event) => {
      const row = event.target?.closest?.("[data-obd-address]");
      const address = row?.dataset?.obdAddress;
      if (address) {
        handlers.selectObdDevice(address);
      }
    });
    dom.inspectObdBtn.addEventListener("click", handlers.inspectObdBle);
    dom.scanComPortsBtn.addEventListener("click", handlers.scanComPorts);
    dom.comPortList.addEventListener("click", (event) => {
      const row = event.target?.closest?.("[data-com-port]");
      const device = row?.dataset?.comPort;
      if (device) {
        handlers.selectComPort(device);
      }
    });
    dom.startVehicleLiveBtn.addEventListener("click", handlers.startVehicleLive);
    dom.stopVehicleLiveBtn.addEventListener("click", handlers.stopVehicleLive);
    dom.copyLiveSampleBtn.addEventListener("click", handlers.copyLiveSample);
    dom.saveCanSignalBtn.addEventListener("click", handlers.saveCanSignal);
    dom.addObdProbeBtn.addEventListener("click", handlers.addObdProbeCommand);
    dom.paletteSearch.addEventListener("input", () => {
      state.paletteQuery = dom.paletteSearch.value.trim().toLowerCase();
      handlers.renderPalette();
    });
    dom.validationCloseBtn.addEventListener("click", handlers.hideValidationDrawer);
    dom.deleteBtn.addEventListener("click", handlers.deleteSelected);
    dom.duplicateBtn.addEventListener("click", handlers.duplicateSelected);
    dom.frontBtn.addEventListener("click", () => handlers.bumpZ(1));
    dom.backBtn.addEventListener("click", () => handlers.bumpZ(-1));
    dom.zoomFitBtn.addEventListener("click", handlers.renderOverlay);
    dom.selectionOverlay.addEventListener("pointerdown", handlers.onPointerDown);
    windowRef.addEventListener("pointermove", handlers.onPointerMove);
    windowRef.addEventListener("pointerup", handlers.onPointerUp);
    windowRef.addEventListener("resize", handlers.renderOverlay);
    windowRef.addEventListener("keydown", handlers.onKeyDown);
  }

  const api = {
    DOM_IDS,
    bindActions,
    bindDom,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorDomBindings = api;
})(typeof window !== "undefined" ? window : globalThis);
