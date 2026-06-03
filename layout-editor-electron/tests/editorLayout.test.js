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

test("Python editor layout helpers sync screens and prepare handoff metadata", () => {
  const script = [
    "import json",
    "from editor_layout import ensure_screen_layout, sync_current_screen, prepare_for_save",
    "layout = {",
    "    'canvas': {'width': 1920, 'height': 480, 'background': '#000000'},",
    "    'dummy_data': {'vehicle': {'speed_kmh': 42}},",
    "    'elements': [{'id': 'standalone_marker', 'type': 'text', 'text': 'A', 'x': 20, 'y': 20, 'w': 120, 'h': 40}],",
    "    'screens': {'bridge': {'label': 'Bridge', 'elements': [{'id': 'bridge_marker', 'type': 'text', 'text': 'B', 'x': 20, 'y': 20, 'w': 120, 'h': 40}]}}",
    "}",
    "ensure_screen_layout(layout, 'standalone')",
    "layout['elements'] = [{'id': 'changed', 'type': 'text', 'text': 'C', 'x': 20, 'y': 20, 'w': 120, 'h': 40}]",
    "sync_current_screen(layout, 'standalone')",
    "prepared = prepare_for_save(layout, 'standalone')",
    "print(json.dumps({",
    "    'standalone': [item['id'] for item in prepared['screens']['standalone']['elements']],",
    "    'bridge': [item['id'] for item in prepared['screens']['bridge']['elements']],",
    "    'handoff': 'pi_hud_handoff' in prepared,",
    "}))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.deepEqual(payload.standalone, ["changed"]);
  assert.deepEqual(payload.bridge, ["bridge_marker"]);
  assert.equal(payload.handoff, true);
});
