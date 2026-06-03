const test = require("node:test");
const assert = require("node:assert/strict");

const ScreenState = require("../src/renderer/editorScreenState.js");

test("ensureScreens initializes standalone and bridge screens from current elements", () => {
  const layout = {
    elements: [{ id: "speed" }],
  };

  const selected = ScreenState.ensureScreens(layout, "bridge");

  assert.equal(selected, "bridge");
  assert.deepEqual(Object.keys(layout.screens), ["standalone", "bridge"]);
  assert.deepEqual(layout.screens.standalone.elements, [{ id: "speed" }]);
  assert.deepEqual(layout.screens.bridge.elements, [{ id: "speed" }]);
  assert.notEqual(layout.elements, layout.screens.bridge.elements);
});

test("switchScreen stores current elements before loading target elements", () => {
  const layout = {
    elements: [{ id: "standalone_current" }],
    screens: {
      standalone: { label: "Standalone", elements: [{ id: "stale" }] },
      bridge: { label: "Bridge", elements: [{ id: "bridge_current" }] },
    },
  };

  const selected = ScreenState.switchScreen(layout, "standalone", "bridge");

  assert.equal(selected, "bridge");
  assert.deepEqual(layout.screens.standalone.elements, [{ id: "standalone_current" }]);
  assert.deepEqual(layout.elements, [{ id: "bridge_current" }]);
});

test("importOtherScreen replaces the current screen with the opposite screen elements", () => {
  const layout = {
    elements: [{ id: "old_bridge" }],
    screens: {
      standalone: { label: "Standalone", elements: [{ id: "standalone_current" }] },
      bridge: { label: "Bridge", elements: [{ id: "old_bridge" }] },
    },
  };

  ScreenState.importOtherScreen(layout, "bridge");

  assert.deepEqual(layout.screens.bridge.elements, [{ id: "standalone_current" }]);
  assert.deepEqual(layout.elements, [{ id: "standalone_current" }]);
});
