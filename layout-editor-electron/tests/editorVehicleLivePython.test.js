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
    channel: "COM7",
    interface: "slcan",
    bitrate: 500000,
    tty_baudrate: 115200,
    listen_only: true,
  });
  assert.deepEqual(payload.call, payload.kwargs);
  assert.deepEqual(payload.bus, payload.kwargs);
});

test("Python editor vehicle live helpers default Windows COM SLCAN tty baudrate", () => {
  const script = [
    "import json",
    "from editor_vehicle_live import build_can_bus_kwargs",
    "config = {'interface': 'slcan', 'channel': 'COM3', 'bitrate': 500000, 'listenOnly': True}",
    "print(json.dumps(build_can_bus_kwargs(config)))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.channel, "COM3");
  assert.equal(payload.tty_baudrate, 115200);
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
    "from editor_vehicle_live import OBD_LIVE_COMMANDS, build_obd_live_commands, build_obd_live_update, supported_pids_from_records",
    "responses = {",
    "    'ATI': 'ELM327 v1.5',",
    "    'ATDP': 'ISO 15765-4 CAN (11 bit ID, 500 kbaud)',",
    "    'ATRV': '13.9V',",
    "    '0100': '41 00 BE 1F A8 13',",
    "    '0120': '41 20 80 01 80 01',",
    "    '0140': '41 40 40 00 00 10',",
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
    "payload = {",
    "    'update': build_obd_live_update(records),",
    "    'supported': sorted(supported_pids_from_records(records)),",
    "    'commands': build_obd_live_commands(supported_pids_from_records(records)),",
    "}",
    "print(json.dumps(payload))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  const update = payload.update;
  assert.equal(update.obd.adapter_identity, "ELM327 v1.5");
  assert.match(update.obd.protocol, /ISO 15765-4/);
  assert.equal(update.obd.supported_pid_bitmap, "41 00 BE 1F A8 13");
  assert.equal(update.obd.supported_pid_count > 0, true);
  assert.equal(update.obd.values.some((item) => item.command === "010C" && item.value === 1726), true);
  assert.equal(update.obd.values.some((item) => item.command === "010D" && item.value === 42), true);
  assert.equal(update.vehicle.speed_kmh, 42);
  assert.equal(update.vehicle.voltage_v, 13.46);
  assert.equal(payload.commands.includes("015C"), true);
  assert.deepEqual(update.dtc.stored, ["P0133"]);
});

test("Python editor vehicle live OBD update applies manual PID definitions from the vehicle profile", () => {
  const script = [
    "import json",
    "from editor_vehicle_live import build_obd_live_update",
    "records = [",
    "    {'command': '0100', 'response': '41 00 00 00 80 00', 'ok': True},",
    "    {'command': '0149', 'response': '41 49 80', 'ok': True},",
    "]",
    "defs = [{'command': '0149', 'label': 'Pedal position', 'unit': '%', 'path': 'vehicle.pedal_pct', 'byte_length': 1, 'scale': 100/255, 'offset': 0}]",
    "print(json.dumps(build_obd_live_update(records, defs)))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const update = JSON.parse(result.stdout);
  const item = update.obd.values.find((value) => value.command === "0149");
  assert.equal(item.label, "Pedal position");
  assert.equal(item.unit, "%");
  assert.equal(item.statePath, "vehicle.pedal_pct");
  assert.equal(item.rawBytes, "80");
  assert.equal(item.custom, true);
  assert.equal(item.value, 50.1961);
  assert.equal(update.vehicle.pedal_pct, 50.1961);
});

test("Python editor vehicle live serial OBD runner reads Classic Bluetooth COM adapters", () => {
  const script = [
    "import json",
    "import sys",
    "import types",
    "class FakeLink:",
    "    def __init__(self, port, baudrate, timeout, write_timeout):",
    "        self.port = port",
    "        self.baudrate = baudrate",
    "        self.commands = []",
    "    def __enter__(self):",
    "        return self",
    "    def __exit__(self, *args):",
    "        pass",
    "    def write(self, data):",
    "        self.commands.append(data.decode('ascii').strip())",
    "    def flush(self):",
    "        pass",
    "    def read_until(self, marker, size=1024):",
    "        command = self.commands[-1]",
    "        responses = {'ATI': b'ELM327 v1.5\\r>', '0100': b'41 00 BE 1F A8 13\\r>'}",
    "        return responses.get(command, b'OK\\r>')",
    "fake_serial = types.SimpleNamespace(Serial=FakeLink)",
    "sys.modules['serial'] = fake_serial",
    "from editor_vehicle_live import run_serial_elm_commands",
    "print(json.dumps(run_serial_elm_commands('COM8', 38400, ('ATI', '0100'))))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.deepEqual(payload, ["ELM327 v1.5", "41 00 BE 1F A8 13"]);
});

test("Python editor vehicle live OBD loop does not bounce back to connecting after live", () => {
  const script = [
    "import json",
    "from editor_vehicle_live import VehicleLiveSession",
    "events = []",
    "calls = {'count': 0}",
    "responses = {",
    "    'ATI': 'ELM327 v2.3',",
    "    'ATDP': 'AUTO, ISO 15765-4 (CAN 11/500)',",
    "    '0100': '41 00 BE 1F A8 13',",
    "    '010C': '41 0C 1A F8',",
    "    '010D': '41 0D 2A',",
    "}",
    "session = None",
    "def runner(config, commands):",
    "    calls['count'] += 1",
    "    if calls['count'] >= 2:",
    "        session.stop()",
    "    return [responses.get(command, '') for command in commands]",
    "session = VehicleLiveSession(",
    "    {'obd': {'enabled': True, 'port': 'COM4', 'baud': 38400, 'pollSeconds': 0.01}},",
    "    emit=events.append,",
    "    obd_command_runner=runner,",
    ")",
    "session.run_obd_loop()",
    "print(json.dumps([event['state'] for event in events if event.get('type') == 'status' and event.get('source') == 'obd']))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const states = JSON.parse(result.stdout);
  assert.deepEqual(states, ["connecting", "live", "live"]);
});

test("Python editor vehicle live OBD timeout detail mentions Windows pairing PIN", () => {
  const script = [
    "from editor_vehicle_live import obd_exception_detail",
    "print(obd_exception_detail(TimeoutError()))",
    "print(obd_exception_detail(TimeoutError(), {'port': 'COM8'}))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /pair IOS-Vlink/);
  assert.match(result.stdout, /Pair Android-vlink/);
  assert.match(result.stdout, /Classic Bluetooth COM port/);
  assert.match(result.stdout, /1234/);
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

test("Python BLE inspect resolves scanned device objects and reports missing UART characteristics", () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "hud-ble-inspect-"));
  fs.mkdirSync(path.join(tempDir, "bleak"));
  fs.writeFileSync(
    path.join(tempDir, "bleak", "__init__.py"),
    [
      "class FakeDevice:",
      "    address = '41:42:86:9A:B0:3D'",
      "    name = 'IOS-Vlink'",
      "class FakeCharacteristic:",
      "    uuid = '00002a00-0000-1000-8000-00805f9b34fb'",
      "    properties = ['read']",
      "    description = 'Device Name'",
      "class FakeService:",
      "    uuid = '00001800-0000-1000-8000-00805f9b34fb'",
      "    characteristics = [FakeCharacteristic()]",
      "class BleakScanner:",
      "    @staticmethod",
      "    async def discover(timeout=5.0):",
      "        return [FakeDevice()]",
      "class BleakClient:",
      "    def __init__(self, target, timeout=5.0):",
      "        self.target = target",
      "        self.services = [FakeService()]",
      "    async def __aenter__(self):",
      "        if not hasattr(self.target, 'address'):",
      "            raise RuntimeError('expected resolved device object')",
      "        return self",
      "    async def __aexit__(self, *args):",
      "        pass",
      "",
    ].join("\n")
  );
  const script = [
    "import json",
    "import sys",
    `sys.path.insert(0, ${JSON.stringify(tempDir)})`,
    "import editor_bridge",
    "print(json.dumps(editor_bridge.dispatch('inspect-obd-ble', {'mac': '41:42:86:9A:B0:3D', 'timeoutSeconds': 0.1})))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr || result.stdout);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, false);
  assert.match(payload.errors[0], /No notify\/write BLE ELM327/);
  assert.match(payload.errors[0], /Android-vlink Classic Bluetooth COM/);
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
