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

test("Python COM port helper returns sorted device details", () => {
  const script = [
    "import json",
    "from editor_com_ports import list_com_ports",
    "class Port:",
    "    def __init__(self, device, description, hwid, manufacturer='', product='', vid=None, pid=None):",
    "        self.device = device",
    "        self.name = device",
    "        self.description = description",
    "        self.hwid = hwid",
    "        self.manufacturer = manufacturer",
    "        self.product = product",
    "        self.vid = vid",
    "        self.pid = pid",
    "        self.serial_number = ''",
    "        self.location = ''",
    "ports = [",
    "    Port('COM9', 'Bluetooth Serial Port', 'BTHENUM', 'Microsoft'),",
    "    Port('COM3', 'CANable USB to CAN Adapter', 'USB VID:PID=1D50:606F', 'canable.io', 'CANable', 0x1D50, 0x606F),",
    "    Port('COM4', 'CANtact USB/CAN Device', 'USB VID:PID=16D0:117E', 'http://www.cantact.io', '', 0x16D0, 0x117E),",
    "]",
    "print(json.dumps(list_com_ports(lambda: ports), ensure_ascii=False))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, true);
  assert.equal(payload.ports[0].device, "COM3");
  assert.equal(payload.ports[0].description, "CANable USB to CAN Adapter");
  assert.equal(payload.ports[0].manufacturer, "canable.io");
  assert.equal(payload.ports[0].vid, "1D50");
  assert.equal(payload.ports[0].pid, "606F");
  assert.equal(payload.ports[0].likelyCanable, true);
  assert.equal(payload.ports[1].device, "COM4");
  assert.equal(payload.ports[1].description, "CANtact USB/CAN Device");
  assert.equal(payload.ports[1].likelyCanable, true);
});

test("Python COM port helper falls back to Windows PnP records", () => {
  const script = [
    "import json",
    "from editor_com_ports import list_com_ports, windows_pnp_port_record",
    "item = {",
    "    'Status': 'Unknown',",
    "    'FriendlyName': 'CANtact USB/CAN Device(COM3)',",
    "    'InstanceId': 'USB\\\\VID_16D0&PID_117E\\\\205F33853845',",
    "}",
    "print(json.dumps(list_com_ports(lambda: [], lambda: [windows_pnp_port_record(item)]), ensure_ascii=False))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, true);
  assert.equal(payload.ports[0].device, "COM3");
  assert.equal(payload.ports[0].description, "CANtact USB/CAN Device");
  assert.equal(payload.ports[0].vid, "16D0");
  assert.equal(payload.ports[0].pid, "117E");
  assert.equal(payload.ports[0].serialNumber, "205F33853845");
  assert.equal(payload.ports[0].likelyCanable, true);
});

test("Python COM port helper skips slow Windows fallback when pyserial found ports", () => {
  const script = [
    "import json",
    "from editor_com_ports import list_com_ports",
    "class Port:",
    "    device = 'COM5'",
    "    name = 'COM5'",
    "    description = 'Standard Serial over Bluetooth link'",
    "    hwid = 'BTHENUM 4142869AB068'",
    "    manufacturer = 'Microsoft'",
    "    product = ''",
    "    vid = None",
    "    pid = None",
    "    serial_number = ''",
    "    location = ''",
    "def slow_windows_reader():",
    "    raise RuntimeError('fallback should not run')",
    "print(json.dumps(list_com_ports(lambda: [Port()], slow_windows_reader), ensure_ascii=False))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, true);
  assert.equal(payload.ports[0].device, "COM5");
  assert.equal(payload.ports[0].likelyObdSerial, true);
});

test("Python COM port helper merges fast Windows registry Bluetooth COM records", () => {
  const script = [
    "import json",
    "from editor_com_ports import list_com_ports, windows_registry_serial_record",
    "class Port:",
    "    device = 'COM3'",
    "    name = 'COM3'",
    "    description = 'CANtact USB/CAN Device(COM3)'",
    "    hwid = 'USB VID:PID=16D0:117E'",
    "    manufacturer = 'http://www.cantact.io'",
    "    product = ''",
    "    vid = 0x16D0",
    "    pid = 0x117E",
    "    serial_number = ''",
    "    location = ''",
    "registry = lambda: [windows_registry_serial_record('\\\\Device\\\\BthModem0', 'COM5')]",
    "print(json.dumps(list_com_ports(lambda: [Port()], windows_registry_records=registry), ensure_ascii=False))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  const com5 = payload.ports.find((port) => port.device === "COM5");
  assert.equal(payload.ok, true);
  assert.equal(com5.description, "Bluetooth serial port");
  assert.equal(com5.likelyObdSerial, true);
});

test("Python COM port helper merges registry OBD and PnP CAN records", () => {
  const script = [
    "import json",
    "from editor_com_ports import list_com_ports, windows_pnp_port_record, windows_registry_serial_record",
    "registry = lambda: [windows_registry_serial_record('\\\\Device\\\\BthModem0', 'COM5')]",
    "pnp = lambda: [windows_pnp_port_record({",
    "    'Status': 'Unknown',",
    "    'FriendlyName': 'CANtact USB/CAN Device(COM3)',",
    "    'InstanceId': 'USB\\\\VID_16D0&PID_117E\\\\205F33853845',",
    "})]",
    "print(json.dumps(list_com_ports(lambda: [], windows_port_records=pnp, windows_registry_records=registry), ensure_ascii=False))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  const com3 = payload.ports.find((port) => port.device === "COM3");
  const com5 = payload.ports.find((port) => port.device === "COM5");
  assert.equal(com3.likelyCanable, true);
  assert.equal(com5.likelyObdSerial, true);
});

test("Python COM port helper marks outgoing Bluetooth serial links as OBD candidates", () => {
  const script = [
    "import json",
    "from editor_com_ports import list_com_ports, windows_pnp_port_record",
    "items = [",
    "    {",
    "        'Status': 'OK',",
    "        'FriendlyName': '표준 Bluetooth에서 직렬 링크(COM4)',",
    "        'InstanceId': 'BTHENUM\\\\{00001101-0000-1000-8000-00805F9B34FB}_LOCALMFG&0000\\\\8&3A9899E2&0&000000000000_00000002',",
    "    },",
    "    {",
    "        'Status': 'OK',",
    "        'FriendlyName': '표준 Bluetooth에서 직렬 링크(COM5)',",
    "        'InstanceId': 'BTHENUM\\\\{00001101-0000-1000-8000-00805F9B34FB}_LOCALMFG&005D\\\\8&3A9899E2&0&4142869AB068_C00000000',",
    "    },",
    "]",
    "print(json.dumps(list_com_ports(lambda: [], lambda: [windows_pnp_port_record(item) for item in items]), ensure_ascii=False))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  const com4 = payload.ports.find((port) => port.device === "COM4");
  const com5 = payload.ports.find((port) => port.device === "COM5");
  assert.equal(com4.likelyObdSerial, false);
  assert.equal(com5.likelyObdSerial, true);
});

test("Python COM port helper lets PnP incoming Bluetooth detail override generic registry OBD hints", () => {
  const script = [
    "import json",
    "from editor_com_ports import list_com_ports, windows_pnp_port_record, windows_registry_serial_record",
    "registry = lambda: [windows_registry_serial_record('\\\\Device\\\\BthModem0', 'COM5')]",
    "pnp = lambda: [windows_pnp_port_record({",
    "    'Status': 'OK',",
    "    'FriendlyName': '표준 Bluetooth에서 직렬 링크(COM5)',",
    "    'InstanceId': 'BTHENUM\\\\{00001101-0000-1000-8000-00805F9B34FB}_LOCALMFG&0000\\\\8&3A9899E2&0&000000000000_00000002',",
    "})]",
    "print(json.dumps(list_com_ports(lambda: [], windows_port_records=pnp, windows_registry_records=registry), ensure_ascii=False))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  const com5 = payload.ports.find((port) => port.device === "COM5");
  assert.equal(com5.hwid.includes("000000000000_00000002"), true);
  assert.equal(com5.likelyObdSerial, false);
});

test("Python bridge exposes COM port list command without renderer imports", () => {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "hud-com-bridge-"));
  fs.writeFileSync(path.join(tempDir, "pygame.py"), "raise RuntimeError('pygame import should be lazy for COM port list')\n");
  const listPortsDir = path.join(tempDir, "serial", "tools");
  fs.mkdirSync(listPortsDir, { recursive: true });
  fs.writeFileSync(path.join(tempDir, "serial", "__init__.py"), "");
  fs.writeFileSync(path.join(tempDir, "serial", "tools", "__init__.py"), "");
  fs.writeFileSync(
    path.join(listPortsDir, "list_ports.py"),
    [
      "class Port:",
      "    device = 'COM7'",
      "    name = 'COM7'",
      "    description = 'USB Serial Device'",
      "    hwid = 'USB VID:PID=1A86:7523'",
      "    manufacturer = 'wch.cn'",
      "    product = 'USB Serial'",
      "    vid = 0x1A86",
      "    pid = 0x7523",
      "    serial_number = ''",
      "    location = ''",
      "def comports():",
      "    return [Port()]",
      "",
    ].join("\n")
  );
  const script = [
    "import json",
    "import sys",
    `sys.path.insert(0, ${JSON.stringify(tempDir)})`,
    "import editor_bridge",
    "print(json.dumps(editor_bridge.dispatch('list-com-ports', {})))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr || result.stdout);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.ok, true);
  assert.ok(payload.ports.some((port) => port.device === "COM7"));
});
