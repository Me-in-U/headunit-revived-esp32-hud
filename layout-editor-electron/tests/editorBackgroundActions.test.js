const test = require("node:test");
const assert = require("node:assert/strict");

const BackgroundActions = require("../src/renderer/editorBackgroundActions.js");

test("applyBackgroundColor ensures canvas and stores selected background color", () => {
  const state = { layout: {} };

  const result = BackgroundActions.applyBackgroundColor(state, "#123456");

  assert.equal(result.changed, true);
  assert.deepEqual(state.layout.canvas, { background: "#123456" });
});

test("applyBackgroundImage stores image data name and cover fit", () => {
  const state = { layout: { canvas: { background: "#05080c" } } };

  const result = BackgroundActions.applyBackgroundImage(state, {
    canceled: false,
    dataUrl: "data:image/png;base64,abc",
    name: "dash.png",
  });

  assert.equal(result.changed, true);
  assert.deepEqual(state.layout.canvas, {
    background: "#05080c",
    background_image: "data:image/png;base64,abc",
    background_image_name: "dash.png",
    background_image_fit: "cover",
  });
});

test("applyBackgroundImage ignores canceled selections", () => {
  const state = { layout: { canvas: {} } };

  const result = BackgroundActions.applyBackgroundImage(state, { canceled: true });

  assert.equal(result.changed, false);
  assert.deepEqual(state.layout.canvas, {});
});

test("clearBackgroundImage removes image fields from existing canvas", () => {
  const state = {
    layout: {
      canvas: {
        background: "#05080c",
        background_image: "data:image/png;base64,abc",
        background_image_name: "dash.png",
        background_image_fit: "cover",
      },
    },
  };

  const result = BackgroundActions.clearBackgroundImage(state);

  assert.equal(result.changed, true);
  assert.deepEqual(state.layout.canvas, { background: "#05080c" });
});

function commandDeps(log = []) {
  return {
    recordHistory() {
      log.push(["recordHistory"]);
    },
    markDirty() {
      log.push(["markDirty"]);
    },
    schedulePreview(delay) {
      log.push(["schedulePreview", delay]);
    },
  };
}

test("applyBackgroundColorCommand records history marks dirty and schedules preview", () => {
  const log = [];
  const state = { layout: {} };

  const result = BackgroundActions.applyBackgroundColorCommand(state, "#112233", commandDeps(log));

  assert.equal(result.changed, true);
  assert.deepEqual(state.layout.canvas, { background: "#112233" });
  assert.deepEqual(log, [["recordHistory"], ["markDirty"], ["schedulePreview", 40]]);
});

test("chooseBackgroundImageCommand ignores canceled selections from the service", async () => {
  const log = [];
  const state = { layout: { canvas: {} } };
  const service = {
    chooseBackgroundImage() {
      log.push(["chooseBackgroundImage"]);
      return Promise.resolve({ canceled: true });
    },
  };

  const result = await BackgroundActions.chooseBackgroundImageCommand(state, service, commandDeps(log));

  assert.equal(result.changed, false);
  assert.deepEqual(state.layout.canvas, {});
  assert.deepEqual(log, [["chooseBackgroundImage"]]);
});

test("chooseBackgroundImageCommand applies selected image and schedules preview", async () => {
  const log = [];
  const state = { layout: { canvas: { background: "#05080c" } } };
  const service = {
    chooseBackgroundImage() {
      log.push(["chooseBackgroundImage"]);
      return Promise.resolve({ canceled: false, dataUrl: "data:image/png;base64,abc", name: "dash.png" });
    },
  };

  const result = await BackgroundActions.chooseBackgroundImageCommand(state, service, commandDeps(log));

  assert.equal(result.changed, true);
  assert.equal(state.layout.canvas.background_image_name, "dash.png");
  assert.deepEqual(log, [["chooseBackgroundImage"], ["recordHistory"], ["markDirty"], ["schedulePreview", 40]]);
});

test("clearBackgroundImageCommand records history marks dirty and schedules preview", () => {
  const log = [];
  const state = {
    layout: {
      canvas: {
        background_image: "data:image/png;base64,abc",
      },
    },
  };

  const result = BackgroundActions.clearBackgroundImageCommand(state, commandDeps(log));

  assert.equal(result.changed, true);
  assert.deepEqual(state.layout.canvas, {});
  assert.deepEqual(log, [["recordHistory"], ["markDirty"], ["schedulePreview", 40]]);
});
