const { app, BrowserWindow, dialog, ipcMain, session } = require("electron");
const fs = require("fs/promises");
const path = require("path");
const { spawn } = require("child_process");
const { pythonExecutable: resolvePythonExecutable } = require("./pythonRuntime");
const { buildOpenMeteoUrl, chooseBestLocation, normalizeLocation, normalizeWeather } = require("./weather");

app.disableHardwareAcceleration();

function repoRoot() {
  return app.isPackaged ? process.resourcesPath : path.resolve(__dirname, "..", "..");
}

function bridgeScript() {
  return app.isPackaged
    ? path.join(app.getAppPath(), "python", "editor_bridge.py")
    : path.join(repoRoot(), "layout-editor-electron", "python", "editor_bridge.py");
}

function vehicleLiveWorkerScript() {
  return app.isPackaged
    ? path.join(app.getAppPath(), "python", "editor_vehicle_live_worker.py")
    : path.join(repoRoot(), "layout-editor-electron", "python", "editor_vehicle_live_worker.py");
}

let mainWindow;
let vehicleLiveWorker = null;
let vehicleLiveStdoutBuffer = "";

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1540,
    height: 940,
    minWidth: 1180,
    minHeight: 760,
    title: "Headunit HUD Layout Editor",
    backgroundColor: "#0b0f14",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));
}

function pythonExecutable() {
  return resolvePythonExecutable(repoRoot());
}

function runBridge(command, payload = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(pythonExecutable(), [bridgeScript(), command], {
      cwd: repoRoot(),
      stdio: ["pipe", "pipe", "pipe"],
      windowsHide: true,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || `Python bridge exited with code ${code}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout || "{}"));
      } catch (error) {
        reject(new Error(`Invalid Python bridge JSON: ${error.message}\n${stdout}\n${stderr}`));
      }
    });
    child.stdin.end(JSON.stringify(payload));
  });
}

function activeWindow() {
  return BrowserWindow.getFocusedWindow() || mainWindow;
}

ipcMain.handle("app:metadata", () => runBridge("metadata"));
ipcMain.handle("vehicle:scan-obd-ble", (_event, payload) => runBridge("scan-obd-ble", payload || {}));
ipcMain.handle("vehicle:inspect-obd-ble", (_event, payload) => runBridge("inspect-obd-ble", payload || {}));
ipcMain.handle("vehicle:list-com-ports", () => runBridge("list-com-ports"));

ipcMain.handle("layout:load-default", () => runBridge("load-default"));

ipcMain.handle("layout:open-dialog", async () => {
  const result = await dialog.showOpenDialog(activeWindow(), {
    title: "Open HUD layout",
    filters: [
      { name: "HUD layout", extensions: ["json"] },
      { name: "All files", extensions: ["*"] },
    ],
    properties: ["openFile"],
  });
  if (result.canceled || result.filePaths.length === 0) {
    return { canceled: true };
  }
  return runBridge("load-layout", { path: result.filePaths[0] });
});

ipcMain.handle("layout:save", async (_event, payload) => {
  if (!payload.path) {
    const result = await dialog.showSaveDialog(activeWindow(), {
      title: "Save HUD layout",
      defaultPath: "avante_hd_2010_default.json",
      filters: [
        { name: "HUD layout", extensions: ["json"] },
        { name: "All files", extensions: ["*"] },
      ],
    });
    if (result.canceled || !result.filePath) {
      return { canceled: true };
    }
    payload.path = result.filePath;
  }
  return runBridge("save-layout", payload);
});

ipcMain.handle("layout:save-as", async (_event, payload) => {
  const result = await dialog.showSaveDialog(activeWindow(), {
    title: "Save HUD layout as",
    defaultPath: payload.path || "avante_hd_2010_default.json",
    filters: [
      { name: "HUD layout", extensions: ["json"] },
      { name: "All files", extensions: ["*"] },
    ],
  });
  if (result.canceled || !result.filePath) {
    return { canceled: true };
  }
  return runBridge("save-layout", { ...payload, path: result.filePath });
});

ipcMain.handle("layout:render-preview", (_event, payload) => runBridge("render-preview", payload));
ipcMain.handle("layout:validate", (_event, payload) => runBridge("validate-layout", payload));

ipcMain.handle("layout:export-snapshot", async (_event, payload) => {
  const result = await dialog.showSaveDialog(activeWindow(), {
    title: "Export Pi-rendered PNG",
    defaultPath: "layout-preview.png",
    filters: [
      { name: "PNG image", extensions: ["png"] },
      { name: "All files", extensions: ["*"] },
    ],
  });
  if (result.canceled || !result.filePath) {
    return { canceled: true };
  }
  return runBridge("export-snapshot", { ...payload, output: result.filePath });
});

ipcMain.handle("layout:export-field-pack", async (_event, payload) => {
  const result = await dialog.showSaveDialog(activeWindow(), {
    title: "Export Pi field pack",
    defaultPath: "headunit-pi-field-pack.zip",
    filters: [
      { name: "Pi HUD field pack", extensions: ["zip"] },
      { name: "All files", extensions: ["*"] },
    ],
  });
  if (result.canceled || !result.filePath) {
    return { canceled: true };
  }
  return runBridge("export-field-pack", { ...payload, output: result.filePath });
});

ipcMain.handle("weather:fetch-current", async (_event, payload) => {
  const ipLocation = await fetchIpLocation().catch(() => null);
  const location = chooseBestLocation({
    layout: payload?.layout,
    browserLocation: payload?.browserLocation,
    ipLocation,
  });
  if (!location) {
    return { ok: false, errors: ["No usable location was available for weather lookup."] };
  }
  const response = await fetch(buildOpenMeteoUrl(location), {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    return { ok: false, errors: [`Open-Meteo request failed: HTTP ${response.status}`] };
  }
  const payloadJson = await response.json();
  return {
    ok: true,
    location,
    weather: normalizeWeather(payloadJson, location),
  };
});

ipcMain.handle("asset:choose-background-image", async () => {
  const result = await dialog.showOpenDialog(activeWindow(), {
    title: "Choose HUD background image",
    filters: [
      { name: "Images", extensions: ["png", "jpg", "jpeg"] },
      { name: "All files", extensions: ["*"] },
    ],
    properties: ["openFile"],
  });
  if (result.canceled || result.filePaths.length === 0) {
    return { canceled: true };
  }
  const filePath = result.filePaths[0];
  const ext = path.extname(filePath).toLowerCase();
  const mime = ext === ".jpg" || ext === ".jpeg" ? "image/jpeg" : "image/png";
  const data = await fs.readFile(filePath);
  return {
    canceled: false,
    name: path.basename(filePath),
    dataUrl: `data:${mime};base64,${data.toString("base64")}`,
  };
});

ipcMain.handle("vehicle:start-live", async (_event, payload) => {
  stopVehicleLiveWorker();
  vehicleLiveStdoutBuffer = "";
  const child = spawn(pythonExecutable(), [vehicleLiveWorkerScript()], {
    cwd: repoRoot(),
    stdio: ["pipe", "pipe", "pipe"],
    windowsHide: true,
  });
  let startFailed = false;
  vehicleLiveWorker = child;
  child.stdout.setEncoding("utf8");
  child.stderr.setEncoding("utf8");
  child.stdout.on("data", handleVehicleLiveStdout);
  child.stderr.on("data", (chunk) => {
    sendVehicleLiveEvent({
      type: "status",
      source: "can",
      state: "error",
      detail: chunk.trim(),
      updatedAt: new Date().toISOString(),
    });
  });
  child.on("error", (error) => {
    startFailed = true;
    if (vehicleLiveWorker === child) {
      vehicleLiveWorker = null;
    }
    const detail = `Worker start failed: ${error.message}`;
    sendVehicleLiveEvent({ type: "status", source: "can", state: "error", detail, updatedAt: new Date().toISOString() });
    sendVehicleLiveEvent({ type: "status", source: "obd", state: "error", detail, updatedAt: new Date().toISOString() });
  });
  child.on("close", () => {
    if (vehicleLiveWorker === child) {
      vehicleLiveWorker = null;
    }
    if (startFailed) {
      return;
    }
    sendVehicleLiveEvent({ type: "status", source: "can", state: "idle", detail: "Worker stopped", updatedAt: new Date().toISOString() });
    sendVehicleLiveEvent({ type: "status", source: "obd", state: "idle", detail: "Worker stopped", updatedAt: new Date().toISOString() });
  });
  child.stdin.end(JSON.stringify(payload || {}));
  return { ok: true };
});

ipcMain.handle("vehicle:stop-live", async () => {
  stopVehicleLiveWorker();
  return { ok: true };
});

function handleVehicleLiveStdout(chunk) {
  vehicleLiveStdoutBuffer += chunk;
  const lines = vehicleLiveStdoutBuffer.split(/\r?\n/);
  vehicleLiveStdoutBuffer = lines.pop() || "";
  for (const line of lines) {
    if (!line.trim()) {
      continue;
    }
    try {
      sendVehicleLiveEvent(JSON.parse(line));
    } catch (error) {
      sendVehicleLiveEvent({
        type: "status",
        source: "can",
        state: "error",
        detail: `Invalid worker event: ${error.message}`,
        updatedAt: new Date().toISOString(),
      });
    }
  }
}

function sendVehicleLiveEvent(event) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("vehicle-live:event", event);
  }
}

function stopVehicleLiveWorker() {
  if (!vehicleLiveWorker) {
    return;
  }
  const child = vehicleLiveWorker;
  vehicleLiveWorker = null;
  child.removeAllListeners("close");
  child.kill();
}

async function fetchIpLocation() {
  const response = await fetch("https://ipapi.co/json/", {
    headers: {
      Accept: "application/json",
      "User-Agent": "headunit-hud-layout-editor/0.1",
    },
  });
  if (!response.ok) {
    return null;
  }
  const data = await response.json();
  return normalizeLocation(
    {
      latitude: data.latitude,
      longitude: data.longitude,
      accuracy: 50000,
      source: "network",
      name: [data.city, data.region, data.country_name].filter(Boolean).join(", "),
    },
    { source: "network", accuracy: 50000 }
  );
}

app.whenReady().then(() => {
  session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
    callback(permission === "geolocation");
  });
  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
