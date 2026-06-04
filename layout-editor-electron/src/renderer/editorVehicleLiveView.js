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
    writeStatus(dom.obdConnectionStatus, state.vehicleLive.status.obd);
    writeStatus(dom.canConnectionStatus, state.vehicleLive.status.can);
    renderObdSelection(state, dom, documentRef);
    renderComPortSelection(state, dom, documentRef);
  }

  function renderObdSelection(state, dom, documentRef) {
    if (!dom.obdDeviceList || !dom.obdSelectedStatus) {
      return;
    }
    const selected = state.vehicleLive.selectedObdDevice;
    dom.obdSelectedStatus.textContent = selected
      ? `${deviceLabel(selected)} · ${state.vehicleLive.obdConnectState || "selected"}`
      : "No OBD adapter selected";
    renderObdDeviceList(dom.obdDeviceList, documentRef, state.vehicleLive);
  }

  function renderObdDeviceList(parent, documentRef, vehicleLive) {
    const doc = documentRef || parent.ownerDocument;
    parent.replaceChildren();
    const devices = VehicleLiveState.sortedObdDevices(vehicleLive.obdDevices || []);
    if (!devices.length) {
      const empty = doc.createElement("div");
      empty.className = "empty-state compact";
      empty.textContent = vehicleLive.obdConnectState === "scanning" ? "Searching for Bluetooth devices..." : "Search Bluetooth to find nearby OBD adapters.";
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
    const selected = state.vehicleLive.selectedComPort;
    dom.comSelectedStatus.textContent = selected ? `${selected.device || "--"} · ${selected.description || "Serial device"}` : "No COM port selected";
    renderComPortList(dom.comPortList, documentRef, state.vehicleLive);
  }

  function renderComPortList(parent, documentRef, vehicleLive) {
    const doc = documentRef || parent.ownerDocument;
    parent.replaceChildren();
    const ports = VehicleLiveState.sortedComPorts(vehicleLive.comPorts || []);
    if (!ports.length) {
      const empty = doc.createElement("div");
      empty.className = "empty-state compact";
      if (vehicleLive.comPortScanState === "scanning") {
        empty.textContent = "Checking connected COM ports...";
      } else if (vehicleLive.comPortScanState === "error") {
        empty.textContent = vehicleLive.comPortLastError || "COM port scan failed";
      } else {
        empty.textContent = "Refresh COM ports to show connected USB serial or CANable devices.";
      }
      parent.append(empty);
      return;
    }
    for (const port of ports) {
      const row = doc.createElement("button");
      row.type = "button";
      row.className = "com-port-row";
      row.dataset.comPort = port.device || "";
      if (vehicleLive.selectedComPort?.device === port.device) {
        row.className += " selected";
      }
      row.setAttribute("data-com-port", port.device || "");
      row.setAttribute("role", "option");
      row.setAttribute("aria-selected", String(vehicleLive.selectedComPort?.device === port.device));
      row.textContent = comPortText(port);
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
      (item) => `${item.id} · count ${item.count} · changing bytes ${(item.changing_byte_indexes || []).join(",") || "--"}`
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
      writeStatus(dom.liveCanStatus, state.vehicleLive.status.can);
    }
    if (dom.liveObdStatus) {
      writeStatus(dom.liveObdStatus, state.vehicleLive.status.obd);
    }
    if (dom.liveSampleStatus) {
      dom.liveSampleStatus.textContent = Object.keys(state.vehicleLive.mergedState || {}).length ? "Live sample available" : "No live sample";
    }
    if (dom.liveLogList) {
      renderList(dom.liveLogList, documentRef, liveLogRows(state.vehicleLive), (item) => item);
    }
  }

  function renderObdAnalysisPanel(state, dom, documentRef) {
    const obd = state.vehicleLive.mergedState?.obd || {};
    const dtc = state.vehicleLive.mergedState?.dtc || {};
    dom.obdAdapterIdentity.textContent = obd.adapter_identity || "--";
    dom.obdProtocol.textContent = obd.protocol || "--";
    dom.obdSupportedPids.textContent = obd.supported_pid_bitmap || "--";
    dom.obdDtcList.textContent = formatDtc(dtc);
    renderList(
      dom.obdRecordList,
      documentRef,
      state.vehicleLive.obdRecords.slice(0, 30),
      (item) => `${item.ok ? "OK" : "FAIL"} ${item.command}: ${item.response || "--"}`
    );
    const debug = state.vehicleLive.mergedState?.debug || {};
    dom.obdLastRequest.textContent = debug.obd_request || "--";
    dom.obdLastResponse.textContent = debug.obd_response || "--";
  }

  function formatDtc(dtc) {
    const codes = [...(dtc.stored || []), ...(dtc.pending || []), ...(dtc.permanent || [])];
    if (!codes.length) {
      return dtc.count ? `${dtc.count} reported` : "--";
    }
    return codes.join(", ");
  }

  function writeStatus(node, status) {
    const state = status?.state || "idle";
    const detail = status?.detail ? ` · ${status.detail}` : "";
    const updated = status?.updatedAt ? ` · ${status.updatedAt}` : "";
    node.textContent = `${state}${detail}${updated}`;
    node.dataset.state = state;
  }

  function deviceLabel(device) {
    return String(device?.name || device?.address || "Unnamed device");
  }

  function comPortText(port) {
    const channel = port?.device ? `${port.device}@115200` : "--";
    return [channel, port?.description, port?.manufacturer, port?.product, port?.hwid].filter(Boolean).join(" · ");
  }

  function liveLogRows(vehicleLive) {
    const rows = [];
    for (const frame of (vehicleLive.canFrames || []).slice(0, 12)) {
      rows.push(`CAN ${frame.id || "--"}  ${frame.data || "--"}`);
    }
    for (const record of (vehicleLive.obdRecords || []).slice(0, 8)) {
      rows.push(`OBD ${record.ok ? "OK" : "FAIL"} ${record.command || "--"}: ${record.response || "--"}`);
    }
    return rows.slice(0, 20);
  }

  function renderList(parent, documentRef, rows, format) {
    parent.replaceChildren();
    if (!rows.length) {
      const empty = documentRef.createElement("div");
      empty.className = "empty-state compact";
      empty.textContent = "No data";
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

  const api = {
    renderComPortList,
    renderObdDeviceList,
    renderVehicleTools,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorVehicleLiveView = api;
})(typeof window !== "undefined" ? window : globalThis);
