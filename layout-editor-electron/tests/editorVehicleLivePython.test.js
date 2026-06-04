const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

function pythonExecutable() {
  const root = path.resolve(__dirname, "..", "..");
  const venvPython = path.join(root, "pi-hud", ".venv", "Scripts", "python.exe");
  return fs.existsSync(venvPython) ? venvPython : "python";
}

test("Python editor vehicle live helpers open CANable as Windows SLCAN", () => {
  const script = [
    "import json",
    "from editor_vehicle_live import build_can_bus_kwargs, open_can_bus",
    "class FakeInterface:",
    "    def __init__(self):",
    "        self.calls = []",
    "    def Bus(self, **kwargs):",
    "        self.calls.append(kwargs)",
    "        return {'bus': kwargs}",
    "class FakeCan:",
    "    def __init__(self):",
    "        self.interface = FakeInterface()",
    "fake = FakeCan()",
    "config = {'interface': 'slcan', 'channel': 'COM7@115200', 'bitrate': 500000, 'listenOnly': True}",
    "bus = open_can_bus(fake, config)",
    "print(json.dumps({'kwargs': build_can_bus_kwargs(config), 'call': fake.interface.calls[0], 'bus': bus['bus']}))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.deepEqual(payload.kwargs, {
    channel: "COM7@115200",
    interface: "slcan",
    bitrate: 500000,
    listen_only: true,
  });
  assert.deepEqual(payload.call, payload.kwargs);
  assert.deepEqual(payload.bus, payload.kwargs);
});

test("Python editor vehicle live worker emits status state and CAN summary events", () => {
  const script = [
    "import json",
    "from editor_vehicle_live import VehicleLiveSession",
    "class FakeMessage:",
    "    def __init__(self):",
    "        self.arbitration_id = 0x316",
    "        self.data = bytes([5, 32, 0, 255])",
    "        self.dlc = 4",
    "        self.timestamp = 123.4",
    "        self.is_extended_id = False",
    "class FakeBus:",
    "    def __init__(self):",
    "        self.done = False",
    "    def recv(self, timeout=0.5):",
    "        if self.done:",
    "            return None",
    "        self.done = True",
    "        return FakeMessage()",
    "    def shutdown(self):",
    "        pass",
    "events = []",
    "session = VehicleLiveSession(",
    "    {'can': {'enabled': True}, 'layout': {'selected_vehicle': 'car', 'vehicles': [{'id': 'car', 'can_signals': [{'confirmed': True, 'frame_id': '0x316', 'name': 'vehicle.gear_actual', 'start_byte': 1, 'length': 1}]}]}},",
    "    emit=events.append,",
    "    can_bus_factory=lambda config: FakeBus(),",
    ")",
    "session.run_can_once()",
    "print(json.dumps(events))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const events = JSON.parse(result.stdout);
  assert.equal(events[0].type, "status");
  assert.equal(events[0].source, "can");
  assert.equal(events[0].state, "connecting");
  assert.equal(events.some((event) => event.type === "can_frame" && event.record.id === "0x316"), true);
  assert.equal(events.some((event) => event.type === "can_summary" && event.summary.unique_id_count === 1), true);
  const stateEvent = events.find((event) => event.type === "state");
  assert.equal(stateEvent.source, "can");
  assert.equal(stateEvent.update.vehicle.gear_actual, 32);
  assert.equal(stateEvent.mergedState.vehicle.gear_actual, 32);
});

test("Python editor owns CAN analysis summaries outside Pi runtime modules", () => {
  const script = [
    "import json",
    "from editor_can_analysis import summarize_can_records",
    "records = [",
    "    {'timestamp': 1.0, 'arbitration_id': 0x316, 'id': '0x316', 'dlc': 4, 'data': '05 20 00 FF'},",
    "    {'timestamp': 1.1, 'arbitration_id': 0x316, 'id': '0x316', 'dlc': 4, 'data': '05 21 00 FF'},",
    "    {'timestamp': 1.2, 'arbitration_id': 0x329, 'id': '0x329', 'dlc': 2, 'data': '10 00'},",
    "]",
    "print(json.dumps(summarize_can_records(records)))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const summary = JSON.parse(result.stdout);
  assert.equal(summary.frame_count, 3);
  assert.equal(summary.unique_id_count, 2);
  assert.deepEqual(summary.ids[0].changing_byte_indexes, [1]);
  assert.deepEqual(summary.ids[0].sample_data, ["05 20 00 FF", "05 21 00 FF"]);
});

test("Python editor vehicle live OBD update includes adapter protocol supported PIDs and DTCs", () => {
  const script = [
    "import json",
    "from editor_vehicle_live import OBD_LIVE_COMMANDS, build_obd_live_update",
    "responses = {",
    "    'ATI': 'ELM327 v1.5',",
    "    'ATDP': 'ISO 15765-4 CAN (11 bit ID, 500 kbaud)',",
    "    '0100': '41 00 BE 1F A8 13',",
    "    '0101': '41 01 81 07 65 04',",
    "    '010C': '41 0C 1A F8',",
    "    '010D': '41 0D 2A',",
    "    '0105': '41 05 78',",
    "    '0142': '41 42 34 98',",
    "    '03': '43 01 33 00 00 00 00',",
    "    '07': '47 00 00 00 00 00 00',",
    "    '0A': '4A 00 00 00 00 00 00',",
    "}",
    "records = [{'command': command, 'response': responses.get(command, ''), 'ok': True} for command in OBD_LIVE_COMMANDS]",
    "print(json.dumps(build_obd_live_update(records)))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const update = JSON.parse(result.stdout);
  assert.equal(update.obd.adapter_identity, "ELM327 v1.5");
  assert.match(update.obd.protocol, /ISO 15765-4/);
  assert.equal(update.obd.supported_pid_bitmap, "41 00 BE 1F A8 13");
  assert.equal(update.vehicle.speed_kmh, 42);
  assert.deepEqual(update.dtc.stored, ["P0133"]);
});

test("Python BLE bridge commands avoid renderer imports before scanning", () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "hud-ble-bridge-"));
  fs.writeFileSync(path.join(tempDir, "pygame.py"), "raise RuntimeError('pygame import should be lazy for BLE scan')\n");
  fs.mkdirSync(path.join(tempDir, "bleak"));
  fs.writeFileSync(
    path.join(tempDir, "bleak", "__init__.py"),
    [
      "class FakeDevice:",
      "    address = 'AA:BB:CC:DD:EE:FF'",
      "    name = 'ELM327'",
      "    rssi = -42",
      "class BleakScanner:",
      "    @staticmethod",
      "    async def discover(timeout=5.0):",
      "        return [FakeDevice()]",
      "",
    ].join("\n")
  );
  const script = [
    "import json",
    "import sys",
    `sys.path.insert(0, ${JSON.stringify(tempDir)})`,
    "import editor_bridge",
    "print(json.dumps(editor_bridge.dispatch('scan-obd-ble', {'timeoutSeconds': 0.1})))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr || result.stdout);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, true);
  assert.equal(payload.devices[0].name, "ELM327");
});

test("Python BLE scan errors include exception details", () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "hud-ble-error-"));
  fs.mkdirSync(path.join(tempDir, "bleak"));
  fs.writeFileSync(
    path.join(tempDir, "bleak", "__init__.py"),
    [
      "class BleakError(Exception):",
      "    pass",
      "class BleakScanner:",
      "    @staticmethod",
      "    async def discover(timeout=5.0):",
      "        raise BleakError(\"Thread is configured for Windows GUI but callbacks are not working\")",
      "",
    ].join("\n")
  );
  const script = [
    "import json",
    "import sys",
    `sys.path.insert(0, ${JSON.stringify(tempDir)})`,
    "from editor_vehicle_live import scan_obd_ble_devices",
    "print(json.dumps(scan_obd_ble_devices(0.1)))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, false);
  assert.match(payload.errors[0], /BleakError/);
  assert.match(payload.errors[0], /Thread is configured for Windows GUI/);
});
