(function exposeEditorVehicleLiveState(globalScope) {
  function createVehicleLiveState() {
    return {
      activeTab: "elements",
      status: {
        obd: { state: "idle", detail: "", updatedAt: "" },
        can: { state: "idle", detail: "", updatedAt: "" },
      },
      desiredInputs: { obd: false, can: false },
      mergedState: {},
      canFrames: [],
      canSummary: { frame_count: 0, unique_id_count: 0, ids: [] },
      comPorts: [],
      obdComPorts: [],
      canComPorts: [],
      lastObdComScanSummary: "",
      lastCanComScanSummary: "",
      selectedComPort: null,
      selectedCanPort: null,
      selectedObdSerialPort: null,
      comPortScanState: "idle",
      comPortLastError: "",
      obdComPortScanState: "idle",
      obdComPortLastError: "",
      canComPortScanState: "idle",
      canComPortLastError: "",
      obdRecords: [],
      obdDevices: [],
      selectedObdDevice: null,
      selectedObdPair: null,
      obdConnectState: "idle",
      obdInspection: null,
      lastError: "",
      running: false,
    };
  }

  function mergeVehicleLiveEvent(vehicleLive, event) {
    if (!event || typeof event !== "object") {
      return false;
    }
    if (event.type === "status" && event.source) {
      vehicleLive.status[event.source] = {
        state: event.state || "idle",
        detail: event.detail || "",
        updatedAt: event.updatedAt || "",
      };
      vehicleLive.running = Object.values(vehicleLive.status).some((item) => item.state === "connecting" || item.state === "live");
      if (event.state === "error") {
        vehicleLive.lastError = event.detail || "";
      }
      return true;
    }
    if (event.type === "state") {
      vehicleLive.mergedState = clone(event.mergedState || mergeObjects(vehicleLive.mergedState, event.update || {}));
      return true;
    }
    if (event.type === "can_frame" && event.record) {
      vehicleLive.canFrames.unshift(clone(event.record));
      vehicleLive.canFrames = vehicleLive.canFrames.slice(0, 50);
      return true;
    }
    if (event.type === "can_summary" && event.summary) {
      vehicleLive.canSummary = clone(event.summary);
      return true;
    }
    if (event.type === "obd_record" && event.record) {
      vehicleLive.obdRecords.unshift(clone(event.record));
      vehicleLive.obdRecords = vehicleLive.obdRecords.slice(0, 300);
      return true;
    }
    return false;
  }

  function previewStateOverride(state) {
    if (!state?.simulationEnabled) {
      return null;
    }
    const mergedState = state.vehicleLive?.mergedState || {};
    return Object.keys(mergedState).length ? clone(mergedState) : null;
  }

  function copyLiveSampleToDummyData(state) {
    const mergedState = state.vehicleLive?.mergedState || {};
    if (!state.layout || !Object.keys(mergedState).length) {
      return false;
    }
    state.layout.dummy_data = mergeObjects(state.layout.dummy_data || {}, mergedState);
    return true;
  }

  function selectedVehicle(layout) {
    if (!layout || !Array.isArray(layout.vehicles)) {
      return null;
    }
    return layout.vehicles.find((vehicle) => vehicle && vehicle.id === layout.selected_vehicle) || layout.vehicles[0] || null;
  }

  function setSelectedObdDevice(vehicleLive, device) {
    vehicleLive.selectedObdDevice = device ? clone(device) : null;
    return vehicleLive.selectedObdDevice;
  }

  function setSelectedObdPair(vehicleLive, pair) {
    vehicleLive.selectedObdPair = pair ? clone(pair) : null;
    return vehicleLive.selectedObdPair;
  }

  function setSelectedComPort(vehicleLive, port) {
    vehicleLive.selectedComPort = port ? clone(port) : null;
    return vehicleLive.selectedComPort;
  }

  function setSelectedCanPort(vehicleLive, port) {
    vehicleLive.selectedCanPort = port ? clone(port) : null;
    vehicleLive.selectedComPort = vehicleLive.selectedCanPort;
    return vehicleLive.selectedCanPort;
  }

  function setSelectedObdSerialPort(vehicleLive, port) {
    vehicleLive.selectedObdSerialPort = port ? clone(port) : null;
    return vehicleLive.selectedObdSerialPort;
  }

  function sortedObdDevices(devices) {
    return (Array.isArray(devices) ? devices : [])
      .map((device, index) => ({ device, index, score: obdDeviceScore(device) }))
      .sort((left, right) => right.score - left.score || left.index - right.index)
      .map((entry) => clone(entry.device));
  }

  function sortedComPorts(ports) {
    return (Array.isArray(ports) ? ports : [])
      .map((port, index) => ({ port, index, score: comPortScore(port), number: comPortNumber(port) }))
      .sort((left, right) => right.score - left.score || left.number - right.number || left.index - right.index)
      .map((entry) => clone(entry.port));
  }

  function obdDeviceScore(device) {
    const text = `${device?.name || ""} ${device?.address || ""}`.toLowerCase();
    return /\b(elm327|icar|obd|vgate|v-link|vlink)\b/.test(text) ? 1 : 0;
  }

  function comPortScore(port) {
    const text = `${port?.device || ""} ${port?.description || ""} ${port?.hwid || ""} ${port?.manufacturer || ""} ${port?.product || ""}`.toLowerCase();
    return port?.likelyCanable || /\b(cantact|canable|candlelight|candle|slcan|usb to can|can adapter)\b/.test(text) ? 1 : 0;
  }

  function comPortNumber(port) {
    const match = String(port?.device || "").match(/^COM(\d+)$/i);
    return match ? Number.parseInt(match[1], 10) : 10000;
  }

  function upsertConfirmedCanSignal(state, signal) {
    const vehicle = selectedVehicle(state.layout);
    if (!vehicle || !signal || !signal.frame_id || !signal.name) {
      return false;
    }
    const normalized = {
      confirmed: true,
      frame_id: String(signal.frame_id).trim(),
      name: String(signal.name).trim(),
    };
    for (const key of ["start_byte", "start_bit", "bit_length", "length"]) {
      if (signal[key] !== undefined && signal[key] !== "") {
        normalized[key] = Number.parseInt(signal[key], 10);
      }
    }
    for (const key of ["scale", "offset"]) {
      if (signal[key] !== undefined && signal[key] !== "") {
        normalized[key] = Number.parseFloat(signal[key]);
      }
    }
    if (signal.endian) {
      normalized.endian = signal.endian;
    }
    if (signal.signed !== undefined) {
      normalized.signed = Boolean(signal.signed);
    }
    vehicle.can_signals = Array.isArray(vehicle.can_signals) ? vehicle.can_signals : [];
    const index = vehicle.can_signals.findIndex((item) => item.frame_id === normalized.frame_id && item.name === normalized.name);
    if (index >= 0) {
      vehicle.can_signals[index] = { ...vehicle.can_signals[index], ...normalized };
    } else {
      vehicle.can_signals.push(normalized);
    }
    return true;
  }

  function addObdProbeCommand(state, commandText) {
    const vehicle = selectedVehicle(state.layout);
    const commands = String(commandText || "")
      .split(/[,\r\n]+/)
      .map((item) => item.trim())
      .filter(Boolean);
    if (!vehicle || !commands.length) {
      return false;
    }
    vehicle.obd_probe_commands = Array.isArray(vehicle.obd_probe_commands) ? vehicle.obd_probe_commands : [];
    vehicle.obd_probe_commands.push({
      label: commands.join(" "),
      confirmed: false,
      commands,
    });
    return true;
  }

  function upsertObdPidDefinition(state, definition) {
    const vehicle = selectedVehicle(state.layout);
    const command = normalizeObdPidCommand(definition?.command || definition?.pid);
    const label = String(definition?.label || definition?.name || "").trim();
    if (!vehicle || !command || !label) {
      return false;
    }
    const normalized = {
      command,
      label,
      unit: String(definition.unit || "").trim(),
      path: String(definition.path || "").trim() || `vehicle.obd_${command.toLowerCase()}`,
      confirmed: true,
    };
    for (const [sourceKey, targetKey] of [
      ["byteIndex", "byte_index"],
      ["byte_length", "byte_length"],
      ["length", "byte_length"],
      ["byteLength", "byte_length"],
    ]) {
      if (definition[sourceKey] !== undefined && definition[sourceKey] !== "") {
        normalized[targetKey] = Number.parseInt(definition[sourceKey], 10);
      }
    }
    for (const key of ["scale", "offset"]) {
      if (definition[key] !== undefined && definition[key] !== "") {
        normalized[key] = Number.parseFloat(definition[key]);
      }
    }
    if (definition.endian) {
      normalized.endian = definition.endian;
    }
    if (definition.signed !== undefined) {
      normalized.signed = Boolean(definition.signed);
    }
    if (definition.referenceValue !== undefined && String(definition.referenceValue).trim()) {
      normalized.reference_value = String(definition.referenceValue).trim();
    }
    vehicle.obd_pid_definitions = Array.isArray(vehicle.obd_pid_definitions) ? vehicle.obd_pid_definitions : [];
    const index = vehicle.obd_pid_definitions.findIndex((item) => normalizeObdPidCommand(item.command || item.pid) === command);
    if (index >= 0) {
      vehicle.obd_pid_definitions[index] = { ...vehicle.obd_pid_definitions[index], ...normalized };
    } else {
      vehicle.obd_pid_definitions.push(normalized);
    }
    return normalized;
  }

  function normalizeObdPidCommand(value) {
    const text = String(value || "").replace(/[^0-9a-f]/gi, "").toUpperCase();
    if (text.length === 2) {
      return `01${text}`;
    }
    if (text.length === 4 && text.startsWith("01")) {
      return text;
    }
    return "";
  }

  function mergeObjects(left, right) {
    const result = clone(left || {});
    deepMerge(result, right || {});
    return result;
  }

  function deepMerge(target, source) {
    for (const [key, value] of Object.entries(source || {})) {
      if (value && typeof value === "object" && !Array.isArray(value) && target[key] && typeof target[key] === "object" && !Array.isArray(target[key])) {
        deepMerge(target[key], value);
      } else {
        target[key] = clone(value);
      }
    }
    return target;
  }

  function clone(value) {
    if (value === undefined) {
      return undefined;
    }
    return JSON.parse(JSON.stringify(value));
  }

  const api = {
    addObdProbeCommand,
    copyLiveSampleToDummyData,
    createVehicleLiveState,
    mergeObjects,
    mergeVehicleLiveEvent,
    previewStateOverride,
    selectedVehicle,
    setSelectedCanPort,
    setSelectedObdDevice,
    setSelectedObdPair,
    setSelectedComPort,
    setSelectedObdSerialPort,
    sortedComPorts,
    sortedObdDevices,
    upsertConfirmedCanSignal,
    upsertObdPidDefinition,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorVehicleLiveState = api;
})(typeof window !== "undefined" ? window : globalThis);
