const test = require("node:test");
const assert = require("node:assert/strict");

const VehicleLiveState = require("../src/renderer/editorVehicleLiveState.js");
const VehicleLiveView = require("../src/renderer/editorVehicleLiveView.js");

test("renderVehicleTools shows sorted selectable OBD BLE devices and selected device status", () => {
  const state = {
    simulationEnabled: false,
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.activeTab = "connection";
  state.vehicleLive.obdDevices = [
    { address: "11:22:33:44:55:66", name: "Keyboard", rssi: -71 },
    { address: "AA:BB:CC:DD:EE:FF", name: "ELM327", rssi: -41 },
  ];
  state.vehicleLive.obdComPorts = [
    { device: "COM5", description: "Bluetooth Serial Port", hwid: "BTHENUM 4142869AB068", likelyObdSerial: true },
  ];
  state.vehicleLive.canComPorts = [
    { device: "COM3", description: "CANable USB to CAN Adapter", manufacturer: "canable.io", hwid: "USB VID:PID=1D50:606F", likelyCanable: true },
  ];
  state.vehicleLive.selectedObdDevice = { address: "AA:BB:CC:DD:EE:FF", name: "ELM327", rssi: -41 };
  state.vehicleLive.selectedCanPort = { device: "COM3", description: "CANable USB to CAN Adapter", manufacturer: "canable.io", hwid: "USB VID:PID=1D50:606F", likelyCanable: true };
  state.vehicleLive.selectedObdSerialPort = { device: "COM5", description: "Bluetooth Serial Port", hwid: "BTHENUM 4142869AB068", likelyObdSerial: true };
  state.vehicleLive.obdConnectState = "connected";
  const dom = vehicleDom();

  VehicleLiveView.renderVehicleTools(state, dom, { documentRef: fakeDocument() });

  assert.equal(dom.connectionPanel.hidden, false);
  assert.equal(dom.obdDeviceList.children.length, 2);
  assert.equal(dom.obdDeviceList.children[0].dataset.obdAddress, "AA:BB:CC:DD:EE:FF");
  assert.match(dom.obdDeviceList.children[0].textContent, /ELM327/);
  assert.match(dom.obdDeviceList.children[0].textContent, /-41 dBm/);
  assert.equal(dom.obdDeviceList.children[0].className.includes("selected"), true);
  assert.equal(dom.obdSelectedStatus.textContent, "ELM327 · connected");
  assert.equal(dom.obdSerialPortList.children.length, 1);
  assert.equal(dom.obdSerialPortList.children[0].dataset.obdSerialPort, "COM5");
  assert.match(dom.obdSerialPortList.children[0].textContent, /OBD Bluetooth/);
  assert.equal(dom.comPortList.children.length, 1);
  assert.equal(dom.comPortList.children[0].dataset.comPort, "COM3");
  assert.match(dom.comPortList.children[0].textContent, /CANable USB/);
  assert.match(dom.comPortList.children[0].textContent, /COM3/);
  assert.match(dom.comPortList.children[0].textContent, /CAN 어댑터/);
  assert.match(dom.comPortList.children[0].title, /COM3@115200/);
  assert.equal(dom.comPortList.children[0].className.includes("selected"), true);
  assert.equal(dom.comSelectedStatus.textContent, "COM3 · CANable USB to CAN Adapter");
});

test("renderVehicleTools keeps OBD and CAN COM lists independent even when raw scan cache has both", () => {
  const state = {
    simulationEnabled: false,
    selectedId: "speed",
    layout: { elements: [{ id: "speed", type: "value", label: "Speed", binding: "vehicle.old_speed" }] },
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.activeTab = "connection";
  state.vehicleLive.comPorts = [
    { device: "COM5", description: "Bluetooth Serial Port", likelyObdSerial: true },
    { device: "COM3", description: "CANtact USB/CAN Device", likelyCanable: true },
  ];
  state.vehicleLive.canComPorts = [
    { device: "COM3", description: "CANtact USB/CAN Device", likelyCanable: true },
  ];
  const dom = vehicleDom();

  VehicleLiveView.renderVehicleTools(state, dom, { documentRef: fakeDocument() });

  assert.equal(dom.comPortList.children.length, 1);
  assert.equal(dom.comPortList.children[0].dataset.comPort, "COM3");
  assert.equal(dom.obdSerialPortList.children.length, 1);
  assert.match(dom.obdSerialPortList.children[0].textContent, /OBD COM 새로고침/);
});

test("renderVehicleTools shows OBD COM scan summary when no OBD candidate is found", () => {
  const state = {
    simulationEnabled: false,
    selectedId: "rpm",
    layout: {
      elements: [{ id: "rpm", type: "value", label: "RPM", binding: "vehicle.old_rpm" }],
    },
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.activeTab = "connection";
  state.vehicleLive.lastObdComScanSummary = "OBD COM scan complete: no OBD candidates from 2 port(s). Raw: COM3, COM7";
  const dom = vehicleDom();

  VehicleLiveView.renderVehicleTools(state, dom, { documentRef: fakeDocument() });

  assert.equal(dom.obdSerialPortList.children.length, 1);
  assert.match(dom.obdSerialPortList.children[0].textContent, /no OBD candidates/);
  assert.match(dom.obdSerialPortList.children[0].textContent, /COM3, COM7/);
});

test("renderVehicleTools moves live sample state and recent live events into CAN analysis rail", () => {
  const state = {
    simulationEnabled: false,
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.activeTab = "can";
  state.vehicleLive.status.can = { state: "live", detail: "COM3@115200", updatedAt: "12:30:01" };
  state.vehicleLive.status.obd = { state: "live", detail: "ELM327", updatedAt: "12:30:02" };
  state.vehicleLive.mergedState = { vehicle: { speed_kmh: 42 } };
  state.vehicleLive.canFrames = [
    { id: "0x316", data: "05 20 00 00 00 00 00 00" },
  ];
  state.vehicleLive.obdRecords = [
    { ok: true, command: "010C", response: "41 0C 1A F8" },
  ];
  const dom = vehicleDom();

  VehicleLiveView.renderVehicleTools(state, dom, { documentRef: fakeDocument() });

  assert.equal(dom.connectionPanel.hidden, true);
  assert.equal(dom.canAnalysisPanel.hidden, false);
  assert.equal(dom.liveCanStatus.textContent, "연결됨 · COM3@115200 · 12:30:01");
  assert.equal(dom.liveObdStatus.textContent, "연결됨 · ELM327 · 12:30:02");
  assert.equal(dom.liveSampleStatus.textContent, "실시간 샘플 있음");
  assert.equal(dom.liveLogList.children.length, 2);
  assert.match(dom.liveLogList.children[0].textContent, /CAN 0x316/);
  assert.match(dom.liveLogList.children[1].textContent, /OBD OK 010C/);
});

test("renderVehicleTools shows CAN stale detail when no frames are available", () => {
  const state = {
    simulationEnabled: false,
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.activeTab = "can";
  state.vehicleLive.status.can = {
    state: "stale",
    detail: "No CAN frames on COM3 @ 500000 bps listen-only. Check IGN ON.",
    updatedAt: "12:31:01",
  };
  const dom = vehicleDom();

  VehicleLiveView.renderVehicleTools(state, dom, { documentRef: fakeDocument() });

  assert.equal(dom.liveLogList.children.length, 1);
  assert.match(dom.liveLogList.children[0].textContent, /CAN stale: No CAN frames/);
  assert.match(dom.liveCanStatus.textContent, /대기 중/);
});

test("renderVehicleTools shows decoded OBD values separately from raw responses", () => {
  const state = {
    simulationEnabled: false,
    selectedId: "rpm",
    layout: {
      elements: [{ id: "rpm", type: "value", label: "RPM", binding: "vehicle.old_rpm" }],
    },
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.activeTab = "obd";
  state.vehicleLive.mergedState = {
    obd: {
      adapter_identity: "ELM327 v1.5",
      protocol: "ISO 15765-4",
      supported_pid_count: 3,
      supported_pids: ["010C", "010D", "0142"],
      values: [
        { command: "010D", label: "Vehicle speed", value: 42, unit: "km/h", statePath: "vehicle.speed_kmh" },
        { command: "010C", label: "Engine RPM", value: 1726, unit: "rpm", statePath: "vehicle.rpm" },
      ],
    },
    dtc: { stored: [], pending: [], permanent: [], count: 0 },
    debug: { obd_request: "010D", obd_response: "41 0D 2A" },
  };
  state.vehicleLive.obdRecords = [
    { ok: true, command: "010D", response: "41 0D 2A" },
  ];
  const dom = vehicleDom();

  VehicleLiveView.renderVehicleTools(state, dom, { documentRef: fakeDocument() });

  assert.equal(dom.obdAnalysisPanel.hidden, false);
  assert.match(dom.obdSupportedPids.textContent, /3 PIDs/);
  assert.equal(dom.obdValueList.children.length, 1);
  assert.equal(dom.obdValueList.children[0].className, "obd-value-table");
  assert.equal(dom.obdValueList.children[0].children.length, 8);
  assert.match(dom.obdValueList.children[0].children[0].textContent, /이름/);
  assert.match(dom.obdValueList.textContent, /Engine RPM/);
  assert.match(dom.obdValueList.textContent, /1726 rpm/);
  assert.match(dom.obdValueList.textContent, /지원 PID 0142/);
  assert.match(dom.obdValueList.textContent, /어댑터/);
  const rpmRow = dom.obdValueList.children[0].children.find((row) => /Engine RPM/.test(row.textContent));
  const defineButton = rpmRow.children[4].children[0];
  const assignButton = rpmRow.children[4].children[1];
  assert.equal(defineButton.dataset.obdDefinePid, "010C");
  assert.equal(defineButton.dataset.obdLabel, "Engine RPM");
  assert.equal(assignButton.disabled, false);
  assert.equal(assignButton.dataset.obdBinding, "vehicle.rpm");
  assert.equal(assignButton.dataset.obdLabel, "Engine RPM");
  assert.match(dom.obdRecordList.children[0].textContent, /OK 010D/);
});

function vehicleDom() {
  const dom = {
    elementsTab: fakeElement(),
    connectionTab: fakeElement(),
    canAnalysisTab: fakeElement(),
    obdAnalysisTab: fakeElement(),
    elementsPanel: fakeElement(),
    connectionPanel: fakeElement(),
    canAnalysisPanel: fakeElement(),
    obdAnalysisPanel: fakeElement(),
    simulationToggle: { checked: false },
    obdConnectionStatus: fakeElement(),
    canConnectionStatus: fakeElement(),
    liveSampleStatus: fakeElement(),
    liveCanStatus: fakeElement(),
    liveObdStatus: fakeElement(),
    liveLogList: fakeElement(),
    obdDeviceList: fakeElement(),
    obdSerialPortList: fakeElement(),
    obdSelectedStatus: fakeElement(),
    comPortList: fakeElement(),
    comSelectedStatus: fakeElement(),
    canFrameCount: fakeElement(),
    canLastId: fakeElement(),
    canSummaryList: fakeElement(),
    canFrameList: fakeElement(),
    canDecodedPreview: fakeElement(),
    obdAdapterIdentity: fakeElement(),
    obdAnalysisStatus: fakeElement(),
    obdProtocol: fakeElement(),
    obdSupportedPids: fakeElement(),
    obdDtcList: fakeElement(),
    obdValueList: fakeElement(),
    obdRecordList: fakeElement(),
    obdLastRequest: fakeElement(),
    obdLastResponse: fakeElement(),
  };
  return dom;
}

function fakeDocument() {
  return {
    createElement() {
      return fakeElement();
    },
  };
}

function fakeElement() {
  return {
    children: [],
    className: "",
    dataset: {},
    hidden: false,
    textContent: "",
    title: "",
    classList: {
      toggle() {},
    },
    setAttribute() {},
    append(...nodes) {
      this.children.push(...nodes);
      this.textContent += nodes.map((node) => node.textContent || "").join("");
    },
    replaceChildren(...nodes) {
      this.children = nodes;
      this.textContent = nodes.map((node) => node.textContent || "").join("");
    },
  };
}
