const test = require("node:test");
const assert = require("node:assert/strict");

const VehicleLiveActions = require("../src/renderer/editorVehicleLiveActions.js");
const VehicleLiveState = require("../src/renderer/editorVehicleLiveState.js");

test("selectObdDeviceAndConnect inspects BLE UUIDs fills hidden config and starts OBD-only live session", async () => {
  const calls = [];
  const state = {
    layout: { selected_vehicle: "car", vehicles: [{ id: "car" }] },
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.obdDevices = [
    { address: "AA:BB:CC:DD:EE:FF", name: "V-LINK", rssi: -42 },
    { address: "11:22:33:44:55:66", name: "Keyboard", rssi: -70 },
  ];
  const dom = {
    obdEnabled: { checked: false },
    obdBleMac: { value: "" },
    obdBleRxUuid: { value: "" },
    obdBleTxUuid: { value: "" },
    obdTimeout: { value: "2" },
    canEnabled: { checked: true },
    canChannel: { value: "" },
    canBitrate: { value: "500000" },
    canListenOnly: { checked: true },
  };
  const service = {
    async inspectObdBle(payload) {
      calls.push(["inspect", payload]);
      return {
        ok: true,
        mac: payload.mac,
        pairs: [{ rx_uuid: "rx-uuid", tx_uuid: "tx-uuid" }],
      };
    },
    async startVehicleLive(config) {
      calls.push(["start", config]);
      return { ok: true };
    },
  };
  const deps = {
    renderVehicleTools: () => calls.push(["render"]),
    setStatus: (message, type) => calls.push(["status", message, type]),
    vehicleLiveState: VehicleLiveState,
  };

  const result = await VehicleLiveActions.selectObdDeviceAndConnectCommand(
    state,
    service,
    "AA:BB:CC:DD:EE:FF",
    dom,
    deps
  );

  assert.equal(result.ok, true);
  assert.equal(dom.obdEnabled.checked, true);
  assert.equal(dom.obdBleMac.value, "AA:BB:CC:DD:EE:FF");
  assert.equal(dom.obdBleRxUuid.value, "rx-uuid");
  assert.equal(dom.obdBleTxUuid.value, "tx-uuid");
  assert.equal(dom.canEnabled.checked, false);
  assert.deepEqual(state.vehicleLive.selectedObdDevice, { address: "AA:BB:CC:DD:EE:FF", name: "V-LINK", rssi: -42 });
  assert.deepEqual(state.vehicleLive.selectedObdPair, { rx_uuid: "rx-uuid", tx_uuid: "tx-uuid" });
  assert.equal(state.vehicleLive.obdConnectState, "connected");
  assert.deepEqual(calls[0], ["render"]);
  assert.deepEqual(calls[1], ["inspect", { mac: "AA:BB:CC:DD:EE:FF", timeoutSeconds: 5 }]);
  const startCall = calls.find((call) => call[0] === "start");
  assert.equal(startCall[1].obd.enabled, true);
  assert.equal(startCall[1].can.enabled, false);
});

test("scanComPorts stores connected COM devices and selecting a port fills CAN channel", async () => {
  const calls = [];
  const state = {
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  const dom = {
    canEnabled: { checked: false },
    canChannel: { value: "" },
  };
  const service = {
    async listComPorts() {
      calls.push(["listComPorts"]);
      return {
        ok: true,
        ports: [
          {
            device: "COM7",
            description: "CANable USB to CAN Adapter",
            manufacturer: "canable.io",
            product: "CANable",
            hwid: "USB VID:PID=1D50:606F",
            likelyCanable: true,
          },
        ],
      };
    },
  };
  const deps = {
    renderVehicleTools: () => calls.push(["render"]),
    setStatus: (message, type) => calls.push(["status", message, type]),
    vehicleLiveState: VehicleLiveState,
  };

  const scan = await VehicleLiveActions.scanComPortsCommand(state, service, deps);
  VehicleLiveActions.selectComPortCommand(state, "COM7", dom, deps);

  assert.equal(scan.ok, true);
  assert.equal(state.vehicleLive.comPorts.length, 1);
  assert.equal(state.vehicleLive.comPortScanState, "idle");
  assert.deepEqual(state.vehicleLive.selectedComPort.device, "COM7");
  assert.equal(dom.canChannel.value, "COM7@115200");
  assert.equal(dom.canEnabled.checked, true);
  assert.deepEqual(calls.map((call) => call[0]), ["render", "listComPorts", "render", "status", "render", "status"]);
});
