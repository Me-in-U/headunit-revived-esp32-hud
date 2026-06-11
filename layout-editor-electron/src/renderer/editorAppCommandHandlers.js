(function exposeEditorAppCommandHandlers(globalScope) {
  function createAppCommandHandlers({ state, dom, modules, refs, runtimeFactory, selectedElement }) {
    function deps(factoryName) {
      return modules.appDeps[factoryName](runtimeFactory());
    }

    function hudEditor() {
      return refs.windowRef.hudEditor;
    }

    function applyLoadedLayout(response) {
      return modules.fileCommands.applyLoadedLayoutCommand(state, response, deps("fileCommandDeps"));
    }

    async function openLayout() {
      await modules.fileCommands.openLayoutCommand(state, hudEditor(), deps("fileCommandDeps"));
    }

    async function resetDefaultLayout() {
      await modules.fileCommands.resetDefaultLayoutCommand(state, hudEditor(), deps("fileCommandDeps"));
    }

    async function saveLayout(saveAs) {
      await modules.fileCommands.saveLayoutCommand(state, saveAs, hudEditor(), deps("fileCommandDeps"));
    }

    function duplicateSelected() {
      modules.commandActions.duplicateSelected(state, deps("commandActionDeps"));
    }

    async function validateLayout() {
      await modules.fileCommands.validateLayoutCommand(state, hudEditor(), deps("fileCommandDeps"));
    }

    async function exportSnapshot() {
      await modules.fileCommands.exportSnapshotCommand(state, hudEditor(), deps("fileCommandDeps"));
    }

    async function exportFieldPack() {
      await modules.fileCommands.exportFieldPackCommand(state, hudEditor(), deps("fileCommandDeps"));
    }

    async function fetchWeather() {
      await modules.weatherActions.fetchWeatherCommand(state, hudEditor(), refs.navigatorRef, deps("weatherActionDeps"));
    }

    function onSimulationToggle() {
      modules.vehicleLiveActions.onSimulationToggleCommand(state, dom.simulationToggle.checked, deps("vehicleLiveActionDeps"));
    }

    function selectToolTab(tab) {
      modules.vehicleLiveActions.selectToolTabCommand(state, tab, deps("vehicleLiveActionDeps"));
    }

    async function scanObdBle() {
      await modules.vehicleLiveActions.scanObdBleCommand(state, hudEditor(), deps("vehicleLiveActionDeps"));
    }

    async function scanComPorts() {
      await modules.vehicleLiveActions.scanComPortsCommand(state, hudEditor(), dom, deps("vehicleLiveActionDeps"), {
        target: "can",
        autoFillObdSerial: false,
      });
    }

    async function scanObdComPorts() {
      await modules.vehicleLiveActions.scanComPortsCommand(state, hudEditor(), dom, deps("vehicleLiveActionDeps"), {
        target: "obd",
        autoFillObdSerial: true,
      });
    }

    function selectComPort(device) {
      modules.vehicleLiveActions.selectComPortCommand(state, device, dom, deps("vehicleLiveActionDeps"));
    }

    function selectCanPort(device) {
      modules.vehicleLiveActions.selectCanPortCommand(state, device, dom, deps("vehicleLiveActionDeps"));
    }

    function selectObdSerialPort(device) {
      modules.vehicleLiveActions.selectObdSerialPortCommand(state, device, dom, deps("vehicleLiveActionDeps"));
    }

    async function selectObdDevice(address) {
      await modules.vehicleLiveActions.selectObdDeviceAndConnectCommand(state, hudEditor(), address, dom, deps("vehicleLiveActionDeps"));
    }

    async function inspectObdBle() {
      await modules.vehicleLiveActions.inspectObdBleCommand(state, hudEditor(), dom.obdBleMac.value.trim(), deps("vehicleLiveActionDeps"));
    }

    async function startVehicleLive() {
      await startConfiguredInputs({
        obd: Boolean(dom.obdEnabled.checked),
        can: Boolean(dom.canEnabled.checked),
      });
    }

    async function startObdLive() {
      await startConfiguredInputs({ obd: true, can: desiredInput("can") });
    }

    async function startCanLive() {
      await startConfiguredInputs({ obd: desiredInput("obd"), can: true });
    }

    async function stopObdLive() {
      await stopConfiguredInput("obd");
    }

    async function stopCanLive() {
      await stopConfiguredInput("can");
    }

    async function startConfiguredInputs(enabledSources) {
      let nextSources = { ...enabledSources };
      state.vehicleLive.desiredInputs = { ...state.vehicleLive.desiredInputs, ...nextSources };
      modules.vehicleLiveActions.prepareVehicleLiveDomForStart(state, dom);
      const blockedStatuses = [];
      if (nextSources.obd) {
        const obdReady = await ensureObdInputReady();
        if (!obdReady.ok) {
          nextSources = { ...nextSources, obd: false };
          state.vehicleLive.desiredInputs = { ...state.vehicleLive.desiredInputs, obd: false };
          blockedStatuses.push({ source: "obd", detail: obdReady.detail });
        }
      }
      if (!nextSources.obd && !nextSources.can) {
        for (const blocked of blockedStatuses) {
          emitLocalStatus(blocked.source, "error", blocked.detail);
        }
        return;
      }
      modules.vehicleLiveActions.prepareVehicleLiveDomForStart(state, dom);
      await modules.vehicleLiveActions.startVehicleLiveCommand(
        state,
        hudEditor(),
        modules.vehicleLiveActions.buildVehicleLiveConfig(state, dom, { enabledSources: nextSources }),
        deps("vehicleLiveActionDeps")
      );
      for (const blocked of blockedStatuses) {
        emitLocalStatus(blocked.source, "error", blocked.detail);
      }
    }

    async function ensureObdInputReady() {
      if (!shouldValidateObdSerial()) {
        return { ok: true, detail: "" };
      }
      const originalPort = dom.obdSerialPort.value.trim();
      await modules.vehicleLiveActions.scanComPortsCommand(state, hudEditor(), dom, deps("vehicleLiveActionDeps"), {
        target: "obd",
        autoFillObdSerial: !originalPort,
      });
      const selectedPort = dom.obdSerialPort.value.trim();
      if (!selectedPort) {
        return {
          ok: false,
          detail:
            "사용 가능한 OBD Classic Bluetooth COM 포트가 없습니다. Windows Bluetooth 설정에서 PIN 1234로 Android-vlink를 페어링한 뒤 OBD COM 새로고침을 누르세요.",
        };
      }
      if (hasAvailableObdPort(selectedPort)) {
        return { ok: true, detail: "" };
      }
      const fallbackPort = (state.vehicleLive.obdComPorts || [])[0];
      if (fallbackPort?.device) {
        modules.vehicleLiveActions.selectObdSerialPortCommand(
          state,
          fallbackPort.device,
          dom,
          deps("vehicleLiveActionDeps")
        );
        return { ok: true, detail: "" };
      }
      return {
        ok: false,
        detail: `OBD 시리얼 ${selectedPort}이 현재 Windows COM 목록에 없습니다. PIN 1234로 Android-vlink를 페어링한 뒤 OBD COM 새로고침을 누르세요.`,
      };
    }

    function hasAvailableObdPort(port) {
      const wanted = normalizeDeviceName(port);
      return (state.vehicleLive.obdComPorts || []).some((item) => normalizeDeviceName(item.device) === wanted);
    }

    function shouldValidateObdSerial() {
      if (dom.obdSerialPort.value.trim()) {
        return true;
      }
      return Boolean(
        !dom.obdBleMac.value.trim() &&
          !dom.obdBleRxUuid.value.trim() &&
          !dom.obdBleTxUuid.value.trim()
      );
    }

    function emitLocalStatus(source, statusState, detail) {
      modules.vehicleLiveActions.handleVehicleLiveEventCommand(
        state,
        { type: "status", source, state: statusState, detail, updatedAt: new Date().toISOString() },
        deps("vehicleLiveActionDeps")
      );
      deps("vehicleLiveActionDeps").setStatus(detail, statusState === "error" ? "error" : "ok");
    }

    function normalizeDeviceName(device) {
      return String(device || "").trim().toUpperCase();
    }

    async function stopConfiguredInput(source) {
      const nextSources = {
        obd: desiredInput("obd"),
        can: desiredInput("can"),
        [source]: false,
      };
      state.vehicleLive.desiredInputs = nextSources;
      if (nextSources.obd || nextSources.can) {
        await startConfiguredInputs(nextSources);
        return;
      }
      await modules.vehicleLiveActions.stopVehicleLiveCommand(state, hudEditor(), deps("vehicleLiveActionDeps"));
    }

    function desiredInput(source) {
      return Boolean(state.vehicleLive?.desiredInputs?.[source]);
    }

    async function stopVehicleLive() {
      await modules.vehicleLiveActions.stopVehicleLiveCommand(state, hudEditor(), deps("vehicleLiveActionDeps"));
    }

    function onVehicleLiveEvent(event) {
      modules.vehicleLiveActions.handleVehicleLiveEventCommand(state, event, deps("vehicleLiveActionDeps"));
    }

    function copyLiveSample() {
      modules.vehicleLiveActions.copyLiveSampleCommand(state, deps("vehicleLiveActionDeps"));
    }

    function saveCanSignal() {
      modules.vehicleLiveActions.saveCanSignalCommand(
        state,
        {
          frame_id: dom.canSignalFrameId.value.trim(),
          name: dom.canSignalName.value.trim(),
          start_byte: dom.canSignalStartByte.value,
          start_bit: dom.canSignalStartBit.value,
          bit_length: dom.canSignalBitLength.value,
          length: dom.canSignalLength.value,
          scale: dom.canSignalScale.value,
          offset: dom.canSignalOffset.value,
        },
        deps("vehicleLiveActionDeps")
      );
    }

    function addObdProbeCommand() {
      modules.vehicleLiveActions.addObdProbeCommand(state, dom.obdProbeCommand.value, deps("vehicleLiveActionDeps"));
    }

    function editObdPidDefinition(row) {
      modules.vehicleLiveActions.editObdPidDefinitionCommand(dom, row, deps("vehicleLiveActionDeps"));
    }

    function saveObdPidDefinition() {
      modules.vehicleLiveActions.saveObdPidDefinitionCommand(
        state,
        {
          command: dom.obdPidCommand.value.trim(),
          label: dom.obdPidLabel.value.trim(),
          referenceValue: dom.obdPidReferenceValue.value.trim(),
          unit: dom.obdPidUnit.value.trim(),
          path: dom.obdPidPath.value.trim(),
          byteIndex: dom.obdPidByteIndex.value,
          byteLength: dom.obdPidLength.value,
          scale: dom.obdPidScale.value,
          offset: dom.obdPidOffset.value,
          endian: dom.obdPidEndian.value,
          signed: dom.obdPidSigned.checked,
        },
        deps("vehicleLiveActionDeps")
      );
    }

    function assignObdBinding(binding, label) {
      modules.vehicleLiveActions.assignObdBindingCommand(
        state,
        binding,
        selectedElement(),
        deps("vehicleLiveActionDeps"),
        label
      );
    }

    function onVehicleChange() {
      modules.contextCommands.applyVehicleCommand(state, dom.vehicleSelect.value, deps("contextCommandDeps"));
    }

    function onScreenChange() {
      modules.contextCommands.applyScreenCommand(state, dom.screenSelect.value, deps("contextCommandDeps"));
    }

    function importOtherScreen() {
      modules.contextCommands.importOtherScreenCommand(state, deps("contextCommandDeps"));
    }

    function onLanguageChange() {
      modules.contextCommands.applyLanguageCommand(state, dom.languageSelect.value, deps("contextCommandDeps"));
    }

    function onBackgroundColor() {
      modules.backgroundActions.applyBackgroundColorCommand(state, dom.backgroundColor.value, deps("backgroundActionDeps"));
    }

    async function chooseBackgroundImage() {
      await modules.backgroundActions.chooseBackgroundImageCommand(state, hudEditor(), deps("backgroundActionDeps"));
    }

    function clearBackgroundImage() {
      modules.backgroundActions.clearBackgroundImageCommand(state, deps("backgroundActionDeps"));
    }

    function onPropertyInput(event) {
      modules.editActions.handlePropertyInput(state, dom, event, selectedElement, deps("editActionDeps"));
    }

    function onPointerDown(event) {
      modules.pointerActions.handlePointerDown(state, dom, event, deps("pointerActionDeps"));
    }

    function onPointerMove(event) {
      modules.pointerActions.handlePointerMove(state, dom, event, deps("pointerActionDeps"));
    }

    function onPointerUp() {
      modules.pointerActions.handlePointerUp(state, dom, deps("pointerActionDeps"));
    }

    function onKeyDown(event) {
      modules.commandActions.handleKeyDown(state, event, deps("commandActionDeps"));
    }

    function deleteSelected() {
      modules.commandActions.deleteSelected(state, deps("commandActionDeps"));
    }

    function bumpZ(delta) {
      modules.commandActions.bumpZ(state, delta, deps("commandActionDeps"));
    }

    function markDirty() {
      modules.historyCommands.markDirtyCommand(state, deps("historyCommandDeps"));
    }

    function snapshotState() {
      return modules.historyCommands.snapshotStateCommand(state, deps("historyCommandDeps"));
    }

    function recordHistory() {
      return modules.historyCommands.recordHistoryCommand(state, deps("historyCommandDeps"));
    }

    function pushUndoSnapshot(snapshot) {
      modules.historyCommands.pushUndoSnapshotCommand(state, snapshot, deps("historyCommandDeps"));
    }

    function undo() {
      modules.historyCommands.undoCommand(state, deps("historyCommandDeps"));
    }

    function redo() {
      modules.historyCommands.redoCommand(state, deps("historyCommandDeps"));
    }

    return {
      applyLoadedLayout,
      bumpZ,
      chooseBackgroundImage,
      clearBackgroundImage,
      deleteSelected,
      duplicateSelected,
      exportFieldPack,
      exportSnapshot,
      fetchWeather,
      addObdProbeCommand,
      assignObdBinding,
      editObdPidDefinition,
      importOtherScreen,
      markDirty,
      onBackgroundColor,
      onKeyDown,
      onLanguageChange,
      onSimulationToggle,
      onVehicleLiveEvent,
      onPointerDown,
      onPointerMove,
      onPointerUp,
      onPropertyInput,
      onScreenChange,
      onVehicleChange,
      openLayout,
      pushUndoSnapshot,
      recordHistory,
      redo,
      resetDefaultLayout,
      saveLayout,
      saveCanSignal,
      saveObdPidDefinition,
      scanComPorts,
      scanObdComPorts,
      scanObdBle,
      selectCanPort,
      selectComPort,
      selectObdDevice,
      selectObdSerialPort,
      selectToolTab,
      startCanLive,
      startObdLive,
      startVehicleLive,
      stopCanLive,
      stopObdLive,
      stopVehicleLive,
      snapshotState,
      undo,
      validateLayout,
    };
  }

  const api = {
    createAppCommandHandlers,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorAppCommandHandlers = api;
})(typeof window !== "undefined" ? window : globalThis);
