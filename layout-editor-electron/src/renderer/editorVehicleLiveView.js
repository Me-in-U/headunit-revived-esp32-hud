(function exposeEditorVehicleLiveView(globalScope) {
  const VehicleLiveState =
    globalScope.EditorVehicleLiveState ||
    (typeof require !== "undefined" ? require("./editorVehicleLiveState.js") : null);
  const TOOL_TABS = ["elements", "connection", "can", "obd"];

  function renderVehicleTools(state, dom, options) {
    const live = state.vehicleLive;
    for (const tab of TOOL_TABS) {
      const button = dom[`${tab === "elements" ? "elements" : tab === "can" ? "canAnalysis" : tab === "obd" ? "obdAnalysis" : "connection"}Tab`];
      if (button) {
        button.classList.toggle("active", live.activeTab === tab);
        button.setAttribute("aria-selected", String(live.activeTab === tab));
      }
    }
    dom.elementsPanel.hidden = live.activeTab !== "elements";
    dom.connectionPanel.hidden = live.activeTab !== "connection";
    dom.canAnalysisPanel.hidden = live.activeTab !== "can";
    dom.obdAnalysisPanel.hidden = live.activeTab !== "obd";
    renderConnectionPanel(state, dom, options.documentRef);
    renderCanAnalysisPanel(state, dom, options.documentRef);
    renderObdAnalysisPanel(state, dom, options.documentRef);
  }

  function renderConnectionPanel(state, dom, documentRef) {
    dom.simulationToggle.checked = Boolean(state.simulationEnabled);
    writeStatus(dom.obdConnectionStatus, connectionStatusForObd(state.vehicleLive), documentRef);
    writeStatus(dom.canConnectionStatus, connectionStatusForCan(state.vehicleLive), documentRef);
    renderObdSelection(state, dom, documentRef);
    renderComPortSelection(state, dom, documentRef);
  }

  function renderObdSelection(state, dom, documentRef) {
    if (!dom.obdDeviceList || !dom.obdSelectedStatus) {
      return;
    }
    const selected = state.vehicleLive.selectedObdDevice;
    const selectedSerial = state.vehicleLive.selectedObdSerialPort;
    const serialPort = String(dom.obdSerialPort?.value || "").trim();
    dom.obdSelectedStatus.textContent = selected
      ? `${deviceLabel(selected)} · ${state.vehicleLive.obdConnectState || "selected"}`
      : selectedSerial
        ? `${selectedSerial.device || serialPort} · OBD Classic Bluetooth`
      : serialPort
        ? `OBD serial ${serialPort} · Classic Bluetooth`
        : "OBD 어댑터 선택 안 됨";
    renderObdSerialPortList(dom.obdSerialPortList, documentRef, state.vehicleLive);
    renderObdDeviceList(dom.obdDeviceList, documentRef, state.vehicleLive);
  }

  function renderObdDeviceList(parent, documentRef, vehicleLive) {
    const doc = documentRef || parent.ownerDocument;
    parent.replaceChildren();
    const devices = VehicleLiveState.sortedObdDevices(vehicleLive.obdDevices || []);
    if (!devices.length) {
      const empty = doc.createElement("div");
      empty.className = "empty-state compact";
      empty.textContent = vehicleLive.obdConnectState === "scanning" ? "Bluetooth 장치 검색 중..." : "Bluetooth 검색으로 주변 OBD 어댑터를 찾으세요.";
      parent.append(empty);
      return;
    }
    for (const device of devices) {
      const row = doc.createElement("button");
      row.type = "button";
      row.className = "obd-device-row";
      row.dataset.obdAddress = device.address || "";
      if (vehicleLive.selectedObdDevice?.address === device.address) {
        row.className += " selected";
      }
      row.setAttribute("data-obd-address", device.address || "");
      row.setAttribute("role", "option");
      row.setAttribute("aria-selected", String(vehicleLive.selectedObdDevice?.address === device.address));
      row.textContent = `${deviceLabel(device)} · ${device.address || "--"}${device.rssi !== undefined && device.rssi !== null ? ` · ${device.rssi} dBm` : ""}`;
      parent.append(row);
    }
  }

  function renderComPortSelection(state, dom, documentRef) {
    if (!dom.comPortList || !dom.comSelectedStatus) {
      return;
    }
    const selected = state.vehicleLive.selectedCanPort || state.vehicleLive.selectedComPort;
    dom.comSelectedStatus.textContent = selected ? `${selected.device || "--"} · ${selected.description || "시리얼 장치"}` : "COM 포트 선택 안 됨";
    renderComPortList(dom.comPortList, documentRef, state.vehicleLive);
  }

  function renderComPortList(parent, documentRef, vehicleLive) {
    return renderSerialPortList(parent, documentRef, vehicleLive, {
      emptyIdle: "COM 포트 새로고침을 누르면 연결된 CANable 또는 CANtact USB 장치가 표시됩니다.",
      filter: isLikelyCanPort,
      ports: vehicleLive.canComPorts || [],
      scanState: vehicleLive.canComPortScanState || vehicleLive.comPortScanState,
      scanError: vehicleLive.canComPortLastError || vehicleLive.comPortLastError,
      scanSummary: vehicleLive.lastCanComScanSummary,
      selected: vehicleLive.selectedCanPort || vehicleLive.selectedComPort,
      selectedDatasetName: "comPort",
      selectedAttribute: "data-com-port",
    });
  }

  function renderObdSerialPortList(parent, documentRef, vehicleLive) {
    return renderSerialPortList(parent, documentRef, vehicleLive, {
      emptyIdle: "OBD COM 새로고침을 누르면 Android-vlink Classic Bluetooth 시리얼 포트가 표시됩니다.",
      filter: isLikelyObdSerialPort,
      ports: vehicleLive.obdComPorts || [],
      scanState: vehicleLive.obdComPortScanState || vehicleLive.comPortScanState,
      scanError: vehicleLive.obdComPortLastError || vehicleLive.comPortLastError,
      scanSummary: vehicleLive.lastObdComScanSummary,
      selected: vehicleLive.selectedObdSerialPort,
      selectedDatasetName: "obdSerialPort",
      selectedAttribute: "data-obd-serial-port",
    });
  }

  function renderSerialPortList(parent, documentRef, vehicleLive, options) {
    if (!parent) {
      return;
    }
    const doc = documentRef || parent.ownerDocument;
    parent.replaceChildren();
    const ports = VehicleLiveState.sortedComPorts(options.ports || []).filter(options.filter);
    if (!ports.length) {
      const empty = doc.createElement("div");
      empty.className = "empty-state compact";
      if (options.scanState === "scanning") {
        empty.textContent = "연결된 COM 포트 확인 중...";
      } else if (options.scanState === "error") {
        empty.textContent = options.scanError || "COM 포트 검색 실패";
      } else {
        empty.textContent = options.scanSummary || options.emptyIdle;
      }
      parent.append(empty);
      return;
    }
    for (const port of ports) {
      const row = doc.createElement("button");
      row.type = "button";
      row.className = "com-port-row";
      row.dataset[options.selectedDatasetName] = port.device || "";
      if (options.selected?.device === port.device) {
        row.className += " selected";
      }
      row.setAttribute(options.selectedAttribute, port.device || "");
      row.setAttribute("role", "option");
      row.setAttribute("aria-selected", String(options.selected?.device === port.device));
      row.title = comPortText(port);
      const title = doc.createElement("span");
      title.className = "port-title";
      title.textContent = comPortTitle(port);
      const meta = doc.createElement("span");
      meta.className = "port-meta";
      meta.textContent = comPortMeta(port);
      row.append(title, meta);
      parent.append(row);
    }
  }

  function renderCanAnalysisPanel(state, dom, documentRef) {
    const summary = state.vehicleLive.canSummary || {};
    dom.canFrameCount.textContent = String(summary.frame_count || 0);
    const firstId = Array.isArray(summary.ids) && summary.ids.length ? summary.ids[0].id : "--";
    dom.canLastId.textContent = state.vehicleLive.canFrames[0]?.id || firstId || "--";
    renderList(
      dom.canSummaryList,
      documentRef,
      (summary.ids || []).slice(0, 20),
      (item) => `${item.id} · 개수 ${item.count} · 변화 Byte ${(item.changing_byte_indexes || []).join(",") || "--"}`
    );
    renderList(
      dom.canFrameList,
      documentRef,
      state.vehicleLive.canFrames.slice(0, 20),
      (item) => `${item.id}  ${item.data}`
    );
    dom.canDecodedPreview.textContent = JSON.stringify(state.vehicleLive.mergedState?.vehicle || {}, null, 2);
    renderLiveLogPanel(state, dom, documentRef);
  }

  function renderLiveLogPanel(state, dom, documentRef) {
    if (dom.liveCanStatus) {
      writeStatus(dom.liveCanStatus, state.vehicleLive.status.can, documentRef);
    }
    if (dom.liveObdStatus) {
      writeStatus(dom.liveObdStatus, state.vehicleLive.status.obd, documentRef);
    }
    if (dom.liveSampleStatus) {
      dom.liveSampleStatus.textContent = Object.keys(state.vehicleLive.mergedState || {}).length ? "실시간 샘플 있음" : "실시간 샘플 없음";
    }
    if (dom.liveLogList) {
      renderList(dom.liveLogList, documentRef, liveLogRows(state.vehicleLive), (item) => item);
    }
  }

  function renderObdAnalysisPanel(state, dom, documentRef) {
    const obd = state.vehicleLive.mergedState?.obd || {};
    const dtc = state.vehicleLive.mergedState?.dtc || {};
    if (dom.obdAnalysisStatus) {
      writeStatus(dom.obdAnalysisStatus, state.vehicleLive.status.obd, documentRef);
    }
    dom.obdAdapterIdentity.textContent = obd.adapter_identity || "--";
    dom.obdProtocol.textContent = obd.protocol || "--";
    dom.obdSupportedPids.textContent = obd.supported_pid_count
      ? `${obd.supported_pid_count} PIDs · ${(obd.supported_pids || []).slice(0, 12).join(", ")}${(obd.supported_pids || []).length > 12 ? ", ..." : ""}`
      : obd.supported_pid_ranges || obd.supported_pid_bitmap || "--";
    dom.obdDtcList.textContent = formatDtc(dtc);
    renderObdValueTable(dom.obdValueList, documentRef, obdValueRows(obd, dtc, state), {
      selectedElement: selectedBindingElement(state),
    });
    renderList(
      dom.obdRecordList,
      documentRef,
      state.vehicleLive.obdRecords.slice(0, 80),
      (item) => `${item.ok ? "OK" : "FAIL"} ${item.command}: ${item.response || "--"}`
    );
    const debug = state.vehicleLive.mergedState?.debug || {};
    dom.obdLastRequest.textContent = debug.obd_request || "--";
    dom.obdLastResponse.textContent = debug.obd_response || "--";
  }

  function formatDtc(dtc) {
    const codes = [...(dtc.stored || []), ...(dtc.pending || []), ...(dtc.permanent || [])];
    if (!codes.length) {
      return dtc.count ? `${dtc.count}개 보고됨` : "--";
    }
    return codes.join(", ");
  }

  function writeStatus(node, status, documentRef) {
    if (!node) {
      return;
    }
    const view = statusView(status);
    node.dataset.state = view.state;
    const doc = documentRef || node.ownerDocument;
    if (!doc?.createElement || !node.replaceChildren) {
      node.textContent = view.text;
      return;
    }
    const dot = doc.createElement("span");
    dot.className = "status-dot";
    dot.setAttribute("aria-hidden", "true");
    const copy = doc.createElement("span");
    copy.className = "status-copy";
    const label = doc.createElement("strong");
    label.className = "status-label";
    label.textContent = view.label;
    copy.append(label);
    if (view.detail) {
      const detail = doc.createElement("span");
      detail.className = "status-detail";
      detail.textContent = ` · ${view.detail}`;
      copy.append(detail);
    }
    node.replaceChildren(dot, copy);
  }

  function statusView(status) {
    const rawState = status?.state || "idle";
    const state = normalizeStatusState(rawState);
    const label = statusLabel(rawState);
    const detailParts = [];
    if (status?.detail) {
      detailParts.push(status.detail);
    }
    if (status?.updatedAt) {
      detailParts.push(status.updatedAt);
    }
    const detail = detailParts.join(" · ");
    return {
      state,
      label,
      detail,
      text: detail ? `${label} · ${detail}` : label,
    };
  }

  function normalizeStatusState(state) {
    if (["connected", "live"].includes(state)) {
      return "live";
    }
    if (["connecting", "scanning", "inspecting"].includes(state)) {
      return "connecting";
    }
    if (state === "error") {
      return "error";
    }
    if (state === "stale") {
      return "stale";
    }
    return "idle";
  }

  function statusLabel(state) {
    if (state === "connected" || state === "live") {
      return "연결됨";
    }
    if (state === "scanning") {
      return "검색 중";
    }
    if (state === "inspecting") {
      return "검사 중";
    }
    if (state === "connecting") {
      return "연결 중";
    }
    if (state === "stale") {
      return "대기 중";
    }
    if (state === "error") {
      return "오류";
    }
    return "연결 안 됨";
  }

  function connectionStatusForObd(vehicleLive) {
    const status = vehicleLive.status?.obd || {};
    if (normalizeStatusState(status.state || "idle") !== "idle") {
      return status;
    }
    if (vehicleLive.obdComPortScanState === "scanning") {
      return { state: "scanning", detail: "OBD COM 포트 확인 중", updatedAt: "" };
    }
    if (vehicleLive.obdComPortScanState === "error") {
      return { state: "error", detail: vehicleLive.obdComPortLastError || "OBD COM 포트 검색 실패", updatedAt: "" };
    }
    const connectState = vehicleLive.obdConnectState;
    if (["scanning", "inspecting", "connecting", "connected", "error"].includes(connectState)) {
      return {
        state: connectState,
        detail: status.detail || vehicleLive.lastError || obdConnectDetail(connectState),
        updatedAt: status.updatedAt || "",
      };
    }
    return status;
  }

  function connectionStatusForCan(vehicleLive) {
    const status = vehicleLive.status?.can || {};
    if (normalizeStatusState(status.state || "idle") !== "idle") {
      return status;
    }
    if (vehicleLive.comPortScanState === "scanning") {
      return { state: "scanning", detail: "CANable COM 포트 확인 중", updatedAt: "" };
    }
    if (vehicleLive.canComPortScanState === "scanning") {
      return { state: "scanning", detail: "CANable COM 포트 확인 중", updatedAt: "" };
    }
    if (vehicleLive.canComPortScanState === "error") {
      return { state: "error", detail: vehicleLive.canComPortLastError || "COM 포트 검색 실패", updatedAt: "" };
    }
    if (vehicleLive.comPortScanState === "error") {
      return { state: "error", detail: vehicleLive.comPortLastError || "COM 포트 검색 실패", updatedAt: "" };
    }
    return status;
  }

  function obdConnectDetail(state) {
    if (state === "scanning") {
      return "OBD 어댑터 검색 중";
    }
    if (state === "inspecting") {
      return "BLE 특성 확인 중";
    }
    if (state === "connecting") {
      return "OBD 입력 여는 중";
    }
    if (state === "connected") {
      return "OBD 입력 준비됨";
    }
    return "";
  }

  function deviceLabel(device) {
    return String(device?.name || device?.address || "이름 없는 장치");
  }

  function comPortText(port) {
    const channel = port?.device ? `${port.device}@115200` : "--";
    return [channel, port?.description, port?.manufacturer, port?.product, port?.hwid].filter(Boolean).join(" · ");
  }

  function comPortTitle(port) {
    const device = port?.device || "--";
    if (port?.likelyCanable) {
      return `${device} · CAN 어댑터`;
    }
    if (port?.likelyObdSerial) {
      return `${device} · OBD Bluetooth`;
    }
    return `${device} · 시리얼 포트`;
  }

  function comPortMeta(port) {
    const description = String(port?.description || port?.product || "시리얼 장치").replace(/\s*\(COM\d+\)\s*$/i, "");
    const serial = port?.serialNumber ? ` · ${port.serialNumber}` : "";
    return `${description}${serial}`;
  }

  function isLikelyCanPort(port) {
    const text = `${port?.device || ""} ${port?.description || ""} ${port?.hwid || ""} ${port?.manufacturer || ""} ${port?.product || ""}`.toLowerCase();
    return Boolean(port?.likelyCanable || /\b(cantact|canable|candlelight|candle|slcan|usb to can|can adapter)\b/.test(text));
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

  function liveLogRows(vehicleLive) {
    const rows = [];
    for (const frame of (vehicleLive.canFrames || []).slice(0, 12)) {
      rows.push(`CAN ${frame.id || "--"}  ${frame.data || "--"}`);
    }
    for (const record of (vehicleLive.obdRecords || []).slice(0, 8)) {
      rows.push(`OBD ${record.ok ? "OK" : "FAIL"} ${record.command || "--"}: ${record.response || "--"}`);
    }
    if (!rows.length) {
      const canStatus = vehicleLive.status?.can || {};
      const obdStatus = vehicleLive.status?.obd || {};
      if (canStatus.detail) {
        rows.push(`CAN ${canStatus.state || "idle"}: ${canStatus.detail}`);
      }
      if (obdStatus.detail) {
        rows.push(`OBD ${obdStatus.state || "idle"}: ${obdStatus.detail}`);
      }
    }
    return rows.slice(0, 20);
  }

  function obdValueRows(obd, dtc, state) {
    const customDefinitions = obdPidDefinitionMap(selectedVehicle(state.layout)?.obd_pid_definitions || []);
    const rows = [
      { name: "어댑터", value: obd.adapter_identity || "--", pid: "ATI", detail: "" },
      { name: "프로토콜", value: obd.protocol || "--", pid: "ATDP", detail: "" },
      { name: "DTC", value: formatDtc(dtc), pid: "03/07/0A", detail: "" },
      {
        name: "지원 PID",
        value: obd.supported_pid_count ? `${obd.supported_pid_count} PIDs` : "--",
        pid: "0100+",
        detail: (obd.supported_pids || []).join(", "),
      },
    ];
    const values = Array.isArray(obd.values)
      ? [...obd.values].sort((left, right) => String(left.command || "").localeCompare(String(right.command || "")))
      : [];
    const valueCommands = new Set(values.map((item) => String(item.command || "").toUpperCase()).filter(Boolean));
    for (const item of values) {
      const command = normalizeObdPidCommand(item.command);
      const displayItem = applyObdPidDefinition(item, customDefinitions[command]);
      rows.push({
        name: displayItem.label || displayItem.command || "값",
        value: formatObdValue(displayItem),
        pid: displayItem.command || "",
        detail: displayItem.statePath || "",
        unit: displayItem.unit || "",
        rawBytes: displayItem.rawBytes || "",
      });
    }
    for (const pid of obd.supported_pids || []) {
      const command = String(pid || "").toUpperCase();
      if (!command || valueCommands.has(command)) {
        continue;
      }
      const definition = customDefinitions[normalizeObdPidCommand(command)];
      rows.push({
        name: definition?.label || `지원 PID ${command}`,
        value: "지원됨",
        pid: command,
        detail: definition?.path || "",
        unit: definition?.unit || "",
        rawBytes: "",
      });
    }
    return rows;
  }

  function selectedVehicle(layout) {
    if (!layout || !Array.isArray(layout.vehicles)) {
      return null;
    }
    return layout.vehicles.find((vehicle) => vehicle && vehicle.id === layout.selected_vehicle) || layout.vehicles[0] || null;
  }

  function obdPidDefinitionMap(definitions) {
    const mapped = {};
    for (const definition of Array.isArray(definitions) ? definitions : []) {
      const command = normalizeObdPidCommand(definition?.command || definition?.pid);
      if (command) {
        mapped[command] = definition;
      }
    }
    return mapped;
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

  function applyObdPidDefinition(item, definition) {
    if (!definition) {
      return item;
    }
    const rawBytes = String(item.rawBytes || (item.unit === "raw" ? item.value : "") || "");
    const decoded = decodeCustomObdValue(rawBytes, definition);
    return {
      ...item,
      label: definition.label || definition.name || item.label,
      unit: definition.unit !== undefined ? definition.unit : item.unit,
      statePath: definition.path || definition.statePath || item.statePath,
      rawBytes,
      value: decoded === undefined ? item.value : decoded,
    };
  }

  function decodeCustomObdValue(rawBytes, definition) {
    const byteLength = parseOptionalInt(definition?.byte_length ?? definition?.byteLength ?? definition?.length);
    if (!byteLength) {
      return undefined;
    }
    const bytes = String(rawBytes || "")
      .replace(/[^0-9a-f]/gi, "")
      .match(/.{1,2}/g)
      ?.map((item) => Number.parseInt(item, 16))
      .filter((item) => Number.isFinite(item)) || [];
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

  function formatObdValue(item) {
    const value = item?.value;
    const text = value === undefined || value === null || value === "" ? "--" : String(value);
    return item?.unit ? `${text} ${item.unit}` : text;
  }

  function renderList(parent, documentRef, rows, format) {
    parent.replaceChildren();
    if (!rows.length) {
      const empty = documentRef.createElement("div");
      empty.className = "empty-state compact";
      empty.textContent = "데이터 없음";
      parent.append(empty);
      return;
    }
    for (const row of rows) {
      const item = documentRef.createElement("div");
      item.className = "analysis-row";
      item.textContent = format(row);
      parent.append(item);
    }
  }

  function selectedBindingElement(state) {
    const selectedId = String(state.selectedId || "");
    return (state.layout?.elements || []).find((element) => element?.id === selectedId) || null;
  }

  function renderObdValueTable(parent, documentRef, rows, options = {}) {
    parent.replaceChildren();
    const doc = documentRef || parent.ownerDocument;
    const table = doc.createElement("div");
    table.className = "obd-value-table";
    table.setAttribute("role", "table");
    const header = doc.createElement("div");
    header.className = "obd-value-row obd-value-header";
    header.setAttribute("role", "row");
    for (const label of ["이름", "값", "PID", "경로", "작업"]) {
      const cell = doc.createElement("span");
      cell.setAttribute("role", "columnheader");
      cell.textContent = label;
      header.append(cell);
    }
    table.append(header);
    const visibleRows = (rows || []).filter((row) => row.value !== undefined && row.value !== null && row.value !== "");
    if (!visibleRows.length) {
      const empty = doc.createElement("div");
      empty.className = "obd-value-row obd-value-empty";
      empty.setAttribute("role", "row");
      empty.textContent = "아직 OBD 값이 없습니다. 연결 탭에서 OBD COM 새로고침을 누르고 시리얼 COM을 확인한 뒤 OBD 연결을 누르세요.";
      table.append(empty);
      parent.append(table);
      return;
    }
    for (const row of visibleRows) {
      const item = doc.createElement("div");
      item.className = "obd-value-row";
      item.setAttribute("role", "row");
      for (const value of [row.name, row.value, row.pid, row.detail]) {
        const cell = doc.createElement("span");
        cell.setAttribute("role", "cell");
        cell.textContent = value || "--";
        item.append(cell);
      }
      const actionCell = doc.createElement("span");
      actionCell.setAttribute("role", "cell");
      actionCell.className = "obd-value-action";
      actionCell.append(obdDefineButton(doc, row));
      actionCell.append(obdAssignButton(doc, row, options.selectedElement));
      item.append(actionCell);
      table.append(item);
    }
    parent.append(table);
  }

  function obdAssignButton(doc, row, selectedElement) {
    const button = doc.createElement("button");
    button.type = "button";
    button.className = "obd-bind-button";
    const binding = String(row.detail || "").trim();
    const enabled = Boolean(binding && selectedElement && supportsObdBindingAssignment(selectedElement));
    button.textContent = "연결";
    button.disabled = !enabled;
    button.title = binding
      ? enabled
        ? `${selectedElement.label || selectedElement.id || "선택 요소"}에 ${binding} 연결`
        : "먼저 값, 경고, 기어 HUD 요소를 선택하세요."
      : "이 행에는 HUD 연결 경로가 없습니다.";
    if (binding) {
      button.dataset.obdBinding = binding;
      button.dataset.obdLabel = row.name || binding;
    }
    return button;
  }

  function obdDefineButton(doc, row) {
    const button = doc.createElement("button");
    button.type = "button";
    button.className = "obd-define-button";
    const command = normalizeObdPidCommand(row.pid);
    button.textContent = "정의";
    button.disabled = !command;
    button.title = command ? `${command} 정의` : "Mode 01 PID 행만 정의할 수 있습니다.";
    if (command) {
      button.dataset.obdDefinePid = command;
      button.dataset.obdLabel = row.name || command;
      button.dataset.obdUnit = row.unit || "";
      button.dataset.obdPath = row.detail || "";
      button.dataset.obdRawBytes = row.rawBytes || "";
    }
    return button;
  }

  function supportsObdBindingAssignment(element) {
    const type = String(element?.type || "");
    return ["value", "warning_icon", "gear_indicator"].includes(type) || Object.prototype.hasOwnProperty.call(element || {}, "binding");
  }

  const api = {
    renderComPortList,
    renderObdDeviceList,
    renderObdSerialPortList,
    renderVehicleTools,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorVehicleLiveView = api;
})(typeof window !== "undefined" ? window : globalThis);
