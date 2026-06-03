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
