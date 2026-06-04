const test = require("node:test");
const assert = require("node:assert/strict");

const VehicleLiveState = require("../src/renderer/editorVehicleLiveState.js");

test("vehicle live state stores connection events and exposes simulation preview override", () => {
  const state = VehicleLiveState.createVehicleLiveState();

  VehicleLiveState.mergeVehicleLiveEvent(state, {
    type: "status",
    source: "obd",
    state: "live",
    detail: "iCar BLE connected",
    updatedAt: "2026-06-04T00:00:00Z",
  });
  VehicleLiveState.mergeVehicleLiveEvent(state, {
    type: "state",
    source: "obd",
    update: { vehicle: { speed_kmh: 55, obd_state: "live" } },
    mergedState: { vehicle: { speed_kmh: 55, obd_state: "live" } },
  });

  assert.equal(state.status.obd.state, "live");
  assert.equal(state.status.obd.detail, "iCar BLE connected");
  assert.deepEqual(VehicleLiveState.previewStateOverride({ simulationEnabled: false, vehicleLive: state }), null);
  assert.deepEqual(
    VehicleLiveState.previewStateOverride({ simulationEnabled: true, vehicleLive: state }),
    { vehicle: { speed_kmh: 55, obd_state: "live" } }
  );
});

test("copy live sample writes merged live state to layout dummy data only on explicit action", () => {
  const appState = {
    layout: { dummy_data: { vehicle: { speed_kmh: 42 }, nav: { connected: false } } },
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
    dirty: false,
  };
  VehicleLiveState.mergeVehicleLiveEvent(appState.vehicleLive, {
    type: "state",
    source: "can",
    update: { vehicle: { gear_actual: "D" }, debug: { last_can_id: "0x316" } },
    mergedState: { vehicle: { gear_actual: "D" }, debug: { last_can_id: "0x316" } },
  });

  const copied = VehicleLiveState.copyLiveSampleToDummyData(appState);

  assert.equal(copied, true);
  assert.deepEqual(appState.layout.dummy_data, {
    vehicle: { speed_kmh: 42, gear_actual: "D" },
    nav: { connected: false },
    debug: { last_can_id: "0x316" },
  });
});

test("vehicle live state keeps CAN summaries OBD records and confirmed signal profile edits", () => {
  const appState = {
    layout: {
      selected_vehicle: "car",
      vehicles: [{ id: "car", can_signals: [] }],
    },
    vehicleLive: VehicleLiveState.createVehicleLiveState(),
  };

  VehicleLiveState.mergeVehicleLiveEvent(appState.vehicleLive, {
    type: "can_summary",
    summary: { frame_count: 2, unique_id_count: 1, ids: [{ id: "0x316", count: 2 }] },
  });
  VehicleLiveState.mergeVehicleLiveEvent(appState.vehicleLive, {
    type: "obd_record",
    record: { command: "010C", response: "41 0C 1C F8", ok: true },
  });
  const saved = VehicleLiveState.upsertConfirmedCanSignal(appState, {
    frame_id: "0x316",
    name: "vehicle.gear_actual",
    start_byte: 1,
    length: 1,
  });

  assert.equal(appState.vehicleLive.canSummary.unique_id_count, 1);
  assert.equal(appState.vehicleLive.obdRecords[0].command, "010C");
  assert.equal(saved, true);
  assert.deepEqual(appState.layout.vehicles[0].can_signals, [
    { confirmed: true, frame_id: "0x316", name: "vehicle.gear_actual", start_byte: 1, length: 1 },
  ]);
});

test("vehicle live state tracks selected OBD BLE device and sorts likely OBD adapters first", () => {
  const state = VehicleLiveState.createVehicleLiveState();

  VehicleLiveState.setSelectedObdDevice(state, { address: "AA:BB:CC:DD:EE:FF", name: "V-LINK" });
  VehicleLiveState.setSelectedObdPair(state, { rx_uuid: "rx", tx_uuid: "tx" });

  assert.deepEqual(state.selectedObdDevice, { address: "AA:BB:CC:DD:EE:FF", name: "V-LINK" });
  assert.deepEqual(state.selectedObdPair, { rx_uuid: "rx", tx_uuid: "tx" });
  assert.deepEqual(
    VehicleLiveState.sortedObdDevices([
      { address: "11", name: "Keyboard" },
      { address: "22", name: "ELM327" },
      { address: "33", name: "iCar Pro" },
    ]).map((device) => device.address),
    ["22", "33", "11"]
  );
});
