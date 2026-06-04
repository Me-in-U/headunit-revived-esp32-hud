(function exposeEditorVehicleLiveActions(globalScope) {
  function onSimulationToggleCommand(state, checked, deps) {
    state.simulationEnabled = Boolean(checked);
    deps.renderVehicleTools();
    deps.schedulePreview(30);
    deps.setStatus(state.simulationEnabled ? "Simulation mode enabled" : "Simulation mode disabled", "ok");
  }

  function selectToolTabCommand(state, tab, deps) {
    state.vehicleLive.activeTab = tab;
    deps.renderVehicleTools();
  }

  async function scanObdBleCommand(state, service, deps) {
    state.vehicleLive.obdConnectState = "scanning";
    deps.renderVehicleTools();
    const result = await service.scanObdBle({ timeoutSeconds: 5 });
    state.vehicleLive.obdDevices = result.devices || [];
    state.vehicleLive.obdConnectState = result.ok ? "idle" : "error";
    state.vehicleLive.lastError = (result.errors || []).join("\n");
    deps.renderVehicleTools();
    deps.setStatus(result.ok ? `Found ${state.vehicleLive.obdDevices.length} BLE devices` : state.vehicleLive.lastError, result.ok ? "ok" : "error");
    return result;
  }

  async function scanComPortsCommand(state, service, deps) {
    state.vehicleLive.comPortScanState = "scanning";
    state.vehicleLive.comPortLastError = "";
    deps.renderVehicleTools();
    const result = await service.listComPorts();
    state.vehicleLive.comPorts = deps.vehicleLiveState.sortedComPorts(result.ports || []);
    state.vehicleLive.comPortScanState = result.ok ? "idle" : "error";
    state.vehicleLive.comPortLastError = (result.errors || []).join("\n");
    deps.renderVehicleTools();
    deps.setStatus(result.ok ? `Found ${state.vehicleLive.comPorts.length} COM ports` : state.vehicleLive.comPortLastError, result.ok ? "ok" : "error");
    return result;
  }

  function selectComPortCommand(state, device, dom, deps) {
    const port = findComPort(state.vehicleLive, device) || { device, description: "" };
    deps.vehicleLiveState.setSelectedComPort(state.vehicleLive, port);
    dom.canEnabled.checked = true;
    dom.canChannel.value = canChannelForPort(port);
    deps.renderVehicleTools();
    deps.setStatus(`Selected ${dom.canChannel.value}`, "ok");
    return port;
  }

  async function selectObdDeviceAndConnectCommand(state, service, address, dom, deps) {
    const device = findObdDevice(state.vehicleLive, address) || { address, name: address };
    deps.vehicleLiveState.setSelectedObdDevice(state.vehicleLive, device);
    deps.vehicleLiveState.setSelectedObdPair(state.vehicleLive, null);
    state.vehicleLive.obdConnectState = "inspecting";
    state.vehicleLive.lastError = "";
    deps.renderVehicleTools();

    const inspection = await service.inspectObdBle({ mac: address, timeoutSeconds: 5 });
    state.vehicleLive.obdInspection = inspection;
    const pair = Array.isArray(inspection.pairs) && inspection.pairs.length ? inspection.pairs[0] : null;
    if (!inspection.ok || !pair) {
      state.vehicleLive.obdConnectState = "error";
      state.vehicleLive.lastError = (inspection.errors || []).join("\n") || "No notify/write BLE characteristic pair found";
      deps.renderVehicleTools();
      deps.setStatus(state.vehicleLive.lastError, "error");
      return { ok: false, inspection };
    }

    deps.vehicleLiveState.setSelectedObdPair(state.vehicleLive, pair);
    fillObdConfig(dom, address, pair);
    if (!String(dom.canChannel.value || "").trim()) {
      dom.canEnabled.checked = false;
    }
    state.vehicleLive.obdConnectState = "connecting";
    deps.renderVehicleTools();

    const live = await service.startVehicleLive(buildVehicleLiveConfig(state, dom));
    state.vehicleLive.running = Boolean(live.ok);
    state.vehicleLive.obdConnectState = live.ok ? "connected" : "error";
    state.vehicleLive.lastError = live.ok ? "" : (live.errors || []).join("\n");
    deps.renderVehicleTools();
    deps.setStatus(live.ok ? `Connected to ${deviceLabel(device)}` : state.vehicleLive.lastError, live.ok ? "ok" : "error");
    return { ok: Boolean(live.ok), inspection, live };
  }

  async function inspectObdBleCommand(state, service, mac, deps) {
    const result = await service.inspectObdBle({ mac, timeoutSeconds: 5 });
    state.vehicleLive.obdInspection = result;
    if (result.ok && Array.isArray(result.pairs) && result.pairs.length) {
      deps.vehicleLiveState.setSelectedObdPair(state.vehicleLive, result.pairs[0]);
    }
    deps.renderVehicleTools();
    deps.setStatus(result.ok ? "OBD BLE characteristics ready" : (result.errors || []).join("\n"), result.ok ? "ok" : "error");
    return result;
  }

  async function startVehicleLiveCommand(state, service, config, deps) {
    const result = await service.startVehicleLive(config);
    state.vehicleLive.running = Boolean(result.ok);
    deps.renderVehicleTools();
    deps.setStatus(result.ok ? "Vehicle live worker started" : (result.errors || []).join("\n"), result.ok ? "ok" : "error");
    return result;
  }

  async function stopVehicleLiveCommand(state, service, deps) {
    const result = await service.stopVehicleLive();
    state.vehicleLive.running = false;
    deps.renderVehicleTools();
    deps.setStatus("Vehicle live worker stopped", "ok");
    return result;
  }

  function handleVehicleLiveEventCommand(state, event, deps) {
    if (!deps.vehicleLiveState.mergeVehicleLiveEvent(state.vehicleLive, event)) {
      return false;
    }
    deps.renderVehicleTools();
    if (event.type === "state" && state.simulationEnabled) {
      deps.schedulePreview(30);
    }
    return true;
  }

  function copyLiveSampleCommand(state, deps) {
    const mergedState = state.vehicleLive?.mergedState || {};
    if (!state.layout || !Object.keys(mergedState).length) {
      deps.setStatus("No live sample to copy", "error");
      return false;
    }
    deps.recordHistory();
    deps.vehicleLiveState.copyLiveSampleToDummyData(state);
    deps.markDirty();
    deps.renderAll();
    deps.schedulePreview(30);
    deps.setStatus("Live sample copied to dummy data", "ok");
    return true;
  }

  function saveCanSignalCommand(state, signal, deps) {
    if (!deps.vehicleLiveState.selectedVehicle(state.layout) || !signal?.frame_id || !signal?.name) {
      deps.setStatus("CAN signal requires frame ID and state path", "error");
      return false;
    }
    deps.recordHistory();
    deps.vehicleLiveState.upsertConfirmedCanSignal(state, signal);
    deps.markDirty();
    deps.renderVehicleTools();
    deps.setStatus("Confirmed CAN signal saved to vehicle profile", "ok");
    return true;
  }

  function addObdProbeCommand(state, commandText, deps) {
    const commands = String(commandText || "")
      .split(/[,\r\n]+/)
      .map((item) => item.trim())
      .filter(Boolean);
    if (!deps.vehicleLiveState.selectedVehicle(state.layout) || !commands.length) {
      deps.setStatus("OBD probe command is empty", "error");
      return false;
    }
    deps.recordHistory();
    deps.vehicleLiveState.addObdProbeCommand(state, commandText);
    deps.markDirty();
    deps.renderVehicleTools();
    deps.setStatus("OBD probe command added to vehicle profile", "ok");
    return true;
  }

  function buildVehicleLiveConfig(state, dom) {
    return {
      layout: state.layout,
      obd: {
        enabled: Boolean(dom.obdEnabled.checked),
        mac: dom.obdBleMac.value.trim(),
        rxUuid: dom.obdBleRxUuid.value.trim(),
        txUuid: dom.obdBleTxUuid.value.trim(),
        timeoutSeconds: Number.parseFloat(dom.obdTimeout.value) || 2,
      },
      can: {
        enabled: Boolean(dom.canEnabled.checked && dom.canChannel.value.trim()),
        interface: "slcan",
        channel: dom.canChannel.value.trim(),
        bitrate: Number.parseInt(dom.canBitrate.value, 10) || 500000,
        listenOnly: Boolean(dom.canListenOnly.checked),
      },
    };
  }

  function findObdDevice(vehicleLive, address) {
    return (vehicleLive.obdDevices || []).find((device) => device.address === address) || null;
  }

  function findComPort(vehicleLive, deviceName) {
    return (vehicleLive.comPorts || []).find((port) => port.device === deviceName) || null;
  }

  function canChannelForPort(port) {
    const device = String(port?.device || "").trim();
    if (!device) {
      return "";
    }
    return device.includes("@") ? device : `${device}@115200`;
  }

  function fillObdConfig(dom, address, pair) {
    dom.obdEnabled.checked = true;
    dom.obdBleMac.value = address;
    dom.obdBleRxUuid.value = pair.rx_uuid || pair.rxUuid || "";
    dom.obdBleTxUuid.value = pair.tx_uuid || pair.txUuid || "";
  }

  function deviceLabel(device) {
    return device?.name ? `${device.name} (${device.address})` : String(device?.address || "OBD BLE adapter");
  }

  const api = {
    addObdProbeCommand,
    buildVehicleLiveConfig,
    copyLiveSampleCommand,
    handleVehicleLiveEventCommand,
    inspectObdBleCommand,
    onSimulationToggleCommand,
    saveCanSignalCommand,
    scanComPortsCommand,
    selectObdDeviceAndConnectCommand,
    selectComPortCommand,
    scanObdBleCommand,
    selectToolTabCommand,
    startVehicleLiveCommand,
    stopVehicleLiveCommand,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorVehicleLiveActions = api;
})(typeof window !== "undefined" ? window : globalThis);
