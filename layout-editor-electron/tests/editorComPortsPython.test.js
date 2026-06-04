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
  assert.equal(payload.ports[0].device, "COM7");
});
