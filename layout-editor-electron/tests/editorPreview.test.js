const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

function pythonExecutable() {
  const root = path.resolve(__dirname, "..", "..");
  const venvPython = path.join(root, "pi-hud", ".venv", "Scripts", "python.exe");
  return fs.existsSync(venvPython) ? venvPython : "python";
}

test("Python editor preview renderer returns PNG bytes outside the bridge runtime", () => {
  const script = [
    "from editor_preview import render_preview_png",
    "layout = {",
    "    'canvas': {'width': 320, 'height': 120, 'background': '#000000'},",
    "    'dummy_data': {'vehicle': {'speed_kmh': 42}, 'warnings': {'door_open': False}},",
    "    'elements': [",
    "        {'id': 'speed', 'type': 'value', 'binding': 'vehicle.speed_kmh', 'x': 20, 'y': 20, 'w': 120, 'h': 40, 'font_size': 28},",
    "        {'id': 'door', 'type': 'warning_icon', 'binding': 'warnings.door_open', 'icon': 'door_open', 'x': 180, 'y': 20, 'w': 48, 'h': 48},",
    "    ],",
    "}",
    "png = render_preview_png(layout, 320, 120)",
    "assert png.startswith(b'\\x89PNG\\r\\n\\x1a\\n')",
    "print(len(png))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(Number.parseInt(result.stdout, 10) > 100, true);
});
