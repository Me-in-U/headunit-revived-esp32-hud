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
      await modules.vehicleLiveActions.scanComPortsCommand(state, hudEditor(), deps("vehicleLiveActionDeps"));
    }

    function selectComPort(device) {
      modules.vehicleLiveActions.selectComPortCommand(state, device, dom, deps("vehicleLiveActionDeps"));
    }

    async function selectObdDevice(address) {
      await modules.vehicleLiveActions.selectObdDeviceAndConnectCommand(state, hudEditor(), address, dom, deps("vehicleLiveActionDeps"));
    }

    async function inspectObdBle() {
      await modules.vehicleLiveActions.inspectObdBleCommand(state, hudEditor(), dom.obdBleMac.value.trim(), deps("vehicleLiveActionDeps"));
    }

    async function startVehicleLive() {
      await modules.vehicleLiveActions.startVehicleLiveCommand(
        state,
        hudEditor(),
        modules.vehicleLiveActions.buildVehicleLiveConfig(state, dom),
        deps("vehicleLiveActionDeps")
      );
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
      scanComPorts,
      scanObdBle,
      selectComPort,
      selectObdDevice,
      selectToolTab,
      startVehicleLive,
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
