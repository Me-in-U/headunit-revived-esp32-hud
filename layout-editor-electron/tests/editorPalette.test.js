const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const path = require("node:path");

function pythonExecutable() {
  const root = path.resolve(__dirname, "..", "..");
  const venvPython = path.join(root, "pi-hud", ".venv", "Scripts", "python.exe");
  return require("node:fs").existsSync(venvPython) ? venvPython : "python";
}

test("Python editor palette metadata is importable outside the bridge runtime", () => {
  const script = [
    "import json",
    "from editor_palette import PALETTE",
    "print(json.dumps({'categories': sorted(PALETTE), 'speed_count': len(PALETTE['Speed'])}))",
  ].join("; ");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.categories.includes("Speed"), true);
  assert.equal(payload.categories.includes("Gear"), true);
  assert.equal(payload.speed_count >= 4, true);
});
