(function exposeEditorVehicleLiveState(globalScope) {
  function createVehicleLiveState() {
    return {
      activeTab: "elements",
      status: {
        obd: { state: "idle", detail: "", updatedAt: "" },
        can: { state: "idle", detail: "", updatedAt: "" },
      },
      mergedState: {},
      canFrames: [],
      canSummary: { frame_count: 0, unique_id_count: 0, ids: [] },
      comPorts: [],
      selectedComPort: null,
      comPortScanState: "idle",
      comPortLastError: "",
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
      vehicleLive.obdRecords = vehicleLive.obdRecords.slice(0, 80);
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
    return port?.likelyCanable || /\b(canable|candlelight|candle|slcan|usb to can|can adapter)\b/.test(text) ? 1 : 0;
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
    setSelectedObdDevice,
    setSelectedObdPair,
    setSelectedComPort,
    sortedComPorts,
    sortedObdDevices,
    upsertConfirmedCanSignal,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorVehicleLiveState = api;
})(typeof window !== "undefined" ? window : globalThis);
