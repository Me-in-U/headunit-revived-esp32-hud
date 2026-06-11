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
    "obdSerialPort",
    "obdSerialBaud",
    "obdBleMac",
    "obdBleRxUuid",
    "obdBleTxUuid",
    "obdTimeout",
    "scanObdComPortsBtn",
    "scanObdBtn",
    "obdSerialPortList",
    "obdDeviceList",
    "obdSelectedStatus",
    "obdAdvancedSettings",
    "startObdLiveBtn",
    "stopObdLiveBtn",
    "inspectObdBtn",
    "obdConnectionStatus",
    "obdAnalysisStatus",
    "canEnabled",
    "scanComPortsBtn",
    "comPortList",
    "comSelectedStatus",
    "canChannel",
    "canBitrate",
    "canListenOnly",
    "startCanLiveBtn",
    "stopCanLiveBtn",
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
    "obdPidCommand",
    "obdPidLabel",
    "obdPidReferenceValue",
    "obdPidUnit",
    "obdPidPath",
    "obdPidByteIndex",
    "obdPidLength",
    "obdPidScale",
    "obdPidOffset",
    "obdPidEndian",
    "obdPidSigned",
    "saveObdPidBtn",
    "obdValueList",
    "obdRecordList",
    "categoryTabs",
    "paletteSearch",
    "paletteButtons",
    "previewFrame",
    "previewStage",
    "previewImage",
    "dragGhost",
    "selectionOverlay",
    "canvasPanel",
    "toggleCanvasBtn",
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
    dom.scanObdComPortsBtn.addEventListener("click", handlers.scanObdComPorts);
    dom.obdSerialPortList.addEventListener("click", (event) => {
      const row = event.target?.closest?.("[data-obd-serial-port]");
      const device = row?.dataset?.obdSerialPort;
      if (device) {
        handlers.selectObdSerialPort(device);
      }
    });
    dom.obdDeviceList.addEventListener("click", (event) => {
      const row = event.target?.closest?.("[data-obd-address]");
      const address = row?.dataset?.obdAddress;
      if (address) {
        handlers.selectObdDevice(address);
      }
    });
    dom.inspectObdBtn.addEventListener("click", handlers.inspectObdBle);
    dom.startObdLiveBtn.addEventListener("click", handlers.startObdLive);
    dom.stopObdLiveBtn.addEventListener("click", handlers.stopObdLive);
    dom.scanComPortsBtn.addEventListener("click", handlers.scanComPorts);
    dom.comPortList.addEventListener("click", (event) => {
      const row = event.target?.closest?.("[data-com-port]");
      const device = row?.dataset?.comPort;
      if (device) {
        handlers.selectCanPort(device);
      }
    });
    dom.startCanLiveBtn.addEventListener("click", handlers.startCanLive);
    dom.stopCanLiveBtn.addEventListener("click", handlers.stopCanLive);
    dom.copyLiveSampleBtn.addEventListener("click", handlers.copyLiveSample);
    dom.saveCanSignalBtn.addEventListener("click", handlers.saveCanSignal);
    dom.addObdProbeBtn.addEventListener("click", handlers.addObdProbeCommand);
    dom.saveObdPidBtn.addEventListener("click", handlers.saveObdPidDefinition);
    dom.obdValueList.addEventListener("click", (event) => {
      const defineButton = event.target?.closest?.("[data-obd-define-pid]");
      const command = defineButton?.dataset?.obdDefinePid;
      if (command && !defineButton.disabled) {
        handlers.editObdPidDefinition({
          command,
          label: defineButton.dataset?.obdLabel || "",
          unit: defineButton.dataset?.obdUnit || "",
          path: defineButton.dataset?.obdPath || "",
          rawBytes: defineButton.dataset?.obdRawBytes || "",
        });
        return;
      }
      const button = event.target?.closest?.("[data-obd-binding]");
      const binding = button?.dataset?.obdBinding;
      if (binding && !button.disabled) {
        handlers.assignObdBinding(binding, button.dataset?.obdLabel || "");
      }
    });
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
    dom.toggleCanvasBtn.addEventListener("click", () => toggleCanvasPanel(dom));
    dom.selectionOverlay.addEventListener("pointerdown", handlers.onPointerDown);
    windowRef.addEventListener("pointermove", handlers.onPointerMove);
    windowRef.addEventListener("pointerup", handlers.onPointerUp);
    windowRef.addEventListener("resize", handlers.renderOverlay);
    windowRef.addEventListener("keydown", handlers.onKeyDown);
  }

  function toggleCanvasPanel(dom) {
    const collapsed = !String(dom.canvasPanel.className || "").split(/\s+/).includes("is-collapsed");
    setCanvasPanelCollapsed(dom, collapsed);
  }

  function setCanvasPanelCollapsed(dom, collapsed) {
    if (dom.canvasPanel.classList?.toggle) {
      dom.canvasPanel.classList.toggle("is-collapsed", collapsed);
    } else {
      const classNames = new Set(String(dom.canvasPanel.className || "").split(/\s+/).filter(Boolean));
      if (collapsed) {
        classNames.add("is-collapsed");
      } else {
        classNames.delete("is-collapsed");
      }
      dom.canvasPanel.className = [...classNames].join(" ");
    }
    dom.toggleCanvasBtn.textContent = collapsed ? "Canvas 펼치기" : "Canvas 접기";
    dom.toggleCanvasBtn.setAttribute?.("aria-expanded", collapsed ? "false" : "true");
  }

  const api = {
    DOM_IDS,
    bindActions,
    bindDom,
    setCanvasPanelCollapsed,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorDomBindings = api;
})(typeof window !== "undefined" ? window : globalThis);
