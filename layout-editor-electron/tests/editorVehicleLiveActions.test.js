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
    obdSerialPort: { value: "COM8" },
    obdSerialBaud: { value: "38400" },
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
  assert.equal(dom.obdSerialPort.value, "");
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
  assert.equal(startCall[1].obd.port, "");
  assert.equal(startCall[1].obd.baud, 38400);
  assert.equal(startCall[1].can.enabled, false);
});

test("buildVehicleLiveConfig sends Classic Bluetooth serial OBD settings when present", () => {
  const state = {
    layout: { selected_vehicle: "car", vehicles: [{ id: "car" }] },
  };
  const dom = {
    obdEnabled: { checked: true },
    obdSerialPort: { value: "COM8" },
    obdSerialBaud: { value: "38400" },
    obdBleMac: { value: "41:42:86:9A:B0:3D" },
    obdBleRxUuid: { value: "rx" },
    obdBleTxUuid: { value: "tx" },
    obdTimeout: { value: "2" },
    canEnabled: { checked: false },
    canChannel: { value: "" },
    canBitrate: { value: "500000" },
    canListenOnly: { checked: true },
  };

  const config = VehicleLiveActions.buildVehicleLiveConfig(state, dom);

  assert.equal(config.obd.enabled, true);
  assert.equal(config.obd.port, "COM8");
  assert.equal(config.obd.baud, 38400);
  assert.equal(config.obd.mac, "41:42:86:9A:B0:3D");
  assert.equal(config.can.enabled, false);
});

test("startVehicleLiveCommand marks inputs connecting before worker start resolves", async () => {
  const calls = [];
  const state = {
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  const config = {
    obd: { enabled: true, port: "COM5" },
    can: { enabled: true, channel: "COM3@115200" },
  };
  const service = {
    async startVehicleLive(actualConfig) {
      calls.push(["start", actualConfig, state.vehicleLive.status.obd.state, state.vehicleLive.status.can.state]);
      return { ok: true };
    },
  };
  const deps = {
    renderVehicleTools: () => calls.push(["render", state.vehicleLive.status.obd.state, state.vehicleLive.status.can.state]),
    setStatus: (message, type) => calls.push(["status", message, type]),
    vehicleLiveState: VehicleLiveState,
  };

  await VehicleLiveActions.startVehicleLiveCommand(state, service, config, deps);

  assert.deepEqual(calls[0], ["render", "connecting", "connecting"]);
  assert.deepEqual(calls[1], ["start", config, "connecting", "connecting"]);
  assert.equal(state.vehicleLive.status.obd.state, "connecting");
  assert.equal(state.vehicleLive.status.can.state, "connecting");
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
  assert.equal(state.vehicleLive.canComPorts.length, 1);
  assert.equal(state.vehicleLive.obdComPorts.length, 0);
  assert.equal(state.vehicleLive.comPortScanState, "idle");
  assert.deepEqual(state.vehicleLive.selectedComPort.device, "COM7");
  assert.deepEqual(state.vehicleLive.selectedCanPort.device, "COM7");
  assert.equal(dom.canChannel.value, "COM7@115200");
  assert.equal(dom.canEnabled.checked, true);
  assert.deepEqual(calls.map((call) => call[0]), ["render", "listComPorts", "render", "status", "render", "status"]);
});

test("selectComPort routes OBD Bluetooth serial ports to OBD instead of CAN", () => {
  const calls = [];
  const state = {
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.comPorts = [
    { device: "COM3", description: "CANtact USB/CAN Device", likelyCanable: true },
    { device: "COM5", description: "Standard Serial over Bluetooth link", hwid: "BTHENUM 4142869AB068", likelyObdSerial: true },
  ];
  const dom = {
    obdEnabled: { checked: false },
    obdSerialPort: { value: "" },
    obdSerialBaud: { value: "" },
    obdBleMac: { value: "41:42:86:9A:B0:3D" },
    obdBleRxUuid: { value: "rx" },
    obdBleTxUuid: { value: "tx" },
    canEnabled: { checked: true },
    canChannel: { value: "COM5@115200" },
  };
  const deps = {
    renderVehicleTools: () => calls.push(["render"]),
    setStatus: (message, type) => calls.push(["status", message, type]),
    vehicleLiveState: VehicleLiveState,
  };

  VehicleLiveActions.selectComPortCommand(state, "COM5", dom, deps);

  assert.equal(dom.obdEnabled.checked, true);
  assert.equal(dom.obdSerialPort.value, "COM5");
  assert.equal(state.vehicleLive.selectedObdSerialPort.device, "COM5");
  assert.equal(dom.obdSerialBaud.value, "38400");
  assert.equal(dom.obdBleMac.value, "");
  assert.equal(dom.obdBleRxUuid.value, "");
  assert.equal(dom.obdBleTxUuid.value, "");
  assert.equal(dom.canEnabled.checked, false);
  assert.equal(dom.canChannel.value, "");
  assert.deepEqual(calls.at(-1), ["status", "OBD 시리얼로 COM5 선택", "ok"]);
});

test("prepareVehicleLiveDomForStart repairs an OBD serial port misplaced in CAN channel", () => {
  const state = {
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.comPorts = [
    { device: "COM5", description: "Standard Serial over Bluetooth link", likelyObdSerial: true },
  ];
  const dom = {
    obdEnabled: { checked: false },
    obdSerialPort: { value: "" },
    obdSerialBaud: { value: "38400" },
    obdBleMac: { value: "" },
    obdBleRxUuid: { value: "" },
    obdBleTxUuid: { value: "" },
    canEnabled: { checked: true },
    canChannel: { value: "COM5@115200" },
  };

  const port = VehicleLiveActions.prepareVehicleLiveDomForStart(state, dom);

  assert.equal(port.device, "COM5");
  assert.equal(dom.obdEnabled.checked, true);
  assert.equal(dom.obdSerialPort.value, "COM5");
  assert.equal(state.vehicleLive.selectedObdSerialPort.device, "COM5");
  assert.equal(state.vehicleLive.selectedCanPort, null);
  assert.equal(dom.canEnabled.checked, false);
  assert.equal(dom.canChannel.value, "");
});

test("buildVehicleLiveConfig does not open the same COM device as both OBD and CAN", () => {
  const state = {
    layout: { selected_vehicle: "car", vehicles: [{ id: "car" }] },
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.comPorts = [
    { device: "COM5", description: "Standard Serial over Bluetooth link", likelyObdSerial: true },
  ];
  const dom = {
    obdEnabled: { checked: true },
    obdSerialPort: { value: "COM5" },
    obdSerialBaud: { value: "38400" },
    obdBleMac: { value: "" },
    obdBleRxUuid: { value: "" },
    obdBleTxUuid: { value: "" },
    obdTimeout: { value: "2" },
    canEnabled: { checked: true },
    canChannel: { value: "COM5@115200" },
    canBitrate: { value: "500000" },
    canListenOnly: { checked: true },
  };

  const config = VehicleLiveActions.buildVehicleLiveConfig(state, dom);

  assert.equal(config.obd.enabled, true);
  assert.equal(config.obd.port, "COM5");
  assert.equal(config.can.enabled, false);
});

test("scanComPorts treats CANtact driver ports as CAN adapters", async () => {
  const state = {
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  const service = {
    async listComPorts() {
      return {
        ok: true,
        ports: [
          { device: "COM9", description: "Bluetooth Serial Port", hwid: "BTHENUM" },
          {
            device: "COM3",
            description: "CANtact USB/CAN Device(COM3)",
            manufacturer: "http://www.cantact.io",
            hwid: "USB VID:PID=16D0:117E",
            likelyCanable: true,
          },
        ],
      };
    },
  };
  const deps = {
    renderVehicleTools: () => {},
    setStatus: () => {},
    vehicleLiveState: VehicleLiveState,
  };

  const scan = await VehicleLiveActions.scanComPortsCommand(state, service, deps);

  assert.equal(scan.ok, true);
  assert.equal(state.vehicleLive.comPorts[0].device, "COM3");
  assert.equal(state.vehicleLive.canComPorts[0].device, "COM3");
});

test("scanComPorts auto-fills Android Vlink Bluetooth serial port for OBD", async () => {
  const calls = [];
  const state = {
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  const dom = {
    obdEnabled: { checked: false },
    obdSerialPort: { value: "" },
    obdSerialBaud: { value: "38400" },
    obdBleMac: { value: "41:42:86:9A:B0:3D" },
    obdBleRxUuid: { value: "rx" },
    obdBleTxUuid: { value: "tx" },
  };
  const service = {
    async listComPorts() {
      return {
        ok: true,
        ports: [
          { device: "COM3", description: "CANtact USB/CAN Device", likelyCanable: true },
          { device: "COM4", description: "Standard Serial over Bluetooth link", hwid: "BTHENUM 000000000000_00000000" },
          { device: "COM5", description: "Standard Serial over Bluetooth link", hwid: "BTHENUM 4142869AB068", likelyObdSerial: true },
        ],
      };
    },
  };
  const deps = {
    renderVehicleTools: () => calls.push(["render"]),
    setStatus: (message, type) => calls.push(["status", message, type]),
    vehicleLiveState: VehicleLiveState,
  };

  await VehicleLiveActions.scanComPortsCommand(state, service, dom, deps);

  assert.equal(dom.obdEnabled.checked, true);
  assert.equal(dom.obdSerialPort.value, "COM5");
  assert.equal(state.vehicleLive.obdComPorts.length, 1);
  assert.equal(state.vehicleLive.obdComPorts[0].device, "COM5");
  assert.match(state.vehicleLive.lastObdComScanSummary, /3개 포트 중 후보 1개/);
  assert.equal(state.vehicleLive.canComPorts.length, 0);
  assert.equal(state.vehicleLive.selectedObdSerialPort.device, "COM5");
  assert.equal(dom.obdBleMac.value, "");
  assert.equal(dom.obdBleRxUuid.value, "");
  assert.equal(dom.obdBleTxUuid.value, "");
  assert.match(calls.at(-1)[1], /OBD 시리얼 COM5 선택됨/);
});

test("scanComPorts can refresh CAN candidates without changing OBD serial selection", async () => {
  const state = {
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  const dom = {
    obdEnabled: { checked: false },
    obdSerialPort: { value: "" },
    obdSerialBaud: { value: "38400" },
    obdBleMac: { value: "" },
    obdBleRxUuid: { value: "" },
    obdBleTxUuid: { value: "" },
  };
  const service = {
    async listComPorts() {
      return {
        ok: true,
        ports: [
          { device: "COM3", description: "CANtact USB/CAN Device", likelyCanable: true },
          { device: "COM5", description: "Standard Serial over Bluetooth link", likelyObdSerial: true },
        ],
      };
    },
  };
  const deps = {
    renderVehicleTools: () => {},
    setStatus: () => {},
    vehicleLiveState: VehicleLiveState,
  };

  await VehicleLiveActions.scanComPortsCommand(state, service, dom, deps, { autoFillObdSerial: false });

  assert.equal(dom.obdSerialPort.value, "");
  assert.equal(state.vehicleLive.selectedObdSerialPort, null);
  assert.equal(state.vehicleLive.comPorts.length, 2);
  assert.equal(state.vehicleLive.canComPorts.length, 1);
  assert.equal(state.vehicleLive.canComPorts[0].device, "COM3");
  assert.match(state.vehicleLive.lastCanComScanSummary, /2개 포트 중 후보 1개/);
  assert.equal(state.vehicleLive.obdComPorts.length, 0);
});

test("assignObdBindingCommand binds an OBD value path to the selected HUD element", () => {
  const calls = [];
  const state = {
    layout: {
      elements: [{ id: "rpm", type: "value", label: "RPM", binding: "vehicle.old_rpm", palette_key: "old" }],
    },
  };
  const element = state.layout.elements[0];
  const deps = {
    markDirty: () => calls.push(["markDirty"]),
    recordHistory: () => calls.push(["recordHistory"]),
    renderAll: () => calls.push(["renderAll"]),
    renderLayers: () => calls.push(["renderLayers"]),
    renderOverlay: () => calls.push(["renderOverlay"]),
    renderProperties: () => calls.push(["renderProperties"]),
    schedulePreview: (delay) => calls.push(["schedulePreview", delay]),
    setStatus: (message, type) => calls.push(["status", message, type]),
  };

  const changed = VehicleLiveActions.assignObdBindingCommand(state, "vehicle.rpm", element, deps, "Engine RPM");

  assert.equal(changed, true);
  assert.equal(element.binding, "vehicle.rpm");
  assert.equal("palette_key" in element, false);
  assert.deepEqual(calls.map((call) => call[0]), [
    "recordHistory",
    "markDirty",
    "renderAll",
    "renderProperties",
    "renderLayers",
    "renderOverlay",
    "schedulePreview",
    "status",
  ]);
  assert.deepEqual(calls.at(-1), ["status", "Engine RPM을 RPM에 연결했습니다.", "ok"]);
});

test("assignObdBindingCommand asks for a selected HUD element", () => {
  const calls = [];
  const deps = {
    setStatus: (message, type) => calls.push(["status", message, type]),
  };

  const changed = VehicleLiveActions.assignObdBindingCommand({}, "vehicle.rpm", null, deps, "Engine RPM");

  assert.equal(changed, false);
  assert.deepEqual(calls, [["status", "먼저 캔버스에서 HUD 요소를 선택하세요.", "error"]]);
});

test("saveObdPidDefinitionCommand stores a manual PID decoder and applies the live raw value", () => {
  const calls = [];
  const state = {
    simulationEnabled: true,
    layout: { selected_vehicle: "car", vehicles: [{ id: "car" }] },
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };
  state.vehicleLive.obdRecords = [{ command: "0149", response: "41 49 80", ok: true }];
  state.vehicleLive.mergedState = { obd: { values: [] } };
  const deps = {
    markDirty: () => calls.push(["dirty"]),
    recordHistory: () => calls.push(["history"]),
    renderVehicleTools: () => calls.push(["render"]),
    schedulePreview: (delay) => calls.push(["preview", delay]),
    setStatus: (message, type) => calls.push(["status", message, type]),
    vehicleLiveState: VehicleLiveState,
  };

  const result = VehicleLiveActions.saveObdPidDefinitionCommand(
    state,
    {
      command: "49",
      label: "Pedal position",
      unit: "%",
      path: "vehicle.pedal_pct",
      byteLength: "1",
      scale: String(100 / 255),
      offset: "0",
      endian: "big",
      referenceValue: "50 %",
    },
    deps
  );

  assert.equal(result, true);
  assert.equal(state.layout.vehicles[0].obd_pid_definitions[0].command, "0149");
  assert.equal(state.layout.vehicles[0].obd_pid_definitions[0].path, "vehicle.pedal_pct");
  assert.equal(state.layout.vehicles[0].obd_pid_definitions[0].reference_value, "50 %");
  assert.equal(state.vehicleLive.mergedState.vehicle.pedal_pct, 50.1961);
  assert.deepEqual(state.vehicleLive.mergedState.obd.values[0], {
    command: "0149",
    label: "Pedal position",
    value: 50.1961,
    unit: "%",
    statePath: "vehicle.pedal_pct",
    rawBytes: "80",
    custom: true,
  });
  assert.deepEqual(calls.map((call) => call[0]), ["history", "dirty", "render", "preview", "status"]);
});

test("editObdPidDefinitionCommand fills the manual PID editor from a raw value row", () => {
  const calls = [];
  const dom = {
    obdPidCommand: { value: "" },
    obdPidLabel: { value: "" },
    obdPidReferenceValue: { value: "old" },
    obdPidUnit: { value: "" },
    obdPidPath: { value: "" },
    obdPidByteIndex: { value: "1" },
    obdPidLength: { value: "2" },
    obdPidScale: { value: "3" },
    obdPidOffset: { value: "4" },
    obdPidEndian: { value: "" },
    obdPidSigned: { checked: true },
  };
  const deps = {
    setStatus: (message, type) => calls.push(["status", message, type]),
  };

  const result = VehicleLiveActions.editObdPidDefinitionCommand(
    dom,
    { command: "0149", label: "Mode 01 PID 49", unit: "raw", rawBytes: "80" },
    deps
  );

  assert.equal(result, true);
  assert.equal(dom.obdPidCommand.value, "0149");
  assert.equal(dom.obdPidLabel.value, "");
  assert.equal(dom.obdPidUnit.value, "");
  assert.equal(dom.obdPidPath.value, "vehicle.obd_0149");
  assert.equal(dom.obdPidByteIndex.value, "");
  assert.equal(dom.obdPidEndian.value, "big");
  assert.equal(dom.obdPidSigned.checked, false);
  assert.deepEqual(calls, [["status", "0149 Raw 80 불러옴", "ok"]]);
});
