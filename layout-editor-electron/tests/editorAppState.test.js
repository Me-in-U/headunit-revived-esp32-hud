const assert = require("node:assert/strict");
const test = require("node:test");

const I18n = require("../src/renderer/editorI18n.js");
const AppState = require("../src/renderer/editorAppState.js");

test("createInitialState preserves renderer state defaults and normalized app language", () => {
  const storage = {
    getItem(key) {
      assert.equal(key, I18n.APP_LANGUAGE_KEY);
      return "zz";
    },
  };

  assert.deepEqual(AppState.createInitialState(I18n, storage), {
    layout: null,
    path: "",
    currentScreen: "standalone",
    metadata: null,
    vehicleProfiles: {},
    selectedId: "",
    activeCategory: "",
    dirty: false,
    renderToken: 0,
    previewBusy: false,
    previewPending: false,
    drag: null,
    paletteQuery: "",
    validationMessages: [],
    simulationEnabled: false,
    vehicleLive: {
      activeTab: "elements",
      status: {
        obd: { state: "idle", detail: "", updatedAt: "" },
        can: { state: "idle", detail: "", updatedAt: "" },
      },
      mergedState: {},
      canFrames: [],
      canSummary: { frame_count: 0, unique_id_count: 0, ids: [] },
      obdRecords: [],
      obdDevices: [],
      selectedObdDevice: null,
      selectedObdPair: null,
      obdConnectState: "idle",
      obdInspection: null,
      lastError: "",
      running: false,
    },
    history: {
      undo: [],
      redo: [],
      applying: false,
    },
    appLanguage: "ko",
  });
});

test("createInitialState uses Korean when storage contains a supported language", () => {
  const state = AppState.createInitialState(I18n, { getItem: () => "ko" });

  assert.equal(state.appLanguage, "ko");
});

test("createEditorDom returns an empty DOM reference bag", () => {
  assert.deepEqual(AppState.createEditorDom(), {});
});
