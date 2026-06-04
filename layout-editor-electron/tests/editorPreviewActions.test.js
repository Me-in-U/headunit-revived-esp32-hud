const test = require("node:test");
const assert = require("node:assert/strict");

const PreviewActions = require("../src/renderer/editorPreviewActions.js");

function previewOptions(overrides = {}) {
  const calls = {
    hidden: 0,
    overlays: 0,
    raf: 0,
    rendered: [],
    scheduled: [],
    statuses: [],
  };
  return {
    calls,
    options: {
      hideDragGhost() {
        calls.hidden += 1;
      },
      renderOverlay() {
        calls.overlays += 1;
      },
      renderPreview: async (request) => {
        calls.rendered.push(request);
        return { png: "abc123", width: request.width, height: request.height };
      },
      requestAnimationFrame(callback) {
        calls.raf += 1;
        callback();
      },
      schedulePreview(delay) {
        calls.scheduled.push(delay);
      },
      setStatus(message, kind = "") {
        calls.statuses.push([message, kind]);
      },
      translate(key) {
        return `t:${key}`;
      },
      ...overrides,
    },
  };
}

test("renderPreview marks pending and skips service while preview is busy", async () => {
  const state = { layout: { canvas: {} }, previewBusy: true, previewPending: false, renderToken: 0 };
  const dom = { previewImage: {}, pixelStatus: {} };
  const { calls, options } = previewOptions();

  await PreviewActions.renderPreview(state, dom, options);

  assert.equal(state.previewPending, true);
  assert.equal(calls.rendered.length, 0);
  assert.deepEqual(calls.statuses, []);
});

test("renderPreview renders current layout and updates preview dom status and overlay", async () => {
  const layout = { canvas: { width: 1280, height: 400 } };
  const state = {
    layout,
    currentScreen: "bridge",
    previewBusy: false,
    previewPending: false,
    renderToken: 0,
  };
  const dom = { previewImage: {}, pixelStatus: { textContent: "" } };
  const { calls, options } = previewOptions();

  await PreviewActions.renderPreview(state, dom, options);

  assert.deepEqual(calls.rendered, [
    {
      layout,
      currentScreen: "bridge",
      width: 1280,
      height: 400,
    },
  ]);
  assert.equal(dom.previewImage.src, "data:image/png;base64,abc123");
  assert.equal(dom.pixelStatus.textContent, "1280 x 400");
  assert.equal(state.previewBusy, false);
  assert.equal(state.previewPending, false);
  assert.equal(state.renderToken, 1);
  assert.equal(calls.hidden, 1);
  assert.equal(calls.raf, 1);
  assert.equal(calls.overlays, 1);
  assert.deepEqual(calls.statuses, [
    ["t:renderPreview", ""],
    ["t:previewReady", "ok"],
  ]);
});

test("renderPreview schedules a follow-up when pending work appeared during render", async () => {
  const state = {
    layout: { canvas: {} },
    currentScreen: "standalone",
    previewBusy: false,
    previewPending: true,
    renderToken: 0,
  };
  const dom = { previewImage: {}, pixelStatus: { textContent: "" } };
  const { calls, options } = previewOptions();

  await PreviewActions.renderPreview(state, dom, options);

  assert.equal(state.previewBusy, false);
  assert.equal(state.previewPending, false);
  assert.deepEqual(calls.scheduled, [30]);
});

test("renderPreview includes simulation override only when one is available", async () => {
  const layout = { canvas: { width: 1920, height: 480 } };
  const state = {
    layout,
    currentScreen: "standalone",
    previewBusy: false,
    previewPending: false,
    renderToken: 0,
  };
  const dom = { previewImage: {}, pixelStatus: { textContent: "" } };
  const { calls, options } = previewOptions({
    previewStateOverride: () => ({ vehicle: { speed_kmh: 88 } }),
  });

  await PreviewActions.renderPreview(state, dom, options);

  assert.deepEqual(calls.rendered[0], {
    layout,
    currentScreen: "standalone",
    width: 1920,
    height: 480,
    stateOverride: { vehicle: { speed_kmh: 88 } },
  });
});

test("renderPreview reports render errors and clears busy state", async () => {
  const state = {
    layout: { canvas: {} },
    currentScreen: "standalone",
    previewBusy: false,
    previewPending: false,
    renderToken: 0,
  };
  const dom = { previewImage: {}, pixelStatus: { textContent: "" } };
  const { calls, options } = previewOptions({
    renderPreview: async () => {
      throw new Error("render failed");
    },
  });

  await PreviewActions.renderPreview(state, dom, options);

  assert.equal(state.previewBusy, false);
  assert.deepEqual(calls.statuses, [
    ["t:renderPreview", ""],
    ["render failed", "error"],
  ]);
});
