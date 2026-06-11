(function exposeEditorVehicleLiveActions(globalScope) {
  function onSimulationToggleCommand(state, checked, deps) {
    state.simulationEnabled = Boolean(checked);
    deps.renderVehicleTools();
    deps.schedulePreview(30);
    deps.setStatus(state.simulationEnabled ? "시뮬레이션 모드 켜짐" : "시뮬레이션 모드 꺼짐", "ok");
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
    deps.setStatus(result.ok ? `BLE 장치 ${state.vehicleLive.obdDevices.length}개 발견` : state.vehicleLive.lastError, result.ok ? "ok" : "error");
    return result;
  }

  async function scanComPortsCommand(state, service, domOrDeps, maybeDeps, options) {
    const dom = maybeDeps ? domOrDeps : null;
    const deps = maybeDeps || domOrDeps;
    const target = options?.target || targetFromScanOptions(options, dom);
    const autoFillObd = Boolean(dom && (options?.autoFillObdSerial ?? true));
    setPortScanSummary(state.vehicleLive, target, "");
    setPortScanState(state.vehicleLive, target, "scanning", "");
    deps.renderVehicleTools();
    const result = await service.listComPorts();
    const ports = deps.vehicleLiveState.sortedComPorts(result.ports || []);
    state.vehicleLive.comPorts = ports;
    updateTargetPortLists(state.vehicleLive, ports, target);
    setPortScanSummary(state.vehicleLive, target, portScanSummary(state.vehicleLive, ports, target));
    setPortScanState(state.vehicleLive, target, result.ok ? "idle" : "error", (result.errors || []).join("\n"));
    const obdPorts = target === "obd" ? state.vehicleLive.obdComPorts : ports;
    const obdPort = autoFillObd ? autoFillObdSerialPort(dom, obdPorts) : null;
    if (obdPort) {
      setSelectedObdSerialPort(deps.vehicleLiveState, state.vehicleLive, obdPort);
    }
    deps.renderVehicleTools();
    const foundMessage = obdPort
      ? `COM 포트 ${ports.length}개 발견; OBD 시리얼 ${obdPort.device} 선택됨`
      : `COM 포트 ${ports.length}개 발견`;
    deps.setStatus(result.ok ? foundMessage : (result.errors || []).join("\n"), result.ok ? "ok" : "error");
    return result;
  }

  function selectComPortCommand(state, device, dom, deps) {
    const port = findComPort(state.vehicleLive, device) || { device, description: "" };
    if (isLikelyObdSerialPort(port)) {
      return selectObdSerialPortCommand(state, device, dom, deps);
    }
    return selectCanPortCommand(state, device, dom, deps);
  }

  function selectObdSerialPortCommand(state, device, dom, deps) {
    const port = findComPort(state.vehicleLive, device) || { device, description: "" };
    setSelectedObdSerialPort(deps.vehicleLiveState, state.vehicleLive, port);
    fillObdSerialConfig(dom, port);
    if (!canChannelDevice(dom.canChannel.value) || sameDeviceName(canChannelDevice(dom.canChannel.value), port.device)) {
      dom.canEnabled.checked = false;
      dom.canChannel.value = "";
      setSelectedCanPort(deps.vehicleLiveState, state.vehicleLive, null);
    }
    deps.renderVehicleTools();
    deps.setStatus(`OBD 시리얼로 ${port.device} 선택`, "ok");
    return port;
  }

  function selectCanPortCommand(state, device, dom, deps) {
    const port = findComPort(state.vehicleLive, device) || { device, description: "" };
    setSelectedCanPort(deps.vehicleLiveState, state.vehicleLive, port);
    dom.canEnabled.checked = true;
    dom.canChannel.value = canChannelForPort(port);
    deps.renderVehicleTools();
    deps.setStatus(`${dom.canChannel.value} 선택`, "ok");
    return port;
  }

  async function selectObdDeviceAndConnectCommand(state, service, address, dom, deps) {
    const device = findObdDevice(state.vehicleLive, address) || { address, name: address };
    deps.vehicleLiveState.setSelectedObdDevice(state.vehicleLive, device);
    deps.vehicleLiveState.setSelectedObdPair(state.vehicleLive, null);
    setSelectedObdSerialPort(deps.vehicleLiveState, state.vehicleLive, null);
    state.vehicleLive.obdConnectState = "inspecting";
    state.vehicleLive.lastError = "";
    deps.renderVehicleTools();

    const inspection = await service.inspectObdBle({ mac: address, timeoutSeconds: 5 });
    state.vehicleLive.obdInspection = inspection;
    const pair = Array.isArray(inspection.pairs) && inspection.pairs.length ? inspection.pairs[0] : null;
    if (!inspection.ok || !pair) {
      state.vehicleLive.obdConnectState = "error";
      state.vehicleLive.lastError = (inspection.errors || []).join("\n") || "notify/write BLE 특성 쌍을 찾지 못했습니다.";
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
    deps.setStatus(live.ok ? `${deviceLabel(device)} 연결됨` : state.vehicleLive.lastError, live.ok ? "ok" : "error");
    return { ok: Boolean(live.ok), inspection, live };
  }

  async function inspectObdBleCommand(state, service, mac, deps) {
    const result = await service.inspectObdBle({ mac, timeoutSeconds: 5 });
    state.vehicleLive.obdInspection = result;
    if (result.ok && Array.isArray(result.pairs) && result.pairs.length) {
      deps.vehicleLiveState.setSelectedObdPair(state.vehicleLive, result.pairs[0]);
    }
    deps.renderVehicleTools();
    deps.setStatus(result.ok ? "OBD BLE 특성 준비됨" : (result.errors || []).join("\n"), result.ok ? "ok" : "error");
    return result;
  }

  async function startVehicleLiveCommand(state, service, config, deps) {
    applyConfiguredInputStatuses(state, config);
    deps.renderVehicleTools();
    const result = await service.startVehicleLive(config);
    state.vehicleLive.running = Boolean(result.ok);
    if (!result.ok) {
      const detail = (result.errors || []).join("\n") || "차량 실시간 워커를 시작하지 못했습니다.";
      if (config?.obd?.enabled) {
        setLocalInputStatus(state, "obd", "error", detail);
      }
      if (config?.can?.enabled) {
        setLocalInputStatus(state, "can", "error", detail);
      }
    }
    deps.renderVehicleTools();
    deps.setStatus(result.ok ? "차량 실시간 워커 시작됨" : (result.errors || []).join("\n"), result.ok ? "ok" : "error");
    return result;
  }

  async function stopVehicleLiveCommand(state, service, deps) {
    const result = await service.stopVehicleLive();
    state.vehicleLive.running = false;
    state.vehicleLive.desiredInputs = { obd: false, can: false };
    setLocalInputStatus(state, "obd", "idle", "연결 해제됨");
    setLocalInputStatus(state, "can", "idle", "연결 해제됨");
    deps.renderVehicleTools();
    deps.setStatus("차량 실시간 워커 중지됨", "ok");
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
      deps.setStatus("복사할 실시간 샘플이 없습니다.", "error");
      return false;
    }
    deps.recordHistory();
    deps.vehicleLiveState.copyLiveSampleToDummyData(state);
    deps.markDirty();
    deps.renderAll();
    deps.schedulePreview(30);
    deps.setStatus("실시간 샘플을 더미 데이터에 복사했습니다.", "ok");
    return true;
  }

  function saveCanSignalCommand(state, signal, deps) {
    if (!deps.vehicleLiveState.selectedVehicle(state.layout) || !signal?.frame_id || !signal?.name) {
      deps.setStatus("CAN 신호에는 프레임 ID와 상태 경로가 필요합니다.", "error");
      return false;
    }
    deps.recordHistory();
    deps.vehicleLiveState.upsertConfirmedCanSignal(state, signal);
    deps.markDirty();
    deps.renderVehicleTools();
    deps.setStatus("확인된 CAN 신호를 차량 프로필에 저장했습니다.", "ok");
    return true;
  }

  function addObdProbeCommand(state, commandText, deps) {
    const commands = String(commandText || "")
      .split(/[,\r\n]+/)
      .map((item) => item.trim())
      .filter(Boolean);
    if (!deps.vehicleLiveState.selectedVehicle(state.layout) || !commands.length) {
      deps.setStatus("OBD 프로브 명령이 비어 있습니다.", "error");
      return false;
    }
    deps.recordHistory();
    deps.vehicleLiveState.addObdProbeCommand(state, commandText);
    deps.markDirty();
    deps.renderVehicleTools();
    deps.setStatus("OBD 프로브 명령을 차량 프로필에 추가했습니다.", "ok");
    return true;
  }

  function editObdPidDefinitionCommand(dom, row, deps) {
    const command = normalizeObdPidCommand(row?.command || row?.pid);
    if (!command) {
      deps.setStatus("이 OBD PID 행은 편집할 수 없습니다.", "error");
      return false;
    }
    dom.obdPidCommand.value = command;
    dom.obdPidLabel.value = cleanDefaultPidLabel(row.label, command);
    dom.obdPidUnit.value = row.unit === "raw" ? "" : row.unit || "";
    dom.obdPidPath.value = row.path || `vehicle.obd_${command.toLowerCase()}`;
    dom.obdPidReferenceValue.value = "";
    dom.obdPidByteIndex.value = "";
    dom.obdPidLength.value = "";
    dom.obdPidScale.value = "";
    dom.obdPidOffset.value = "";
    dom.obdPidEndian.value = "big";
    dom.obdPidSigned.checked = false;
    const raw = String(row.rawBytes || "").trim();
    deps.setStatus(raw ? `${command} Raw ${raw} 불러옴` : `${command} 불러옴`, "ok");
    return true;
  }

  function saveObdPidDefinitionCommand(state, definition, deps) {
    const command = normalizeObdPidCommand(definition?.command);
    const label = String(definition?.label || "").trim();
    if (!deps.vehicleLiveState.selectedVehicle(state.layout)) {
      deps.setStatus("OBD PID를 저장하기 전에 차량을 선택하세요.", "error");
      return false;
    }
    if (!command || !label) {
      deps.setStatus("OBD PID에는 PID와 이름이 필요합니다.", "error");
      return false;
    }
    deps.recordHistory();
    const saved = deps.vehicleLiveState.upsertObdPidDefinition(state, { ...definition, command, label });
    if (!saved) {
      deps.setStatus("OBD PID 정의를 저장하지 못했습니다.", "error");
      return false;
    }
    applyObdPidDefinitionToLiveState(state, saved);
    deps.markDirty();
    deps.renderVehicleTools();
    if (state.simulationEnabled) {
      deps.schedulePreview(30);
    }
    deps.setStatus(`OBD PID ${saved.command}을 ${saved.label}(으)로 저장했습니다.`, "ok");
    return true;
  }

  function assignObdBindingCommand(state, binding, element, deps, label = "") {
    const path = String(binding || "").trim();
    if (!path) {
      deps.setStatus("이 OBD 행에는 HUD 연결 경로가 없습니다.", "error");
      return false;
    }
    if (!element) {
      deps.setStatus("먼저 캔버스에서 HUD 요소를 선택하세요.", "error");
      return false;
    }
    if (!supportsObdBindingAssignment(element)) {
      deps.setStatus("선택한 요소는 표준 HUD 연결을 사용하지 않습니다.", "error");
      return false;
    }
    if (String(element.binding || "") === path) {
      deps.setStatus(`${element.label || element.id || "선택 요소"}는 이미 ${path}를 사용합니다.`, "ok");
      return false;
    }
    deps.recordHistory();
    element.binding = path;
    delete element.palette_key;
    deps.markDirty();
    deps.renderAll();
    deps.renderProperties?.();
    deps.renderLayers?.();
    deps.renderOverlay?.();
    deps.schedulePreview(60);
    const target = element.label || element.id || "선택 요소";
    const source = String(label || path).trim();
    deps.setStatus(`${source}을 ${target}에 연결했습니다.`, "ok");
    return true;
  }

  function applyObdPidDefinitionToLiveState(state, definition) {
    const command = normalizeObdPidCommand(definition?.command);
    if (!command || !state.vehicleLive?.mergedState) {
      return false;
    }
    const record = (state.vehicleLive.obdRecords || []).find((item) => normalizeObdPidCommand(item.command) === command);
    const bytes = payloadBytesAfter(record?.response || "", command);
    const rawBytes = bytesToHex(bytes);
    const value = customObdValueFromBytes(definition, bytes);
    if (value === undefined) {
      return false;
    }
    const obd = (state.vehicleLive.mergedState.obd = state.vehicleLive.mergedState.obd || {});
    obd.values = Array.isArray(obd.values) ? obd.values : [];
    const item = {
      command,
      label: definition.label,
      value,
      unit: definition.unit || "",
      statePath: definition.path || "",
      rawBytes,
      custom: true,
    };
    const index = obd.values.findIndex((entry) => normalizeObdPidCommand(entry.command) === command);
    if (index >= 0) {
      obd.values[index] = { ...obd.values[index], ...item };
    } else {
      obd.values.push(item);
    }
    obd.value_count = obd.values.length;
    if (definition.path) {
      setNestedValue(state.vehicleLive.mergedState, definition.path, value);
    }
    return true;
  }

  function payloadBytesAfter(response, command) {
    const compact = String(response || "").replace(/[^0-9a-f]/gi, "").toUpperCase();
    const normalized = normalizeObdPidCommand(command);
    if (!compact || !normalized) {
      return [];
    }
    const marker = `41${normalized.slice(2)}`;
    const index = compact.indexOf(marker);
    if (index < 0) {
      return [];
    }
    const payload = compact.slice(index + marker.length);
    const bytes = [];
    for (let offset = 0; offset + 1 < payload.length; offset += 2) {
      const value = Number.parseInt(payload.slice(offset, offset + 2), 16);
      if (Number.isFinite(value)) {
        bytes.push(value);
      }
    }
    return bytes;
  }

  function customObdValueFromBytes(definition, bytes) {
    const rawBytes = bytesToHex(bytes);
    const byteLength = parseOptionalInt(definition?.byte_length ?? definition?.byteLength ?? definition?.length);
    if (!byteLength) {
      return rawBytes || undefined;
    }
    const byteIndex = Math.max(0, parseOptionalInt(definition.byte_index ?? definition.byteIndex) || 0);
    const payload = bytes.slice(byteIndex, byteIndex + Math.max(1, Math.min(4, byteLength)));
    if (payload.length < byteLength) {
      return undefined;
    }
    const ordered = String(definition.endian || "big").toLowerCase() === "little" ? [...payload].reverse() : payload;
    let raw = ordered.reduce((value, byte) => value * 256 + byte, 0);
    if (definition.signed) {
      const bits = payload.length * 8;
      const signBit = 2 ** (bits - 1);
      if (raw >= signBit) {
        raw -= 2 ** bits;
      }
    }
    const decoded = raw * parseOptionalFloat(definition.scale, 1) + parseOptionalFloat(definition.offset, 0);
    return Number.isInteger(decoded) ? decoded : Number(decoded.toFixed(4));
  }

  function setNestedValue(target, path, value) {
    const parts = String(path || "").split(".").filter(Boolean);
    if (!parts.length) {
      return;
    }
    let cursor = target;
    for (const part of parts.slice(0, -1)) {
      if (!cursor[part] || typeof cursor[part] !== "object" || Array.isArray(cursor[part])) {
        cursor[part] = {};
      }
      cursor = cursor[part];
    }
    cursor[parts[parts.length - 1]] = value;
  }

  function bytesToHex(bytes) {
    return (bytes || []).map((byte) => byte.toString(16).toUpperCase().padStart(2, "0")).join(" ");
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

  function parseOptionalInt(value) {
    if (value === undefined || value === null || value === "") {
      return null;
    }
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function parseOptionalFloat(value, fallback) {
    if (value === undefined || value === null || value === "") {
      return fallback;
    }
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function cleanDefaultPidLabel(label, command) {
    const text = String(label || "").trim();
    return text === `Mode 01 PID ${command.slice(2)}` || text === command ? "" : text;
  }

  function buildVehicleLiveConfig(state, dom, options = {}) {
    const enabledSources = options.enabledSources || {};
    const obdPort = String(dom.obdSerialPort.value || "").trim();
    const canChannel = String(dom.canChannel.value || "").trim();
    const canDevice = canChannelDevice(canChannel);
    const canPort = findComPort(state.vehicleLive || {}, canDevice);
    const canMatchesObd = obdPort && sameDeviceName(canDevice, obdPort);
    const canLooksLikeObd = !obdPort && canPort && isLikelyObdSerialPort(canPort);
    const obdRequested = enabledSources.obd ?? Boolean(dom.obdEnabled.checked);
    const canRequested = enabledSources.can ?? Boolean(dom.canEnabled.checked);
    return {
      layout: state.layout,
      obd: {
        enabled: Boolean(obdRequested),
        port: obdPort,
        baud: Number.parseInt(dom.obdSerialBaud.value, 10) || 38400,
        mac: dom.obdBleMac.value.trim(),
        rxUuid: dom.obdBleRxUuid.value.trim(),
        txUuid: dom.obdBleTxUuid.value.trim(),
        timeoutSeconds: Number.parseFloat(dom.obdTimeout.value) || 2,
      },
      can: {
        enabled: Boolean(canRequested && canChannel && !canMatchesObd && !canLooksLikeObd),
        interface: "slcan",
        channel: canChannel,
        bitrate: Number.parseInt(dom.canBitrate.value, 10) || 500000,
        listenOnly: Boolean(dom.canListenOnly.checked),
      },
    };
  }

  function applyConfiguredInputStatuses(state, config) {
    const obdEnabled = Boolean(config?.obd?.enabled);
    const canEnabled = Boolean(config?.can?.enabled);
    state.vehicleLive.desiredInputs = { obd: obdEnabled, can: canEnabled };
    setLocalInputStatus(
      state,
      "obd",
      obdEnabled ? "connecting" : "idle",
      obdEnabled ? obdOpeningDetail(config.obd || {}) : "연결 해제됨"
    );
    setLocalInputStatus(
      state,
      "can",
      canEnabled ? "connecting" : "idle",
      canEnabled ? canOpeningDetail(config.can || {}) : "연결 해제됨"
    );
  }

  function setLocalInputStatus(state, source, statusState, detail) {
    if (!state.vehicleLive.status) {
      state.vehicleLive.status = {};
    }
    state.vehicleLive.status[source] = {
      state: statusState,
      detail,
      updatedAt: new Date().toISOString(),
    };
  }

  function obdOpeningDetail(config) {
    const port = String(config.port || "").trim();
    if (port) {
      return `OBD 시리얼 ${port} 여는 중`;
    }
    const mac = String(config.mac || "").trim();
    if (mac) {
      return `OBD BLE ${mac} 여는 중`;
    }
    return "OBD 입력 여는 중";
  }

  function canOpeningDetail(config) {
    const channel = String(config.channel || "").trim();
    return channel ? `CANable ${channel} 여는 중` : "CANable 입력 여는 중";
  }

  function findObdDevice(vehicleLive, address) {
    return (vehicleLive.obdDevices || []).find((device) => device.address === address) || null;
  }

  function findComPort(vehicleLive, deviceName) {
    const ports = [
      ...(vehicleLive.obdComPorts || []),
      ...(vehicleLive.canComPorts || []),
      ...(vehicleLive.comPorts || []),
    ];
    return ports.find((port) => port.device === deviceName) || null;
  }

  function targetFromScanOptions(options, dom) {
    if (options?.autoFillObdSerial === false) {
      return "can";
    }
    if (dom && (options?.autoFillObdSerial ?? true)) {
      return "obd";
    }
    return "all";
  }

  function updateTargetPortLists(vehicleLive, ports, target) {
    if (target === "obd") {
      vehicleLive.obdComPorts = ports.filter(isLikelyObdSerialPort);
      return;
    }
    if (target === "can") {
      vehicleLive.canComPorts = ports.filter(isLikelyCanPort);
      return;
    }
    vehicleLive.obdComPorts = ports.filter(isLikelyObdSerialPort);
    vehicleLive.canComPorts = ports.filter(isLikelyCanPort);
  }

  function setPortScanState(vehicleLive, target, state, error) {
    vehicleLive.comPortScanState = state;
    vehicleLive.comPortLastError = error || "";
    if (target === "obd" || target === "all") {
      vehicleLive.obdComPortScanState = state;
      vehicleLive.obdComPortLastError = error || "";
    }
    if (target === "can" || target === "all") {
      vehicleLive.canComPortScanState = state;
      vehicleLive.canComPortLastError = error || "";
    }
  }

  function setPortScanSummary(vehicleLive, target, summary) {
    if (target === "obd" || target === "all") {
      vehicleLive.lastObdComScanSummary = summary || "";
    }
    if (target === "can" || target === "all") {
      vehicleLive.lastCanComScanSummary = summary || "";
    }
  }

  function portScanSummary(vehicleLive, ports, target) {
    const total = ports.length;
    if (target === "obd") {
      const candidates = vehicleLive.obdComPorts || [];
      if (candidates.length) {
        return `OBD COM 검색 완료: ${total}개 포트 중 후보 ${candidates.length}개.`;
      }
      return `OBD COM 검색 완료: ${total}개 포트 중 OBD 후보 없음. Raw: ${portNames(ports)}`;
    }
    if (target === "can") {
      const candidates = vehicleLive.canComPorts || [];
      if (candidates.length) {
        return `CANable COM 검색 완료: ${total}개 포트 중 후보 ${candidates.length}개.`;
      }
      return `CANable COM 검색 완료: ${total}개 포트 중 CANable 후보 없음. Raw: ${portNames(ports)}`;
    }
    return `COM 검색 완료: ${total}개 포트.`;
  }

  function portNames(ports) {
    return (ports || []).map((port) => port.device).filter(Boolean).join(", ") || "--";
  }

  function canChannelForPort(port) {
    const device = String(port?.device || "").trim();
    if (!device) {
      return "";
    }
    return device.includes("@") ? device : `${device}@115200`;
  }

  function canChannelDevice(channel) {
    return String(channel || "").trim().split("@")[0].trim();
  }

  function sameDeviceName(left, right) {
    const leftValue = String(left || "").trim().toUpperCase();
    const rightValue = String(right || "").trim().toUpperCase();
    return Boolean(leftValue && rightValue && leftValue === rightValue);
  }

  function fillObdConfig(dom, address, pair) {
    dom.obdEnabled.checked = true;
    dom.obdSerialPort.value = "";
    dom.obdBleMac.value = address;
    dom.obdBleRxUuid.value = pair.rx_uuid || pair.rxUuid || "";
    dom.obdBleTxUuid.value = pair.tx_uuid || pair.txUuid || "";
  }

  function fillObdSerialConfig(dom, port) {
    if (dom.obdEnabled) {
      dom.obdEnabled.checked = true;
    }
    if (dom.obdSerialPort) {
      dom.obdSerialPort.value = port.device || "";
    }
    if (dom.obdSerialBaud && !String(dom.obdSerialBaud.value || "").trim()) {
      dom.obdSerialBaud.value = "38400";
    }
    if (dom.obdBleMac) {
      dom.obdBleMac.value = "";
    }
    if (dom.obdBleRxUuid) {
      dom.obdBleRxUuid.value = "";
    }
    if (dom.obdBleTxUuid) {
      dom.obdBleTxUuid.value = "";
    }
  }

  function autoFillObdSerialPort(dom, ports) {
    if (!dom?.obdSerialPort || String(dom.obdSerialPort.value || "").trim()) {
      return null;
    }
    const port = (ports || []).find((item) => isLikelyObdSerialPort(item));
    if (!port?.device) {
      return null;
    }
    fillObdSerialConfig(dom, port);
    return port;
  }

  function prepareVehicleLiveDomForStart(state, dom) {
    const canDevice = canChannelDevice(dom?.canChannel?.value);
    if (!canDevice || !dom?.obdSerialPort || String(dom.obdSerialPort.value || "").trim()) {
      return null;
    }
    const port = findComPort(state.vehicleLive || {}, canDevice);
    if (!port || !isLikelyObdSerialPort(port)) {
      return null;
    }
    fillObdSerialConfig(dom, port);
    const vehicleLiveState = safeVehicleLiveState();
    setSelectedObdSerialPort(vehicleLiveState, state.vehicleLive, port);
    setSelectedCanPort(vehicleLiveState, state.vehicleLive, null);
    if (dom.canEnabled) {
      dom.canEnabled.checked = false;
    }
    if (dom.canChannel) {
      dom.canChannel.value = "";
    }
    return port;
  }

  function isLikelyObdSerialPort(port) {
    if (port?.likelyCanable) {
      return false;
    }
    if (port?.likelyObdSerial) {
      return true;
    }
    const text = `${port?.device || ""} ${port?.description || ""} ${port?.hwid || ""} ${port?.manufacturer || ""} ${port?.product || ""}`.toLowerCase();
    return (
      text.includes("bluetooth") ||
      text.includes("bthenum") ||
      /\b(elm327|vlink|v-link|icar|obd)\b/.test(text)
    ) && !text.includes("000000000000_") && !text.includes("localmfg&0000");
  }

  function isLikelyCanPort(port) {
    const text = `${port?.device || ""} ${port?.description || ""} ${port?.hwid || ""} ${port?.manufacturer || ""} ${port?.product || ""}`.toLowerCase();
    return Boolean(port?.likelyCanable || /\b(cantact|canable|candlelight|candle|slcan|usb to can|can adapter)\b/.test(text));
  }

  function supportsObdBindingAssignment(element) {
    const type = String(element?.type || "");
    return ["value", "warning_icon", "gear_indicator"].includes(type) || Object.prototype.hasOwnProperty.call(element || {}, "binding");
  }

  function deviceLabel(device) {
    return device?.name ? `${device.name} (${device.address})` : String(device?.address || "OBD BLE 어댑터");
  }

  function setSelectedCanPort(vehicleLiveState, vehicleLive, port) {
    if (vehicleLiveState?.setSelectedCanPort) {
      return vehicleLiveState.setSelectedCanPort(vehicleLive, port);
    }
    vehicleLive.selectedCanPort = port ? JSON.parse(JSON.stringify(port)) : null;
    vehicleLive.selectedComPort = vehicleLive.selectedCanPort;
    return vehicleLive.selectedCanPort;
  }

  function setSelectedObdSerialPort(vehicleLiveState, vehicleLive, port) {
    if (vehicleLiveState?.setSelectedObdSerialPort) {
      return vehicleLiveState.setSelectedObdSerialPort(vehicleLive, port);
    }
    vehicleLive.selectedObdSerialPort = port ? JSON.parse(JSON.stringify(port)) : null;
    return vehicleLive.selectedObdSerialPort;
  }

  function safeVehicleLiveState() {
    return globalScope.EditorVehicleLiveState || (typeof require !== "undefined" ? require("./editorVehicleLiveState.js") : null);
  }

  const api = {
    addObdProbeCommand,
    assignObdBindingCommand,
    autoFillObdSerialPort,
    buildVehicleLiveConfig,
    copyLiveSampleCommand,
    editObdPidDefinitionCommand,
    handleVehicleLiveEventCommand,
    inspectObdBleCommand,
    onSimulationToggleCommand,
    prepareVehicleLiveDomForStart,
    saveCanSignalCommand,
    saveObdPidDefinitionCommand,
    scanComPortsCommand,
    selectCanPortCommand,
    selectObdDeviceAndConnectCommand,
    selectComPortCommand,
    selectObdSerialPortCommand,
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
