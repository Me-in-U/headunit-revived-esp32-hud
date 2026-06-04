const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const PythonRuntime = require("../src/pythonRuntime.js");

test("pythonExecutable prefers explicit override then bundled venv before system Python", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "hud-python-runtime-"));
  const venvPython = path.join(root, "pi-hud", ".venv", "Scripts", "python.exe");
  fs.mkdirSync(path.dirname(venvPython), { recursive: true });
  fs.writeFileSync(venvPython, "");

  assert.equal(
    PythonRuntime.pythonExecutable(root, { HEADUNIT_HUD_PYTHON: "C:\\custom\\python.exe", PYTHON: "C:\\system\\python.exe" }, "win32"),
    "C:\\custom\\python.exe"
  );
  assert.equal(
    PythonRuntime.pythonExecutable(root, { PYTHON: "C:\\system\\python.exe" }, "win32"),
    venvPython
  );
});

test("pythonExecutable falls back to PYTHON when no bundled venv exists", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "hud-python-runtime-"));

  assert.equal(
    PythonRuntime.pythonExecutable(root, { PYTHON: "C:\\system\\python.exe" }, "win32"),
    "C:\\system\\python.exe"
  );
});
