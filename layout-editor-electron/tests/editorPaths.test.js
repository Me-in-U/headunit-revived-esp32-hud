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

test("Python editor path helpers are importable outside the bridge runtime", () => {
  const script = [
    "import json",
    "from editor_paths import default_layout_path, default_vehicle_profile_paths, default_env_example_path, default_warning_icon_assets_dir, default_nav_icon_assets_dir, ensure_pi_hud_path",
    "ensure_pi_hud_path()",
    "payload = {",
    "    'layout': default_layout_path().as_posix(),",
    "    'vehicles': [path.as_posix() for path in default_vehicle_profile_paths()],",
    "    'env': default_env_example_path().as_posix(),",
    "    'warning': default_warning_icon_assets_dir().as_posix(),",
    "    'nav': default_nav_icon_assets_dir().as_posix(),",
    "}",
    "print(json.dumps(payload))",
  ].join("\n");
  const result = spawnSync(pythonExecutable(), ["-c", script], {
    cwd: path.resolve(__dirname, "..", "python"),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.match(payload.layout, /layouts\/avante_hd_2010_default\.json$/);
  assert.equal(payload.vehicles.some((entry) => /\/vehicles$/.test(entry)), true);
  assert.match(payload.env, /pi-hud\/config\/pi-hud\.env\.example$/);
  assert.match(payload.warning, /pi-hud\/assets\/warning-icons$/);
  assert.match(payload.nav, /pi-hud\/assets\/nav-icons$/);
});
