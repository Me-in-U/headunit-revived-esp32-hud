const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("hudEditor", {
  metadata: () => ipcRenderer.invoke("app:metadata"),
  loadDefault: () => ipcRenderer.invoke("layout:load-default"),
  openLayout: () => ipcRenderer.invoke("layout:open-dialog"),
  saveLayout: (payload) => ipcRenderer.invoke("layout:save", payload),
  saveLayoutAs: (payload) => ipcRenderer.invoke("layout:save-as", payload),
  renderPreview: (payload) => ipcRenderer.invoke("layout:render-preview", payload),
  validateLayout: (payload) => ipcRenderer.invoke("layout:validate", payload),
  exportSnapshot: (payload) => ipcRenderer.invoke("layout:export-snapshot", payload),
  exportFieldPack: (payload) => ipcRenderer.invoke("layout:export-field-pack", payload),
  fetchWeather: (payload) => ipcRenderer.invoke("weather:fetch-current", payload),
  chooseBackgroundImage: () => ipcRenderer.invoke("asset:choose-background-image"),
  scanObdBle: (payload) => ipcRenderer.invoke("vehicle:scan-obd-ble", payload),
  inspectObdBle: (payload) => ipcRenderer.invoke("vehicle:inspect-obd-ble", payload),
  listComPorts: () => ipcRenderer.invoke("vehicle:list-com-ports"),
  startVehicleLive: (payload) => ipcRenderer.invoke("vehicle:start-live", payload),
  stopVehicleLive: () => ipcRenderer.invoke("vehicle:stop-live"),
  onVehicleLiveEvent: (handler) => {
    const listener = (_event, payload) => handler(payload);
    ipcRenderer.on("vehicle-live:event", listener);
    return () => ipcRenderer.removeListener("vehicle-live:event", listener);
  },
});
