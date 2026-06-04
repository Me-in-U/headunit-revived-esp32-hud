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
  state.vehicleLive.comPorts = [
    { device: "COM9", description: "Bluetooth Serial Port", hwid: "BTHENUM" },
    { device: "COM3", description: "CANable USB to CAN Adapter", manufacturer: "canable.io", hwid: "USB VID:PID=1D50:606F", likelyCanable: true },
  ];
  state.vehicleLive.selectedObdDevice = { address: "AA:BB:CC:DD:EE:FF", name: "ELM327", rssi: -41 };
  state.vehicleLive.selectedComPort = { device: "COM3", description: "CANable USB to CAN Adapter", manufacturer: "canable.io", hwid: "USB VID:PID=1D50:606F", likelyCanable: true };
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
  assert.equal(dom.comPortList.children.length, 2);
  assert.equal(dom.comPortList.children[0].dataset.comPort, "COM3");
  assert.match(dom.comPortList.children[0].textContent, /CANable USB/);
  assert.match(dom.comPortList.children[0].textContent, /COM3@115200/);
  assert.equal(dom.comPortList.children[0].className.includes("selected"), true);
  assert.equal(dom.comSelectedStatus.textContent, "COM3 · CANable USB to CAN Adapter");
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
  assert.equal(dom.liveCanStatus.textContent, "live · COM3@115200 · 12:30:01");
  assert.equal(dom.liveObdStatus.textContent, "live · ELM327 · 12:30:02");
  assert.equal(dom.liveSampleStatus.textContent, "Live sample available");
  assert.equal(dom.liveLogList.children.length, 2);
  assert.match(dom.liveLogList.children[0].textContent, /CAN 0x316/);
  assert.match(dom.liveLogList.children[1].textContent, /OBD OK 010C/);
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
    obdSelectedStatus: fakeElement(),
    comPortList: fakeElement(),
    comSelectedStatus: fakeElement(),
    canFrameCount: fakeElement(),
    canLastId: fakeElement(),
    canSummaryList: fakeElement(),
    canFrameList: fakeElement(),
    canDecodedPreview: fakeElement(),
    obdAdapterIdentity: fakeElement(),
    obdProtocol: fakeElement(),
    obdSupportedPids: fakeElement(),
    obdDtcList: fakeElement(),
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
