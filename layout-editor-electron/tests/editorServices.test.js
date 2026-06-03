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

test("Python editor services expose metadata and layout response helpers", () => {
  const script = [
    "import json",
    "from editor_paths import default_layout_path",
    "from editor_services import metadata_response, load_layout_response, render_size",
    "metadata = metadata_response()",
    "loaded = load_layout_response(default_layout_path())",
    "width, height = render_size({'canvas': {'width': 321, 'height': 123}}, {})",
    "print(json.dumps({",
    "    'metadata_ok': metadata['ok'],",
    "    'has_speed': 'Speed' in metadata['palette'],",
    "    'loaded_ok': loaded['ok'],",
    "    'screen': loaded['currentScreen'],",
    "    'size': [width, height],",
    "}))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.metadata_ok, true);
  assert.equal(payload.has_speed, true);
  assert.equal(payload.loaded_ok, true);
  assert.equal(payload.screen, "standalone");
  assert.deepEqual(payload.size, [321, 123]);
});
