const fs = require("fs");
const path = require("path");

function bundledPythonExecutable(root, platform = process.platform) {
  const relativePath =
    platform === "win32"
      ? path.join("pi-hud", ".venv", "Scripts", "python.exe")
      : path.join("pi-hud", ".venv", "bin", "python");
  const candidate = path.join(root, relativePath);
  return fs.existsSync(candidate) ? candidate : "";
}

function pythonExecutable(root, env = process.env, platform = process.platform) {
  return env.HEADUNIT_HUD_PYTHON || bundledPythonExecutable(root, platform) || env.PYTHON || "python";
}

module.exports = {
  bundledPythonExecutable,
  pythonExecutable,
};
